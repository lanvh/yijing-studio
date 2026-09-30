import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.api.ai_models import router as models_router
from app.api.auth import router as auth_router
from app.core.config import get_settings
from app.core.database import engine
from app.core.upload_limits import UploadSizeLimitMiddleware
from app.services.ai_models import ModelNotFound
from app.services.image_uploads import UploadRejected

settings = get_settings()
app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Content-Type", "X-Requested-With"],
)
app.include_router(auth_router, prefix="/api/v1")
app.include_router(models_router, prefix="/api/v1")
app.add_middleware(UploadSizeLimitMiddleware)


@app.exception_handler(ModelNotFound)
async def model_not_found(request: Request, exc: ModelNotFound):
    return JSONResponse(status_code=404, content={"detail": "模特或参考图不存在。"})


@app.exception_handler(UploadRejected)
async def upload_rejected(request: Request, exc: UploadRejected):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


@app.exception_handler(OSError)
async def storage_error(request: Request, exc: OSError):
    logging.getLogger(__name__).error("Storage operation failed: %s", type(exc).__name__)
    return JSONResponse(status_code=503, content={"detail": "图片存储暂时不可用，请稍后重试。"})


@app.exception_handler(SQLAlchemyError)
async def database_error(request: Request, exc: SQLAlchemyError):
    logging.getLogger(__name__).error("Database operation failed: %s", type(exc).__name__)
    return JSONResponse(status_code=503, content={"detail": "数据库暂时不可用，请稍后重试。"})


@app.get("/api/v1/health")
def health():
    return {"status": "ok"}


@app.get("/api/v1/health/ready")
def ready():
    # Readiness verifies connectivity AND that explicit migrations have been applied.
    with engine.connect() as connection:
        connection.execute(text("SELECT id FROM users LIMIT 0"))
        connection.execute(text("SELECT token_hash FROM auth_sessions LIMIT 0"))
        connection.execute(text("SELECT id FROM ai_models LIMIT 0"))
        connection.execute(text("SELECT id FROM ai_model_images LIMIT 0"))
    return {"status": "ok", "database": "ready"}
