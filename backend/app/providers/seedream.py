import asyncio
import base64
import binascii
import io
import uuid
from urllib.parse import urlsplit

from PIL import Image

from app.core.config import get_settings
from app.providers.contracts import (
    OPERATIONS,
    ProviderError,
    ProviderHealth,
    ProviderImage,
    ProviderResult,
)
from app.providers.http_transport import BoundedHTTP, ExternalServiceError

BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
DEFAULT_MODEL = "doubao-seedream-5-0-pro-260628"
OUTPUT_SIZE = (1776, 2368)


def official_base(value):
    base = (value or BASE_URL).rstrip("/")
    try:
        url = urlsplit(base)
        valid = (
            url.scheme == "https"
            and url.hostname == "ark.cn-beijing.volces.com"
            and url.port in (None, 443)
            and url.path == "/api/v3"
            and not (url.username or url.password or url.query or url.fragment)
        )
    except ValueError:
        valid = False
    if not valid:
        raise ExternalServiceError("Seedream 官方地址必须为 " + BASE_URL + "。")
    return base


class SeedreamHTTP(BoundedHTTP):
    validate_base = staticmethod(official_base)


class SeedreamImageProvider:
    name = "seedream"

    def __init__(self, transport=None):
        settings = get_settings()
        self.model = settings.image_model or DEFAULT_MODEL
        self.timeout = settings.image_api_timeout_seconds
        self.http = SeedreamHTTP(
            settings.image_api_key.get_secret_value(),
            settings.image_api_base_url,
            self.timeout,
            transport,
        )

    async def health_check(self):
        available = bool(self.http.key)
        message = "Seedream 已配置；仅检查配置，不验证模型权限、余额或触发付费生成。"
        try:
            official_base(self.http.base)
        except ExternalServiceError as exc:
            available, message = False, exc.message
        if not self.http.key:
            message = "未配置 Seedream API Key；请在项目 .env 的 IMAGE_API_KEY 填写后重启。"
        return ProviderHealth(
            provider=self.name,
            available=available,
            mock=False,
            requires_api_key=True,
            operations=list(OPERATIONS) if available else [],
            message=message,
        )

    async def create_character(self, prompt, settings):
        return await self.submit(prompt, settings, (), "create_character")

    async def virtual_try_on(self, character_images, product_images, prompt, settings):
        return await self.content(
            character_images, product_images, prompt, settings, "virtual_try_on"
        )

    async def generate_content_set(self, character_images, product_images, prompt, settings):
        return await self.content(
            character_images, product_images, prompt, settings, "generate_content_set"
        )

    async def content(self, characters, products, prompt, settings, operation):
        # Pro accepts ten references. Preserve both groups and their stable order.
        selected_characters, selected_products = characters[:5], products[:5]
        ordering = (
            f"前 {len(selected_characters)} 张参考图是虚构成年模特，"
            f"后 {len(selected_products)} 张是商品。保持人物身份与商品颜色、结构、Logo。"
        )
        return await self.submit(
            ordering + prompt,
            settings,
            selected_characters + selected_products,
            operation,
            {
                "character_references": len(selected_characters),
                "product_references": len(selected_products),
                "omitted_references": len(characters)
                + len(products)
                - len(selected_characters)
                - len(selected_products),
            },
        )

    async def edit_image(self, reference_images, prompt, settings):
        return await self.submit(prompt, settings, reference_images, "edit_image")

    async def generate_scene(self, references, prompt, settings):
        return await self.submit(prompt, settings, references, "generate_scene")

    async def submit(self, prompt, settings, references, operation, extra=None):
        metadata = {
            "mock": False,
            "real_generation": True,
            "model": self.model,
            "operation": operation,
            "references_used": bool(references),
            "reference_count": len(references),
            "seed_applied": False,
            "negative_prompt_mode": "prompt_text",
            "watermark": True,
            **(extra or {}),
        }
        images, request_ids, usage = [], [], []
        if len(references) > 10:
            return ProviderResult(
                success=False,
                provider=self.name,
                metadata=metadata,
                error=ProviderError(
                    code="invalid_input", message="Seedream 最多支持 10 张参考图。"
                ),
            )
        if settings.negative_prompt:
            prompt += "\n避免：" + settings.negative_prompt
        body = {
            "model": self.model,
            "prompt": prompt,
            "size": f"{OUTPUT_SIZE[0]}x{OUTPUT_SIZE[1]}",
            "response_format": "b64_json",
            "output_format": "jpeg",
            "stream": False,
            "watermark": True,
        }
        if references:
            body["image"] = [
                "data:" + ref.media_type + ";base64," + base64.b64encode(ref.data).decode("ascii")
                for ref in references
            ]

        async def one(index):
            try:
                # Pro returns one image per call. Each candidate is submitted once.
                payload = {
                    **body,
                    "prompt": prompt
                    + f"\n这是本套 {settings.requested_count} 张候选中的第 {index + 1} 张；"
                    "保持资料一致，生成自然的构图变化。",
                }
                value, request_id = await asyncio.wait_for(
                    self.http.post("/images/generations", max_bytes=24 * 1024 * 1024, json=payload),
                    timeout=max(0.1, self.timeout - 5),
                )
                data = value.get("data")
                if not isinstance(data, list) or len(data) != 1:
                    raise ValueError()
                encoded = data[0]["b64_json"]
                if not isinstance(encoded, str) or len(encoded) > 20 * 1024 * 1024:
                    raise ValueError()
                raw = base64.b64decode(encoded, validate=True)
                with Image.open(io.BytesIO(raw)) as decoded:
                    if decoded.format != "JPEG" or decoded.size != OUTPUT_SIZE:
                        raise ValueError()
                    decoded.load()
                item_usage = value.get("usage")
                image = ProviderImage(
                    data=raw,
                    media_type="image/jpeg",
                    width=OUTPUT_SIZE[0],
                    height=OUTPUT_SIZE[1],
                    metadata={**metadata, "request_id": request_id, "usage": item_usage},
                )
                return image, request_id, item_usage, None
            except TimeoutError:
                error = ProviderError(
                    code="timeout",
                    message="Seedream 响应超时；请求可能已计费，请检查用量后再重试。",
                    retryable=True,
                )
            except ExternalServiceError as exc:
                error = ProviderError(code=exc.code, message=exc.message, retryable=exc.retryable)
            except (
                KeyError,
                TypeError,
                ValueError,
                OSError,
                binascii.Error,
                Image.DecompressionBombError,
            ):
                error = ProviderError(
                    code="invalid_result",
                    message="Seedream 返回图片缺失或校验失败；重试可能产生额外费用。",
                    retryable=True,
                )
            return None, "", None, error

        outcomes = await asyncio.gather(*(one(i) for i in range(settings.requested_count)))
        errors = []
        for image, request_id, item_usage, error in outcomes:
            if image:
                images.append(image)
                request_ids.append(request_id)
                usage.append(item_usage)
            if error:
                errors.append(error)
        return ProviderResult(
            success=not errors,
            provider=self.name,
            provider_task_id=str(uuid.uuid4()),
            images=images,
            metadata={**metadata, "request_ids": request_ids, "usage": usage},
            error=errors[0] if errors else None,
        )
