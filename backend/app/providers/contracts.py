import uuid
from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

Operation = Literal[
    "create_character", "virtual_try_on", "edit_image", "generate_scene", "generate_content_set"
]
OPERATIONS: tuple[Operation, ...] = (
    "create_character",
    "virtual_try_on",
    "edit_image",
    "generate_scene",
    "generate_content_set",
)


class GenerationSettings(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    requested_count: int = Field(default=4, strict=True)
    width: int = Field(default=768, ge=256, le=1536, strict=True)
    height: int = Field(default=1024, ge=256, le=1536, strict=True)
    seed: int = Field(default=0, ge=0, le=4294967295, strict=True)
    negative_prompt: str = Field(default="", max_length=3000)

    @field_validator("requested_count")
    @classmethod
    def allowed_count(cls, value):
        if value not in {1, 2, 4, 6}:
            raise ValueError("Requested count must be 1, 2, 4 or 6.")
        return value


class ImageReference(BaseModel):
    """Trusted, previously validated private image bytes, never a URL or client path."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    data: bytes = Field(min_length=1, max_length=15 * 1024 * 1024, exclude=True, repr=False)
    media_type: Literal["image/jpeg", "image/png", "image/webp"] = "image/jpeg"


class GenerationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)
    operation: Operation = "generate_content_set"
    prompt: str = Field(min_length=1, max_length=6000)
    settings: GenerationSettings = Field(default_factory=GenerationSettings)
    character_images: tuple[ImageReference, ...] = Field(default=(), max_length=8)
    product_images: tuple[ImageReference, ...] = Field(default=(), max_length=8)
    reference_images: tuple[ImageReference, ...] = Field(default=(), max_length=8)

    @model_validator(mode="after")
    def reference_groups(self):
        if self.operation in {"virtual_try_on", "generate_content_set"}:
            if not self.character_images or not self.product_images or self.reference_images:
                raise ValueError("Character and product references are required.")
        elif self.operation in {"edit_image", "generate_scene"}:
            if not self.reference_images or self.character_images or self.product_images:
                raise ValueError("Only reference_images are required for this operation.")
        elif self.character_images or self.product_images or self.reference_images:
            raise ValueError("create_character does not accept image references.")
        return self


class ProviderError(BaseModel):
    code: Literal[
        "invalid_input",
        "unavailable",
        "timeout",
        "generation_failed",
        "internal_error",
        "invalid_result",
    ]
    message: str
    retryable: bool = False


class ProviderImage(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    data: bytes = Field(min_length=1, max_length=15 * 1024 * 1024, exclude=True, repr=False)
    media_type: Literal["image/jpeg", "image/png"]
    width: int = Field(ge=1, le=4096)
    height: int = Field(ge=1, le=4096)
    metadata: dict = Field(default_factory=dict)


class ProviderResult(BaseModel):
    success: bool
    provider: str
    provider_task_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()), min_length=1, max_length=256
    )
    images: list[ProviderImage] = Field(default_factory=list, max_length=6)
    metadata: dict = Field(default_factory=dict)
    cost: float | None = Field(default=None, ge=0)
    error: ProviderError | None = None

    @model_validator(mode="after")
    def consistent_result(self):
        if self.success and (not self.images or self.error):
            raise ValueError("Success requires images and no error.")
        if not self.success and self.error is None:
            raise ValueError("Failure requires an error.")
        return self


class ProviderHealth(BaseModel):
    provider: str
    available: bool
    mock: bool
    requires_api_key: bool | None
    operations: list[Operation]
    message: str


class ImageProvider(Protocol):
    name: str

    async def health_check(self) -> ProviderHealth: ...
    async def create_character(
        self, prompt: str, settings: GenerationSettings
    ) -> ProviderResult: ...
    async def virtual_try_on(
        self,
        character_images: tuple[ImageReference, ...],
        product_images: tuple[ImageReference, ...],
        prompt: str,
        settings: GenerationSettings,
    ) -> ProviderResult: ...
    async def edit_image(
        self,
        reference_images: tuple[ImageReference, ...],
        prompt: str,
        settings: GenerationSettings,
    ) -> ProviderResult: ...
    async def generate_scene(
        self, references: tuple[ImageReference, ...], prompt: str, settings: GenerationSettings
    ) -> ProviderResult: ...
    async def generate_content_set(
        self,
        character_images: tuple[ImageReference, ...],
        product_images: tuple[ImageReference, ...],
        prompt: str,
        settings: GenerationSettings,
    ) -> ProviderResult: ...
