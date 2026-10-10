import uuid
from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator

Gender = Literal["female", "male", "androgynous"]
AgeRange = Literal["18-24", "25-34", "35-44", "45-54", "55+"]
Name = Annotated[str, Field(min_length=1, max_length=100)]
Height = Annotated[int, Field(ge=100, le=250, strict=True)]
ShortText = Annotated[str, Field(max_length=60)]
LongText = Annotated[str, Field(max_length=80)]
Description = Annotated[str, Field(max_length=2000)]


class ProfileBase(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class ModelCreate(ProfileBase):
    name: Name
    gender: Gender
    age_range: AgeRange = "25-34"
    height: Height | None = None
    body_type: ShortText = ""
    skin_tone: ShortText = ""
    hair_style: LongText = ""
    hair_color: ShortText = ""
    style: LongText = ""
    description: Description = ""


class ModelUpdate(ProfileBase):
    name: Name | None = None
    gender: Gender | None = None
    age_range: AgeRange | None = None
    height: Height | None = None
    body_type: ShortText | None = None
    skin_tone: ShortText | None = None
    hair_style: LongText | None = None
    hair_color: ShortText | None = None
    style: LongText | None = None
    description: Description | None = None

    @field_validator("*")
    @classmethod
    def reject_null_text(cls, value, info: ValidationInfo):
        if value is None and info.field_name != "height":
            raise ValueError("只有身高可以为空；清空可选文本请使用空字符串。")
        return value


class ImageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    image_url: str
    image_type: str
    metadata: dict = Field(validation_alias="image_metadata")
    created_at: datetime


class ModelResponse(ModelCreate):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    reference_images: list[ImageResponse]
    created_at: datetime
    updated_at: datetime


class ModelPage(BaseModel):
    items: list[ModelResponse]
    total: int
    limit: int
    offset: int
