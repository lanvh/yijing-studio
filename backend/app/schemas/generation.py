import uuid
from datetime import datetime

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
    "bookstore": "书店",
    "gallery": "艺术展馆",
    "rooftop": "城市天台",
    "park": "公园绿道",
    "seaside": "海边",
    "old_town": "复古街区",
    "subway": "地铁站",
    "office": "通勤街景",
    "hotel": "酒店大堂",
    "autumn_road": "秋日林荫道",
    "night_street": "夜晚霓虹街头",
    "home": "居家窗边",
}
STYLES = {
    "dewu": "潮流种草",
    "streetwear": "街头潮流",
    "minimal": "极简",
    "korean": "韩系",
    "sport": "运动",
    "luxury": "轻奢",
    "casual": "休闲",
    "american_vintage": "美式复古",
    "preppy": "复古学院",
    "cleanfit": "清爽简约",
    "french": "法式日常",
    "cityboy": "城市少年",
    "outdoor": "山系户外",
    "workwear": "工装",
    "y2k": "千禧辣妹",
    "old_money": "经典优雅",
    "japanese": "日系松弛",
    "editorial": "时尚杂志",
    "soft": "温柔日常",
}
POSES = {
    "front_standing": "正面站姿",
    "side_standing": "侧面站姿",
    "walking": "行走",
    "sitting": "坐姿",
    "mirror_selfie": "镜前自拍",
    "look_down": "低头",
    "detail_pose": "细节展示",
    "leaning_wall": "靠墙站立",
    "hands_pockets": "双手插兜",
    "crossing_street": "过街抓拍",
    "adjusting_collar": "整理衣领",
    "looking_back": "回头",
    "sitting_steps": "台阶坐姿",
    "holding_coffee": "手持咖啡",
    "turning": "轻转身",
    "close_up": "上半身近景",
    "back_view": "背影",
    "natural_candid": "自然抓拍",
}


class TaskCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    model_id: uuid.UUID
    product_id: uuid.UUID
    request_key: uuid.UUID = Field(default_factory=uuid.uuid4)
    scene: str = Field(default="studio", max_length=32)
    style: str = Field(default="casual", max_length=32)
    pose: str = Field(default="front_standing", max_length=32)
    custom_direction: str = Field(default="", max_length=1200)

    @field_validator("scene", "style", "pose")
    @classmethod
    def valid_direction(cls, value, info):
        choices = {"scene": SCENES, "style": STYLES, "pose": POSES}
        if value not in choices[info.field_name]:
            raise ValueError("请选择有效的预设方向。")
        return value

    @field_validator("custom_direction")
    @classmethod
    def clean_direction(cls, value):
        return value.strip()

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
    custom_direction: str = ""
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
