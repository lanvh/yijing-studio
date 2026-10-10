import asyncio
import logging
import uuid
from datetime import UTC, datetime

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.product import Product, ProductImage
from app.providers.ark_text import ArkTextProvider
from app.providers.openai_http import ExternalServiceError
from app.providers.openai_text import OpenAITextProvider
from app.repositories.products import ProductRepository
from app.schemas.product import CATEGORIES, ProductCreate, ProductUpdate
from app.services.image_uploads import UploadRejected, validate_reference
from app.services.product_analyzer import ProductAnalyzer, image_palette
from app.storage.local import ImageStorage

logger = logging.getLogger(__name__)


class ProductNotFound(Exception):
    pass


class ProductService:
    def __init__(self, db: Session, storage: ImageStorage):
        self.db = db
        self.storage = storage
        self.products = ProductRepository(db)
        self.analyzer = ProductAnalyzer()

    def owned(self, product_id: uuid.UUID, user_id: uuid.UUID, *, lock=False) -> Product:
        product = self.products.owned(product_id, user_id, lock=lock)
        if product is None:
            raise ProductNotFound
        return product

    def create(self, user_id: uuid.UUID, payload: ProductCreate) -> Product:
        values = payload.model_dump()
        notes = values.pop("feature_notes")
        product = Product(user_id=user_id, images=[], **values)
        product.product_features = self.analyzer.analyze(product, notes)
        self.db.add(product)
        self.db.commit()
        return product

    def update(self, product_id: uuid.UUID, user_id: uuid.UUID, payload: ProductUpdate) -> Product:
        product = self.owned(product_id, user_id, lock=True)
        values = payload.model_dump(exclude_unset=True)
        incoming = values.pop("feature_notes", {})
        notes = {**product.product_features.get("confirmed", {}), **incoming}
        for key, value in values.items():
            setattr(product, key, value)
        product.product_features = self.analyzer.analyze(product, notes)
        product.updated_at = datetime.now(UTC)
        self.db.commit()
        return product

    def analyze(self, product_id: uuid.UUID, user_id: uuid.UUID) -> Product:
        product = self.owned(product_id, user_id, lock=True)
        product.product_features = self.analyzer.analyze(product)
        product.updated_at = datetime.now(UTC)
        self.db.commit()
        return self.analyze_visual(product_id, user_id)

    def analyze_visual(self, product_id, user_id):
        product = self.owned(product_id, user_id, lock=True)
        if get_settings().llm_provider not in {"openai", "ark"} or not product.processed_images:
            return product
        image_ids = [str(i.id) for i in product.processed_images]
        revision = product.updated_at
        images = [
            self.storage.read(self.key(user_id, product_id, i))
            for i in product.processed_images[:4]
        ]
        facts = {"name": product.name, "category": product.category, "color": product.color}
        self.db.commit()
        try:
            text_provider = (
                ArkTextProvider() if get_settings().llm_provider == "ark" else OpenAITextProvider()
            )
            findings = asyncio.run(text_provider.analyze(facts, images)).model_dump()
            report = {
                "status": "suggestions_ready",
                "findings": findings,
                "source": get_settings().llm_provider,
                "confirmed": False,
                "image_ids": image_ids,
            }
        except ExternalServiceError as exc:
            report = {
                "status": "failed",
                "message": exc.message,
                "source": get_settings().llm_provider,
                "confirmed": False,
            }
        product = self.owned(product_id, user_id, lock=True)
        if (
            product.updated_at != revision
            or [str(i.id) for i in product.processed_images] != image_ids
        ):
            return product
        if report.get("findings") and product.category == "other":
            inferred = report["findings"].get("category")
            if inferred in CATEGORIES:
                product.category = inferred
        product.product_features = {**product.product_features, "ai_analysis": report}
        self.db.commit()
        return product

    @staticmethod
    def key(user_id: uuid.UUID, product_id: uuid.UUID, image: ProductImage) -> str:
        extension = image.image_metadata["extension"]
        if extension not in {"jpg", "png", "webp"}:
            raise ValueError("Invalid image extension.")
        return f"products/{user_id}/{product_id}/{image.id}.{extension}"

    def cleanup(self, keys: list[str]) -> None:
        for key in keys:
            try:
                self.storage.delete(key)
            except OSError:
                logger.exception("Could not clean up private product image: %s", key)

    def delete(self, product_id: uuid.UUID, user_id: uuid.UUID) -> None:
        product = self.owned(product_id, user_id, lock=True)
        keys = [self.key(user_id, product.id, image) for image in product.images]
        self.db.delete(product)
        self.db.commit()
        self.cleanup(keys)

    def upload(
        self, product_id: uuid.UUID, user_id: uuid.UUID, upload: UploadFile, rights_confirmed: bool
    ) -> Product:
        product = self.owned(product_id, user_id, lock=True)
        if not rights_confirmed:
            raise UploadRejected("请确认拥有商品图片的使用权，或已获授权。")
        if len(product.original_images) >= get_settings().max_product_images:
            raise UploadRejected("商品图片已达上限，请先移除不需要的图片。", 409)
        validated = validate_reference(upload)
        pair_id = str(uuid.uuid4())
        common = {
            "pair_id": pair_id,
            "rights_confirmed": True,
            "confirmed_at": datetime.now(UTC).isoformat(),
            "moderation_status": "not_screened",
        }
        original_id, processed_id = uuid.uuid4(), uuid.uuid4()
        original = ProductImage(
            id=original_id,
            product_id=product.id,
            image_type="original",
            image_url=f"/api/v1/products/{product.id}/images/{original_id}",
            image_metadata={
                **common,
                "extension": validated.original_extension,
                "mime_type": validated.metadata["original_mime_type"],
                "size_bytes": len(validated.original_data),
                "sha256": validated.metadata["original_sha256"],
            },
        )
        processed = ProductImage(
            id=processed_id,
            product_id=product.id,
            image_type="processed",
            image_url=f"/api/v1/products/{product.id}/images/{processed_id}",
            image_metadata={
                **common,
                **validated.metadata,
                "extension": "jpg",
                "palette": image_palette(validated.data),
                "original_image_id": str(original_id),
            },
        )
        written = []
        try:
            for image, data in [(original, validated.original_data), (processed, validated.data)]:
                key = self.key(user_id, product.id, image)
                self.storage.put(key, data)
                written.append(key)
            product.images.extend([original, processed])
            product.product_features = self.analyzer.analyze(product)
            product.updated_at = datetime.now(UTC)
            self.db.commit()
        except Exception:
            self.db.rollback()
            self.cleanup(written)
            raise
        return self.analyze_visual(product_id, user_id)

    def read_image(self, product_id: uuid.UUID, user_id: uuid.UUID, image_id: uuid.UUID):
        product = self.owned(product_id, user_id)
        image = next((item for item in product.images if item.id == image_id), None)
        if image is None:
            raise ProductNotFound
        try:
            return image, self.storage.read(self.key(user_id, product_id, image))
        except FileNotFoundError as exc:
            raise ProductNotFound from exc

    def delete_image(
        self, product_id: uuid.UUID, user_id: uuid.UUID, image_id: uuid.UUID
    ) -> Product:
        product = self.owned(product_id, user_id, lock=True)
        image = next((item for item in product.images if item.id == image_id), None)
        if image is None:
            raise ProductNotFound
        pair = image.image_metadata["pair_id"]
        related = [item for item in product.images if item.image_metadata["pair_id"] == pair]
        keys = [self.key(user_id, product.id, item) for item in related]
        for item in related:
            product.images.remove(item)
        product.product_features = self.analyzer.analyze(product)
        product.updated_at = datetime.now(UTC)
        self.db.commit()
        self.cleanup(keys)
        return product
