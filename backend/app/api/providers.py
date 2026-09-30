from fastapi import APIRouter, Response

from app.api.dependencies import CurrentUser
from app.providers.contracts import ProviderHealth
from app.services.images import ImageService

router = APIRouter(prefix="/providers", tags=["providers"])


@router.get("", response_model=ProviderHealth)
async def provider_status(user: CurrentUser, response: Response):
    response.headers["Cache-Control"] = "no-store"
    return await ImageService().health_check()
