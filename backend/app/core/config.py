from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=("../.env", ".env"), extra="ignore")
    app_name: str = "AI Seed Studio"
    app_env: str = "development"
    frontend_url: str = "http://localhost:5173"
    database_url: str
    session_expire_minutes: int = Field(default=1440, ge=1, le=43200)
    cookie_secure: bool = False
    local_storage_path: str = "./storage"
    max_image_size_mb: int = Field(default=15, ge=1, le=50)
    max_image_pixels: int = Field(default=24_000_000, ge=1024, le=50_000_000)
    max_model_images: int = Field(default=8, ge=1, le=20)
    allowed_image_types: str = "image/jpeg,image/png,image/webp"


@lru_cache
def get_settings() -> Settings:
    return Settings()
