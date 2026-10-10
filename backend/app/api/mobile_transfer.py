import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Response

from app.api.dependencies import CurrentUser, Db, require_same_origin
from app.services.mobile_transfer import MobileTransfer
from app.storage.local import ImageStorage, get_image_storage

router = APIRouter(tags=["mobile-publish"])
Storage = Annotated[ImageStorage, Depends(get_image_storage)]
Token = Annotated[str | None, Header(alias="X-Mobile-Token", max_length=100)]


def private(response: Response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["Referrer-Policy"] = "no-referrer"


@router.post(
    "/generation/tasks/{task_id}/mobile-transfer",
    dependencies=[Depends(require_same_origin), Depends(private)],
)
def create(task_id: uuid.UUID, user: CurrentUser, db: Db, storage: Storage):
    return MobileTransfer(db, storage).create(task_id, user.id)


@router.delete(
    "/generation/tasks/{task_id}/mobile-transfer",
    status_code=204,
    dependencies=[Depends(require_same_origin)],
)
def revoke(task_id: uuid.UUID, user: CurrentUser, db: Db, storage: Storage):
    MobileTransfer(db, storage).revoke(task_id, user.id)


@router.get("/mobile-publish/{task_id}", dependencies=[Depends(private)])
def content(task_id: uuid.UUID, db: Db, storage: Storage, token: Token = None):
    return MobileTransfer(db, storage).content(task_id, token)


@router.get("/mobile-publish/{task_id}/images/{image_id}")
def image(task_id: uuid.UUID, image_id: uuid.UUID, db: Db, storage: Storage, token: Token = None):
    data, mime = MobileTransfer(db, storage).image(task_id, image_id, token)
    return Response(
        data,
        media_type=mime,
        headers={
            "Cache-Control": "no-store",
            "Referrer-Policy": "no-referrer",
            "X-Content-Type-Options": "nosniff",
        },
    )
