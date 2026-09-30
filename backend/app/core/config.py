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


@lru_cache
def get_settings() -> Settings:
    return Settings()
