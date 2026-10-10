import uuid
from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.ai_model import ImageResponse

Category = Literal[
    "top",
    "bottom",
    "dress",
    "shoes",
    "bag",
    "necklace",
    "bracelet",
    "ring",
    "watch",
    "hat",
    "other",
]
CATEGORIES = [
    "top",
    "bottom",
    "dress",
    "shoes",
    "bag",
    "necklace",
    "bracelet",
    "ring",
    "watch",
    "hat",
    "other",
]
FeatureText = Annotated[str, Field(max_length=300)]


class ProductFeatureNotes(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    material: FeatureText = ""
    pattern: FeatureText = ""
    logo_description: FeatureText = ""
    shape: FeatureText = ""
    critical_features: list[Annotated[str, Field(min_length=1, max_length=200)]] = Field(
        default_factory=list, max_length=20
    )


class ProductCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    name: str = Field(min_length=1, max_length=100)
    brand: str = Field(default="", max_length=100)
    category: Category = "other"
    color: str = Field(default="", max_length=100)
    description: str = Field(default="", max_length=2000)
    feature_notes: ProductFeatureNotes = Field(default_factory=ProductFeatureNotes)


class ProductUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    name: str | None = Field(default=None, min_length=1, max_length=100)
    brand: str | None = Field(default=None, max_length=100)
    category: Category | None = None
    color: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default=None, max_length=2000)
    feature_notes: ProductFeatureNotes | None = None

    @field_validator("*")
    @classmethod
    def reject_null(cls, value):
        if value is None:
            raise ValueError("字段不能为 null；清空文本请使用空字符串。")
        return value


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    brand: str
    category: Category = "other"
    color: str
    description: str
    product_features: dict
    original_images: list[ImageResponse]
    processed_images: list[ImageResponse]
    created_at: datetime
    updated_at: datetime


class ProductPage(BaseModel):
    items: list[ProductResponse]
    total: int
    limit: int
    offset: int
