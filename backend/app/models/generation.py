import uuid
from datetime import UTC, datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class GenerationTask(Base):
    __tablename__ = "generation_tasks"
    __table_args__ = (
        CheckConstraint(
            "status IN ('PENDING','PROCESSING','SUCCEEDED','PARTIAL','FAILED')",
            name="ck_task_status",
        ),
        CheckConstraint("requested_count IN (1,2,4,6)", name="ck_task_count"),
        UniqueConstraint("user_id", "request_key", name="uq_task_request"),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    model_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("ai_models.id", ondelete="SET NULL")
    )
    product_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("products.id", ondelete="SET NULL")
    )
    request_key: Mapped[uuid.UUID]
    scene: Mapped[str] = mapped_column(String(32))
    style: Mapped[str] = mapped_column(String(32))
    pose: Mapped[str] = mapped_column(String(32))
    requested_count: Mapped[int]
    status: Mapped[str] = mapped_column(String(16), default="PENDING")
    provider: Mapped[str] = mapped_column(String(64))
    provider_job_id: Mapped[str | None] = mapped_column(String(256))
    prompt: Mapped[str] = mapped_column(Text)
    negative_prompt: Mapped[str] = mapped_column(Text)
    error_message: Mapped[str] = mapped_column(Text, default="")
    snapshot: Mapped[dict] = mapped_column(JSONB)
    attempt: Mapped[int] = mapped_column(default=0)
    lease_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    results: Mapped[list["GenerationResult"]] = relationship(
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="(GenerationResult.created_at, GenerationResult.id)",
    )
    copy: Mapped["ContentCopy | None"] = relationship(
        cascade="all, delete-orphan",
        passive_deletes=True,
        uselist=False,
    )

    @property
    def model_name(self) -> str:
        return self.snapshot["model"]["name"]

    @property
    def product_name(self) -> str:
        return self.snapshot["product"]["name"]

    @property
    def is_mock(self) -> bool:
        return self.provider == "mock"

    @property
    def is_active(self) -> bool:
        return self.status == "PROCESSING" and bool(
            self.lease_expires_at and self.lease_expires_at > datetime.now(UTC)
        )

    @property
    def can_retry(self) -> bool:
        return (
            self.attempt < 3
            and not self.is_active
            and self.status in {"PENDING", "PROCESSING", "FAILED", "PARTIAL"}
        )

    @property
    def result_count(self) -> int:
        return len(self.results)


class GenerationResult(Base):
    __tablename__ = "generation_results"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    task_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("generation_tasks.id", ondelete="CASCADE"), index=True
    )
    image_url: Mapped[str] = mapped_column(Text)
    storage_key: Mapped[str] = mapped_column(Text)
    quality_score: Mapped[float | None]
    identity_score: Mapped[float | None]
    product_score: Mapped[float | None]
    anatomy_score: Mapped[float | None]
    aesthetic_score: Mapped[float | None]
    is_selected: Mapped[bool] = mapped_column(default=True)
    result_metadata: Mapped[dict] = mapped_column("metadata", JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ContentCopy(Base):
    __tablename__ = "content_copy"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    task_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("generation_tasks.id", ondelete="CASCADE"), unique=True
    )
    title: Mapped[str] = mapped_column(String(200))
    caption: Mapped[str] = mapped_column(Text)
    hashtags: Mapped[list] = mapped_column(JSONB)
    product_summary: Mapped[str] = mapped_column(Text)
    styling_notes: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(32), default="local_template")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
