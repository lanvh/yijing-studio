import base64
import binascii
import io
import uuid

from PIL import Image

from app.core.config import get_settings
from app.providers.contracts import (
    OPERATIONS,
    ProviderError,
    ProviderHealth,
    ProviderImage,
    ProviderResult,
)
from app.providers.openai_http import ExternalServiceError, OpenAIHTTP, official_base


class OpenAIImageProvider:
    name = "openai"

    def __init__(self, transport=None):
        settings = get_settings()
        self.model = settings.image_model or "gpt-image-2.5-sunburst"
        self.quality = settings.image_quality
        self.http = OpenAIHTTP(
            settings.image_api_key.get_secret_value(),
            settings.image_api_base_url,
            settings.image_api_timeout_seconds,
            transport,
        )

    async def health_check(self):
        message = "官方图片服务已配置；此处仅检查配置，不验证账户权限或触发付费生成。"
        available = bool(self.http.key)
        try:
            official_base(self.http.base)
        except ExternalServiceError as exc:
            available, message = False, exc.message
        if not self.http.key:
            message = "未配置图片 API Key；请在服务端 .env 配置后重启。"
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
        ordering = (
            f"The first {len(characters)} reference images define the adult fictional character. "
            f"The remaining {len(products)} reference images show the product. "
            "Use the character's identity and visibly preserve the referenced product. "
        )
        return await self.submit(ordering + prompt, settings, characters + products, operation)

    async def edit_image(self, reference_images, prompt, settings):
        return await self.submit(prompt, settings, reference_images, "edit_image")

    async def generate_scene(self, references, prompt, settings):
        return await self.submit(prompt, settings, references, "generate_scene")

    async def submit(self, prompt, settings, references, operation):
        images = []
        job = str(uuid.uuid4())
        metadata = {
            "mock": False,
            "real_generation": True,
            "model": self.model,
            "quality": self.quality,
            "operation": operation,
            "references_used": bool(references),
            "negative_prompt_mode": "prompt_text",
            "seed_applied": False,
        }
        try:
            if settings.negative_prompt:
                prompt += "\nAvoid these artifacts: " + settings.negative_prompt
            fields = dict(
                model=self.model,
                prompt=prompt,
                n=settings.requested_count,
                size=f"{settings.width}x{settings.height}",
                quality=self.quality,
                output_format="jpeg",
            )
            if references:
                files = [
                    ("image[]", (f"reference-{index}.jpg", ref.data, ref.media_type))
                    for index, ref in enumerate(references)
                ]
                value, request_id = await self.http.post(
                    "/images/edits",
                    data={key: str(value) for key, value in fields.items()},
                    files=files,
                )
            else:
                value, request_id = await self.http.post("/images/generations", json=fields)
            job = request_id or job
            metadata["usage"] = value.get("usage")
            data = value.get("data")
            if not isinstance(data, list) or len(data) > settings.requested_count:
                raise ExternalServiceError("图片服务返回了无效结果。", "invalid_result")
            for item in data:
                try:
                    encoded = item["b64_json"]
                    if not isinstance(encoded, str) or len(encoded) > 21 * 1024 * 1024:
                        raise ValueError()
                    raw = base64.b64decode(encoded, validate=True)
                    with Image.open(io.BytesIO(raw)) as decoded:
                        if decoded.format != "JPEG" or decoded.size != (
                            settings.width,
                            settings.height,
                        ):
                            raise ValueError()
                        decoded.load()
                    images.append(
                        ProviderImage(
                            data=raw,
                            media_type="image/jpeg",
                            width=settings.width,
                            height=settings.height,
                            metadata=metadata,
                        )
                    )
                except (KeyError, TypeError, ValueError, OSError, binascii.Error):
                    continue
            success = len(images) == settings.requested_count
            return ProviderResult(
                success=success,
                provider=self.name,
                provider_task_id=job,
                images=images,
                metadata=metadata,
                error=None
                if success
                else ProviderError(
                    code="invalid_result",
                    message="部分图片未返回或校验失败；重试可能产生额外费用。",
                    retryable=True,
                ),
            )
        except ExternalServiceError as exc:
            return ProviderResult(
                success=False,
                provider=self.name,
                provider_task_id=job,
                images=images,
                metadata=metadata,
                error=ProviderError(code=exc.code, message=exc.message, retryable=exc.retryable),
            )
