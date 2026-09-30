from typing import Annotated

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import COOKIE_NAME
from app.models.user import User
from app.services.auth import AuthService

Db = Annotated[Session, Depends(get_db)]


def require_same_origin(request: Request) -> None:
    if request.headers.get("x-requested-with") != "AISeedStudio":
        raise HTTPException(status_code=403, detail="请求校验失败，请刷新页面后重试。")
    origin = request.headers.get("origin")
    if origin and origin != get_settings().frontend_url:
        raise HTTPException(status_code=403, detail="请求来源不受信任。")


def current_user(request: Request, db: Db) -> User:
    user = AuthService(db).current_user(request.cookies.get(COOKIE_NAME))
    if not user:
        raise HTTPException(status_code=401, detail="登录已失效，请重新登录。")
    return user


CurrentUser = Annotated[User, Depends(current_user)]
