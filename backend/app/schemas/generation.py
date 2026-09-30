import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

SCENES = {
    "street": "街头",
    "mall": "商场",
    "mirror": "镜前",
    "studio": "摄影棚",
    "cafe": "咖啡馆",
    "parking": "停车场",
    "campus": "校园",
    "gym": "健身房",
    "travel": "旅行",
}
STYLES = {
    "dewu": "潮流种草",
    "streetwear": "街头潮流",
    "minimal": "极简",
    "korean": "韩系",
    "sport": "运动",
    "luxury": "轻奢",
    "casual": "休闲",
}
POSES = {
    "front_standing": "正面站姿",
    "side_standing": "侧面站姿",
    "walking": "行走",
    "sitting": "坐姿",
    "mirror_selfie": "镜前自拍",
    "look_down": "低头",
    "detail_pose": "细节展示",
}


class TaskCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    model_id: uuid.UUID
    product_id: uuid.UUID
    request_key: uuid.UUID = Field(default_factory=uuid.uuid4)
    scene: Literal[
        "street", "mall", "mirror", "studio", "cafe", "parking", "campus", "gym", "travel"
    ] = "studio"
    style: Literal["dewu", "streetwear", "minimal", "korean", "sport", "luxury", "casual"] = (
        "casual"
    )
    pose: Literal[
        "front_standing",
        "side_standing",
        "walking",
        "sitting",
        "mirror_selfie",
        "look_down",
        "detail_pose",
    ] = "front_standing"
    requested_count: int = Field(default=4, strict=True)

    @field_validator("requested_count")
    @classmethod
    def valid_count(cls, value):
        if value not in (1, 2, 4, 6):
            raise ValueError("请选择 1、2、4 或 6 张。")
        return value


class CopyEdit(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    title: str = Field(min_length=1, max_length=200)
    caption: str = Field(min_length=1, max_length=5000)
    hashtags: list[str] = Field(max_length=20)
    product_summary: str = Field(max_length=2000)
    styling_notes: str = Field(max_length=2000)

    @field_validator("hashtags")
    @classmethod
    def valid_tags(cls, tags):
        if any(not tag.strip() or len(tag) > 60 for tag in tags):
            raise ValueError("标签不能为空且每条最多 60 字。")
        return tags


class CopyResponse(CopyEdit):
    model_config = ConfigDict(from_attributes=True)
    source: str


class ResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    image_url: str
    quality_score: float | None
    identity_score: float | None
    product_score: float | None
    anatomy_score: float | None
    aesthetic_score: float | None
    is_selected: bool
    metadata: dict = Field(validation_alias="result_metadata")
    created_at: datetime


class TaskSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    request_key: uuid.UUID
    model_id: uuid.UUID | None
    product_id: uuid.UUID | None
    model_name: str
    product_name: str
    scene: str
    style: str
    pose: str
    requested_count: int
    status: str
    is_mock: bool
    error_message: str
    attempt: int
    is_active: bool
    can_retry: bool
    result_count: int
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None


class TaskResponse(TaskSummary):
    results: list[ResultResponse]
    content_copy: CopyResponse | None = Field(validation_alias="copy", serialization_alias="copy")


class TaskPage(BaseModel):
    items: list[TaskSummary]
    total: int
    limit: int
    offset: int


class ResultEdit(BaseModel):
    model_config = ConfigDict(extra="forbid")
    is_selected: bool = Field(strict=True)
