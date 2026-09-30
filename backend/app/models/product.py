import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

CATEGORY_SQL = (
    "'top','bottom','dress','shoes','bag','necklace','bracelet','ring','watch','hat','other'"
)


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (CheckConstraint(f"category IN ({CATEGORY_SQL})", name="ck_product_category"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    brand: Mapped[str] = mapped_column(String(100), default="")
    category: Mapped[str] = mapped_column(String(32))
    color: Mapped[str] = mapped_column(String(100), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    product_features: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    images: Mapped[list["ProductImage"]] = relationship(
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="(ProductImage.created_at, ProductImage.id)",
    )

    @property
    def original_images(self) -> list["ProductImage"]:
        return [image for image in self.images if image.image_type == "original"]

    @property
    def processed_images(self) -> list["ProductImage"]:
        return [image for image in self.images if image.image_type == "processed"]


class ProductImage(Base):
    __tablename__ = "product_images"
    __table_args__ = (
        CheckConstraint("image_type IN ('original','processed')", name="ck_product_image_type"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), index=True
    )
    image_url: Mapped[str] = mapped_column(Text)
    image_type: Mapped[str] = mapped_column(String(32))
    image_metadata: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
