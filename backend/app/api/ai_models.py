import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Query, Response, UploadFile

from app.api.dependencies import CurrentUser, Db, require_same_origin
from app.core.config import get_settings
from app.repositories.ai_models import ModelRepository
from app.schemas.ai_model import ImageResponse, ModelCreate, ModelPage, ModelResponse, ModelUpdate
from app.services.ai_models import ModelService
from app.storage.local import ImageStorage, get_image_storage

router = APIRouter(prefix="/models", tags=["models"])
Storage = Annotated[ImageStorage, Depends(get_image_storage)]
write = [Depends(require_same_origin)]


@router.get("", response_model=ModelPage)
def list_models(
    user: CurrentUser,
    db: Db,
    response: Response,
    q: str = Query(default="", max_length=100),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=24, ge=1, le=100),
):
    response.headers["Cache-Control"] = "no-store"
    return ModelRepository(db).list(user.id, q.strip(), offset, limit)


@router.post("", response_model=ModelResponse, status_code=201, dependencies=write)
def create_model(payload: ModelCreate, user: CurrentUser, db: Db, storage: Storage):
    return ModelService(db, storage).create(user.id, payload)


@router.get("/options")
def model_options(user: CurrentUser):
    settings = get_settings()
    return {
        "max_image_size_mb": settings.max_image_size_mb,
        "max_image_pixels": settings.max_image_pixels,
        "max_model_images": settings.max_model_images,
        "allowed_image_types": [item.strip() for item in settings.allowed_image_types.split(",")],
    }


@router.get("/{model_id}", response_model=ModelResponse)
def get_model(model_id: uuid.UUID, user: CurrentUser, db: Db, storage: Storage, response: Response):
    response.headers["Cache-Control"] = "no-store"
    return ModelService(db, storage).owned(model_id, user.id)


@router.patch("/{model_id}", response_model=ModelResponse, dependencies=write)
def update_model(
    model_id: uuid.UUID,
    payload: ModelUpdate,
    user: CurrentUser,
    db: Db,
    storage: Storage,
):
    return ModelService(db, storage).update(model_id, user.id, payload)


@router.delete("/{model_id}", status_code=204, dependencies=write)
def delete_model(model_id: uuid.UUID, user: CurrentUser, db: Db, storage: Storage):
    ModelService(db, storage).delete(model_id, user.id)


@router.post(
    "/{model_id}/images", response_model=ImageResponse, status_code=201, dependencies=write
)
def upload_image(
    model_id: uuid.UUID,
    user: CurrentUser,
    db: Db,
    storage: Storage,
    file: Annotated[UploadFile, File()],
    rights_confirmed: Annotated[bool, Form()],
):
    return ModelService(db, storage).upload(model_id, user.id, file, rights_confirmed)


@router.get("/{model_id}/images/{image_id}")
def read_image(
    model_id: uuid.UUID,
    image_id: uuid.UUID,
    user: CurrentUser,
    db: Db,
    storage: Storage,
):
    data = ModelService(db, storage).read_image(model_id, user.id, image_id)
    return Response(
        data,
        media_type="image/jpeg",
        headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"},
    )


@router.delete("/{model_id}/images/{image_id}", status_code=204, dependencies=write)
def delete_image(
    model_id: uuid.UUID,
    image_id: uuid.UUID,
    user: CurrentUser,
    db: Db,
    storage: Storage,
):
    ModelService(db, storage).delete_image(model_id, user.id, image_id)
