from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import COOKIE_NAME
from app.schemas.auth import LoginRequest, UserResponse
from app.services.auth import AuthService, InvalidCredentials

router = APIRouter(prefix="/auth", tags=["auth"])
Db = Annotated[Session, Depends(get_db)]


def require_same_origin(request: Request) -> None:
    # A custom header prevents HTML form CSRF. CORS only allows our frontend.
    if request.headers.get("x-requested-with") != "AISeedStudio":
        raise HTTPException(status_code=403, detail="请求校验失败，请刷新页面后重试。")
    origin = request.headers.get("origin")
    if origin and origin != get_settings().frontend_url:
        raise HTTPException(status_code=403, detail="请求来源不受信任。")


@router.post("/login", response_model=UserResponse, dependencies=[Depends(require_same_origin)])
def login(payload: LoginRequest, request: Request, response: Response, db: Db):
    try:
        user, token = AuthService(db).login(
            str(payload.email), payload.password, request.cookies.get(COOKIE_NAME)
        )
    except InvalidCredentials:
        raise HTTPException(status_code=401, detail="邮箱或密码错误，或账号已停用。") from None
    settings = get_settings()
    response.set_cookie(
        COOKIE_NAME,
        token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="strict",
        max_age=settings.session_expire_minutes * 60,
        path="/api",
    )
    response.headers["Cache-Control"] = "no-store"
    return user


@router.get("/me", response_model=UserResponse)
def me(request: Request, response: Response, db: Db):
    user = AuthService(db).current_user(request.cookies.get(COOKIE_NAME))
    if not user:
        raise HTTPException(status_code=401, detail="登录已失效，请重新登录。")
    response.headers["Cache-Control"] = "no-store"
    return user


@router.post("/logout", status_code=204, dependencies=[Depends(require_same_origin)])
def logout(request: Request, db: Db):
    AuthService(db).logout(request.cookies.get(COOKIE_NAME))
    response = Response(status_code=204)
    response.delete_cookie(
        COOKIE_NAME,
        path="/api",
        httponly=True,
        secure=get_settings().cookie_secure,
        samesite="strict",
    )
    response.headers["Cache-Control"] = "no-store"
    return response
