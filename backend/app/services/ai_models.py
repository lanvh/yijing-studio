import logging
import uuid
from datetime import UTC, datetime

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.ai_model import AIModel, AIModelImage
from app.repositories.ai_models import ModelRepository
from app.schemas.ai_model import ModelCreate, ModelUpdate
from app.services.image_uploads import UploadRejected, validate_reference
from app.services.moderation import ReferenceUploadPolicy
from app.storage.local import ImageStorage

logger = logging.getLogger(__name__)


class ModelNotFound(Exception):
    pass


class ModelService:
    def __init__(self, db: Session, storage: ImageStorage):
        self.db = db
        self.storage = storage
        self.models = ModelRepository(db)

    def owned(self, model_id: uuid.UUID, user_id: uuid.UUID, *, lock=False) -> AIModel:
        model = self.models.owned(model_id, user_id, lock=lock)
        if model is None:
            raise ModelNotFound
        return model

    def create(self, user_id: uuid.UUID, payload: ModelCreate) -> AIModel:
        model = AIModel(user_id=user_id, reference_images=[], **payload.model_dump())
        self.db.add(model)
        self.db.commit()
        return model

    def update(self, model_id: uuid.UUID, user_id: uuid.UUID, payload: ModelUpdate) -> AIModel:
        model = self.owned(model_id, user_id, lock=True)
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(model, key, value)
        model.updated_at = datetime.now(UTC)
        self.db.commit()
        return model

    @staticmethod
    def key(user_id: uuid.UUID, model_id: uuid.UUID, image_id: uuid.UUID) -> str:
        return f"models/{user_id}/{model_id}/{image_id}.jpg"

    def cleanup(self, keys: list[str]) -> None:
        for key in keys:
            try:
                self.storage.delete(key)
            except OSError:
                # DB ownership is removed first; a retained orphan is never publicly accessible.
                logger.exception("Could not clean up private image: %s", key)

    def delete(self, model_id: uuid.UUID, user_id: uuid.UUID) -> None:
        model = self.owned(model_id, user_id, lock=True)
        keys = [self.key(user_id, model.id, image.id) for image in model.reference_images]
        self.db.delete(model)
        self.db.commit()
        self.cleanup(keys)

    def upload(
        self, model_id: uuid.UUID, user_id: uuid.UUID, upload: UploadFile, rights_confirmed: bool
    ) -> AIModelImage:
        model = self.owned(model_id, user_id, lock=True)
        declaration = ReferenceUploadPolicy().review(rights_confirmed)
        if len(model.reference_images) >= get_settings().max_model_images:
            raise UploadRejected("参考图数量已达上限，请先移除不需要的图片。", 409)
        validated = validate_reference(upload)
        image_id = uuid.uuid4()
        key = self.key(user_id, model.id, image_id)
        image = AIModelImage(
            id=image_id,
            model_id=model.id,
            image_url=f"/api/v1/models/{model.id}/images/{image_id}",
            image_metadata={**validated.metadata, **declaration},
        )
        self.storage.put(key, validated.data)
        try:
            self.db.add(image)
            model.updated_at = datetime.now(UTC)
            self.db.commit()
        except Exception:
            self.db.rollback()
            self.cleanup([key])
            raise
        return image

    def find_image(
        self, model_id: uuid.UUID, user_id: uuid.UUID, image_id: uuid.UUID, *, lock=False
    ) -> AIModelImage:
        model = self.owned(model_id, user_id, lock=lock)
        image = next((item for item in model.reference_images if item.id == image_id), None)
        if image is None:
            raise ModelNotFound
        return image

    def read_image(self, model_id: uuid.UUID, user_id: uuid.UUID, image_id: uuid.UUID) -> bytes:
        self.find_image(model_id, user_id, image_id)
        try:
            return self.storage.read(self.key(user_id, model_id, image_id))
        except FileNotFoundError as exc:
            raise ModelNotFound from exc

    def delete_image(self, model_id: uuid.UUID, user_id: uuid.UUID, image_id: uuid.UUID) -> None:
        model = self.owned(model_id, user_id, lock=True)
        image = next((item for item in model.reference_images if item.id == image_id), None)
        if image is None:
            raise ModelNotFound
        model.reference_images.remove(image)
        model.updated_at = datetime.now(UTC)
        self.db.commit()
        self.cleanup([self.key(user_id, model_id, image_id)])
