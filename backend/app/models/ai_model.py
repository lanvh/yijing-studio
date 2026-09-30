import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AIModel(Base):
    __tablename__ = "ai_models"
    __table_args__ = (
        CheckConstraint(
            "height IS NULL OR (height >= 100 AND height <= 250)", name="ck_model_height"
        ),
        CheckConstraint(
            "age_range IN ('18-24','25-34','35-44','45-54','55+')", name="ck_model_adult_age"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    gender: Mapped[str] = mapped_column(String(32))
    age_range: Mapped[str] = mapped_column(String(32))
    height: Mapped[int | None]
    body_type: Mapped[str] = mapped_column(String(60), default="")
    skin_tone: Mapped[str] = mapped_column(String(60), default="")
    hair_style: Mapped[str] = mapped_column(String(80), default="")
    hair_color: Mapped[str] = mapped_column(String(60), default="")
    style: Mapped[str] = mapped_column(String(80), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    character_prompt: Mapped[str] = mapped_column(Text, default="")
    negative_prompt: Mapped[str] = mapped_column(Text, default="")
    provider_metadata: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    reference_images: Mapped[list["AIModelImage"]] = relationship(
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="(AIModelImage.created_at, AIModelImage.id)",
    )


class AIModelImage(Base):
    __tablename__ = "ai_model_images"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    model_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ai_models.id", ondelete="CASCADE"), index=True
    )
    image_url: Mapped[str] = mapped_column(Text)
    image_type: Mapped[str] = mapped_column(String(32), default="reference")
    image_metadata: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
