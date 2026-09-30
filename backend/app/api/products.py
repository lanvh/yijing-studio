import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Query, Response, UploadFile

from app.api.dependencies import CurrentUser, Db, require_same_origin
from app.core.config import get_settings
from app.repositories.products import ProductRepository
from app.schemas.product import (
    CATEGORIES,
    Category,
    ProductCreate,
    ProductPage,
    ProductResponse,
    ProductUpdate,
)
from app.services.products import ProductService
from app.storage.local import ImageStorage, get_image_storage

router = APIRouter(prefix="/products", tags=["products"])
Storage = Annotated[ImageStorage, Depends(get_image_storage)]
write = [Depends(require_same_origin)]


@router.get("", response_model=ProductPage)
def list_products(
    user: CurrentUser,
    db: Db,
    response: Response,
    q: str = Query(default="", max_length=100),
    category: Category | None = None,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=24, ge=1, le=100),
):
    response.headers["Cache-Control"] = "no-store"
    return ProductRepository(db).list(user.id, q.strip(), category, offset, limit)


@router.get("/options")
def product_options(user: CurrentUser):
    settings = get_settings()
    return {
        "categories": CATEGORIES,
        "max_image_size_mb": settings.max_image_size_mb,
        "max_product_images": settings.max_product_images,
    }


@router.post("", response_model=ProductResponse, status_code=201, dependencies=write)
def create_product(payload: ProductCreate, user: CurrentUser, db: Db, storage: Storage):
    return ProductService(db, storage).create(user.id, payload)


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: uuid.UUID, user: CurrentUser, db: Db, storage: Storage, response: Response
):
    response.headers["Cache-Control"] = "no-store"
    return ProductService(db, storage).owned(product_id, user.id)


@router.patch("/{product_id}", response_model=ProductResponse, dependencies=write)
def update_product(
    product_id: uuid.UUID, payload: ProductUpdate, user: CurrentUser, db: Db, storage: Storage
):
    return ProductService(db, storage).update(product_id, user.id, payload)


@router.delete("/{product_id}", status_code=204, dependencies=write)
def delete_product(product_id: uuid.UUID, user: CurrentUser, db: Db, storage: Storage):
    ProductService(db, storage).delete(product_id, user.id)


@router.post("/{product_id}/analyze", response_model=ProductResponse, dependencies=write)
def analyze_product(product_id: uuid.UUID, user: CurrentUser, db: Db, storage: Storage):
    return ProductService(db, storage).analyze(product_id, user.id)


@router.post(
    "/{product_id}/images", response_model=ProductResponse, status_code=201, dependencies=write
)
def upload_image(
    product_id: uuid.UUID,
    user: CurrentUser,
    db: Db,
    storage: Storage,
    file: Annotated[UploadFile, File()],
    rights_confirmed: Annotated[bool, Form()],
):
    return ProductService(db, storage).upload(product_id, user.id, file, rights_confirmed)


@router.get("/{product_id}/images/{image_id}")
def read_image(
    product_id: uuid.UUID, image_id: uuid.UUID, user: CurrentUser, db: Db, storage: Storage
):
    image, data = ProductService(db, storage).read_image(product_id, user.id, image_id)
    headers = {"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"}
    if image.image_type == "original":
        headers["Content-Disposition"] = (
            f'attachment; filename="{image.id}.{image.image_metadata["extension"]}"'
        )
    return Response(data, media_type=image.image_metadata["mime_type"], headers=headers)


@router.delete(
    "/{product_id}/images/{image_id}", response_model=ProductResponse, dependencies=write
)
def delete_image(
    product_id: uuid.UUID, image_id: uuid.UUID, user: CurrentUser, db: Db, storage: Storage
):
    return ProductService(db, storage).delete_image(product_id, user.id, image_id)
