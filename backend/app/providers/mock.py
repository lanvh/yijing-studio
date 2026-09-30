import asyncio
import hashlib
import io

from PIL import Image, ImageDraw, ImageFont
from pydantic import ValidationError

from app.providers.contracts import (
    OPERATIONS,
    GenerationRequest,
    GenerationSettings,
    ImageReference,
    ProviderError,
    ProviderHealth,
    ProviderImage,
    ProviderResult,
)


class MockImageProvider:
    name = "mock"

    def __init__(self, *, fail_at: frozenset[int] = frozenset()):
        # Explicit local test hook. HTTP clients cannot enable simulated failures.
        if any(type(index) is not int or index < 1 or index > 6 for index in fail_at):
            raise ValueError("Failure positions must be between 1 and 6.")
        self.fail_at = fail_at

    async def health_check(self) -> ProviderHealth:
        return ProviderHealth(
            provider=self.name,
            available=True,
            mock=True,
            requires_api_key=False,
            operations=list(OPERATIONS),
            message="本地 Mock 可用；输出带标记的占位图，不调用 AI。",
        )

    async def create_character(self, prompt: str, settings: GenerationSettings) -> ProviderResult:
        return await self._submit("create_character", prompt, settings)

    async def virtual_try_on(
        self,
        character_images: tuple[ImageReference, ...],
        product_images: tuple[ImageReference, ...],
        prompt: str,
        settings: GenerationSettings,
    ) -> ProviderResult:
        return await self._submit(
            "virtual_try_on",
            prompt,
            settings,
            character_images=character_images,
            product_images=product_images,
        )

    async def edit_image(
        self,
        reference_images: tuple[ImageReference, ...],
        prompt: str,
        settings: GenerationSettings,
    ) -> ProviderResult:
        return await self._submit("edit_image", prompt, settings, reference_images=reference_images)

    async def generate_scene(
        self, references: tuple[ImageReference, ...], prompt: str, settings: GenerationSettings
    ) -> ProviderResult:
        return await self._submit("generate_scene", prompt, settings, reference_images=references)

    async def generate_content_set(
        self,
        character_images: tuple[ImageReference, ...],
        product_images: tuple[ImageReference, ...],
        prompt: str,
        settings: GenerationSettings,
    ) -> ProviderResult:
        return await self._submit(
            "generate_content_set",
            prompt,
            settings,
            character_images=character_images,
            product_images=product_images,
        )

    async def _submit(self, operation, prompt, settings, **references) -> ProviderResult:
        try:
            request = GenerationRequest(
                operation=operation, prompt=prompt, settings=settings, **references
            )
        except ValidationError:
            return ProviderResult(
                success=False,
                provider=self.name,
                cost=0,
                error=ProviderError(code="invalid_input", message="生成请求参数或参考图分组无效。"),
            )
        return await asyncio.to_thread(self._render, request)

    def _render(self, request: GenerationRequest) -> ProviderResult:
        settings = request.settings
        images = []
        failed = []
        # Fixed-size drawing canvas keeps labels readable at every permitted output size.
        for index in range(1, settings.requested_count + 1):
            if index in self.fail_at:
                failed.append(index)
                continue
            digest = hashlib.sha256(
                f"{request.operation}:{request.prompt}:{settings.seed}:{index}".encode()
            ).digest()
            accent = tuple(75 + value % 80 for value in digest[:3])
            canvas = Image.new("RGB", (600, 800), "#eef1e7")
            draw = ImageDraw.Draw(canvas)
            small = ImageFont.load_default(size=18)
            title = ImageFont.load_default(size=36)
            label = ImageFont.load_default(size=23)
            draw.rounded_rectangle((28, 28, 572, 772), radius=20, outline=accent, width=3)
            draw.text((52, 54), "AI SEED STUDIO", font=small, fill=accent)
            draw.text((52, 104), "MOCK / PLACEHOLDER", font=title, fill="#264237")
            draw.text((52, 160), "NOT AN AI-GENERATED PHOTO", font=small, fill="#264237")
            # Abstract geometry deliberately avoids resembling a real try-on result.
            draw.ellipse((220, 242, 380, 402), fill=accent)
            draw.rounded_rectangle((155, 423, 445, 568), radius=28, outline=accent, width=7)
            draw.line((182, 490, 418, 490), fill=accent, width=5)
            draw.text((52, 612), request.operation.upper(), font=label, fill="#264237")
            draw.text(
                (52, 658),
                f"Sample {index:02d} / {settings.requested_count:02d}",
                font=label,
                fill=accent,
            )
            draw.text(
                (52, 708),
                "Development test only. References not rendered.",
                font=small,
                fill="#596d52",
            )
            canvas = canvas.resize((settings.width, settings.height), Image.Resampling.LANCZOS)
            output = io.BytesIO()
            canvas.save(output, format="JPEG", quality=88)
            data = output.getvalue()
            images.append(
                ProviderImage(
                    data=data,
                    media_type="image/jpeg",
                    width=settings.width,
                    height=settings.height,
                    metadata={
                        "mock": True,
                        "aigc_label": "mock_placeholder",
                        "index": index,
                        "sha256": hashlib.sha256(data).hexdigest(),
                        "operation": request.operation,
                    },
                )
            )
        all_references = (
            request.character_images + request.product_images + request.reference_images
        )
        return ProviderResult(
            success=not failed,
            provider=self.name,
            images=images,
            cost=0,
            metadata={
                "mock": True,
                "real_generation": False,
                "references_used": False,
                "reference_count": len(all_references),
                "reference_sha256": [
                    hashlib.sha256(image.data).hexdigest() for image in all_references
                ],
                "negative_prompt_applied": False,
                "prompt_sha256": hashlib.sha256(request.prompt.encode()).hexdigest(),
                "operation": request.operation,
                "requested_count": settings.requested_count,
                "seed": settings.seed,
                "failed_indices": failed,
                "outcome": "SUCCEEDED" if not failed else ("PARTIAL" if images else "FAILED"),
            },
            error=ProviderError(
                code="generation_failed", message="Mock 模拟生成失败。", retryable=True
            )
            if failed
            else None,
        )
