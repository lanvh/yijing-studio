from fastapi import HTTPException
from starlette.responses import JSONResponse

from app.core.config import get_settings


class UploadSizeLimitMiddleware:
    """Bound upload requests before multipart spooling, including chunked requests."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if not (
            scope["type"] == "http"
            and scope["method"] == "POST"
            and scope["path"].startswith(("/api/v1/models/", "/api/v1/products/"))
            and scope["path"].endswith("/images")
        ):
            return await self.app(scope, receive, send)
        limit = get_settings().max_image_size_mb * 1024 * 1024 + 64 * 1024
        headers = dict(scope["headers"])
        try:
            declared_size = int(headers.get(b"content-length", b"0"))
        except ValueError:
            declared_size = limit + 1
        if declared_size > limit:
            response = JSONResponse(status_code=413, content={"detail": "上传请求过大。"})
            return await response(scope, receive, send)
        received = 0

        async def bounded_receive():
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > limit:
                    raise HTTPException(status_code=413, detail="上传请求过大。")
            return message

        return await self.app(scope, bounded_receive, send)
