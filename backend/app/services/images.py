import asyncio
import io
import logging

from PIL import Image

from app.core.config import get_settings
from app.providers.contracts import (
    GenerationRequest,
    ProviderError,
    ProviderHealth,
    ProviderResult,
)
from app.providers.router import ProviderRouter, ProviderUnavailable

logger = logging.getLogger(__name__)


class ImageService:
    def __init__(self, router: ProviderRouter | None = None, timeout_seconds: float | None = None):
        self.router = router if router is not None else ProviderRouter()
        self.timeout = (
            get_settings().image_provider_timeout_seconds
            if timeout_seconds is None
            else timeout_seconds
        )
        if self.timeout <= 0:
            raise ValueError("Provider timeout must be positive.")

    async def health_check(self) -> ProviderHealth:
        try:
            provider = self.router.select()
            return await asyncio.wait_for(provider.health_check(), timeout=self.timeout)
        except (ProviderUnavailable, TimeoutError):
            message = "所配置的图片 Provider 未实现或暂时不可用。"
        except Exception as exc:
            logger.error("Image provider health check failed: %s", type(exc).__name__)
            message = "图片 Provider 健康检查失败。"
        return ProviderHealth(
            provider=self.router.name,
            available=False,
            mock=self.router.name == "mock",
            requires_api_key=False if self.router.name == "mock" else None,
            operations=[],
            message=message,
        )

    def failure(self, code, message, *, retryable=False) -> ProviderResult:
        return ProviderResult(
            success=False,
            provider=self.router.name,
            error=ProviderError(code=code, message=message, retryable=retryable),
        )

    async def generate(self, request: GenerationRequest) -> ProviderResult:
        try:
            provider = self.router.select()
            settings = request.settings
            if request.operation == "create_character":
                call = provider.create_character(request.prompt, settings)
            elif request.operation == "virtual_try_on":
                call = provider.virtual_try_on(
                    request.character_images, request.product_images, request.prompt, settings
                )
            elif request.operation == "edit_image":
                call = provider.edit_image(request.reference_images, request.prompt, settings)
            elif request.operation == "generate_scene":
                call = provider.generate_scene(request.reference_images, request.prompt, settings)
            else:
                call = provider.generate_content_set(
                    request.character_images, request.product_images, request.prompt, settings
                )
            result = await asyncio.wait_for(call, timeout=self.timeout)
            if result.provider != self.router.name or not self.valid_result(result, request):
                return self.failure("invalid_result", "图片 Provider 返回了无效结果。")
            return result
        except ProviderUnavailable:
            return self.failure("unavailable", "所配置的图片 Provider 尚未实现。")
        except TimeoutError:
            return self.failure("timeout", "图片 Provider 响应超时，请稍后重试。", retryable=True)
        except Exception as exc:
            # Do not include vendor exception text: it may contain prompts or credentials.
            logger.error("Image provider call failed: %s", type(exc).__name__)
            return self.failure(
                "internal_error", "图片 Provider 调用失败，请稍后重试。", retryable=True
            )

    @staticmethod
    def valid_result(result: ProviderResult, request: GenerationRequest) -> bool:
        if len(result.images) > request.settings.requested_count:
            return False
        if result.success and len(result.images) != request.settings.requested_count:
            return False
        if len({image.id for image in result.images}) != len(result.images):
            return False
        for image in result.images:
            try:
                with Image.open(io.BytesIO(image.data)) as decoded:
                    expected = "JPEG" if image.media_type == "image/jpeg" else "PNG"
                    if (
                        decoded.format != expected
                        or decoded.size != (image.width, image.height)
                        or decoded.size != (request.settings.width, request.settings.height)
                    ):
                        return False
                    decoded.load()
            except (OSError, ValueError, SyntaxError):
                return False
        return True
