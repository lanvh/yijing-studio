from fastapi import APIRouter, Response

from app.api.dependencies import CurrentUser
from app.core.config import get_settings
from app.providers.openai_http import ExternalServiceError, official_base
from app.providers.seedream import official_base as ark_base
from app.services.images import ImageService

router = APIRouter(prefix="/providers", tags=["providers"])


@router.get("")
async def provider_status(user: CurrentUser, response: Response):
    response.headers["Cache-Control"] = "no-store"
    settings = get_settings()
    health = await ImageService().health_check()
    mode = settings.llm_provider or "local"
    copy_available = mode in ("local", "mock") or (
        mode in {"openai", "ark"}
        and bool(
            settings.llm_api_key.get_secret_value() or settings.image_api_key.get_secret_value()
        )
    )
    try:
        if mode in {"openai", "ark"}:
            (ark_base if mode == "ark" else official_base)(settings.llm_api_base_url)
    except ExternalServiceError:
        copy_available = False
    return {
        **health.model_dump(),
        "copy_mode": mode,
        "copy_available": copy_available,
        "configuration_only": not health.mock,
    }
