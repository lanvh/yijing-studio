import uuid
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query, Response

from app.api.dependencies import CurrentUser, Db, require_same_origin
from app.schemas.generation import (
    POSES,
    SCENES,
    STYLES,
    CopyEdit,
    CopyResponse,
    ResultEdit,
    ResultResponse,
    TaskCreate,
    TaskPage,
    TaskResponse,
)
from app.services.generation import GenerationError, GenerationService
from app.storage.local import ImageStorage, get_image_storage


def private_response(response: Response):
    response.headers["Cache-Control"] = "no-store"


router = APIRouter(
    prefix="/generation", tags=["generation"], dependencies=[Depends(private_response)]
)
Storage = Annotated[ImageStorage, Depends(get_image_storage)]
write = [Depends(require_same_origin)]


@router.get("/options")
def options(user: CurrentUser):
    return {"scenes": SCENES, "styles": STYLES, "poses": POSES, "counts": [1, 2, 4, 6]}


@router.get("/tasks", response_model=TaskPage)
def tasks(
    user: CurrentUser,
    db: Db,
    storage: Storage,
    response: Response,
    offset: int = Query(0, ge=0),
    limit: int = Query(24, ge=1, le=100),
    status: Literal["PENDING", "PROCESSING", "SUCCEEDED", "PARTIAL", "FAILED"] | None = None,
):
    response.headers["Cache-Control"] = "no-store"
    return GenerationService(db, storage).list(user.id, offset, limit, status)


@router.post("/tasks", response_model=TaskResponse, status_code=201, dependencies=write)
def create(payload: TaskCreate, user: CurrentUser, db: Db, storage: Storage):
    return GenerationService(db, storage).create(user.id, payload)


@router.get("/tasks/{task_id}", response_model=TaskResponse)
def detail(task_id: uuid.UUID, user: CurrentUser, db: Db, storage: Storage, response: Response):
    response.headers["Cache-Control"] = "no-store"
    return GenerationService(db, storage).owned(task_id, user.id)


@router.delete("/tasks/{task_id}", status_code=204, dependencies=write)
def delete(task_id: uuid.UUID, user: CurrentUser, db: Db, storage: Storage):
    GenerationService(db, storage).delete(task_id, user.id)


@router.post("/tasks/{task_id}/retry", response_model=TaskResponse, dependencies=write)
def retry(task_id: uuid.UUID, user: CurrentUser, db: Db, storage: Storage):
    return GenerationService(db, storage).run(task_id, user.id)


@router.get("/tasks/{task_id}/results", response_model=list[ResultResponse])
def results(task_id: uuid.UUID, user: CurrentUser, db: Db, storage: Storage):
    return GenerationService(db, storage).owned(task_id, user.id).results


@router.patch("/results/{result_id}", response_model=ResultResponse, dependencies=write)
def select_result(
    result_id: uuid.UUID, payload: ResultEdit, user: CurrentUser, db: Db, storage: Storage
):
    return GenerationService(db, storage).select_result(result_id, user.id, payload.is_selected)


@router.delete("/results/{result_id}", status_code=204, dependencies=write)
def delete_result(result_id: uuid.UUID, user: CurrentUser, db: Db, storage: Storage):
    GenerationService(db, storage).delete_result(result_id, user.id)


@router.get("/results/{result_id}/image")
def image(result_id: uuid.UUID, user: CurrentUser, db: Db, storage: Storage):
    _, result = GenerationService(db, storage).result(result_id, user.id)
    try:
        data = storage.read(result.storage_key)
    except FileNotFoundError as exc:
        raise GenerationError("图片文件不存在。", 404) from exc
    return Response(
        data,
        media_type=result.result_metadata["media_type"],
        headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"},
    )


@router.get("/tasks/{task_id}/copy", response_model=CopyResponse | None)
def read_copy(task_id: uuid.UUID, user: CurrentUser, db: Db, storage: Storage):
    return GenerationService(db, storage).owned(task_id, user.id).copy


@router.post("/tasks/{task_id}/copy", response_model=CopyResponse, dependencies=write)
def regenerate_copy(task_id: uuid.UUID, user: CurrentUser, db: Db, storage: Storage):
    return GenerationService(db, storage).write_copy(task_id, user.id)


@router.patch("/tasks/{task_id}/copy", response_model=CopyResponse, dependencies=write)
def edit_copy(task_id: uuid.UUID, payload: CopyEdit, user: CurrentUser, db: Db, storage: Storage):
    return GenerationService(db, storage).write_copy(task_id, user.id, payload)


@router.get("/tasks/{task_id}/export")
def download(task_id: uuid.UUID, user: CurrentUser, db: Db, storage: Storage):
    data = GenerationService(db, storage).export(task_id, user.id)
    return Response(
        data,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="ai-seed-{task_id}.zip"',
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.post("/tasks/{task_id}/export", dependencies=write)
def export(task_id: uuid.UUID, user: CurrentUser, db: Db, storage: Storage):
    return download(task_id, user, db, storage)
