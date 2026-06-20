from typing import Annotated

from fastapi import APIRouter, Depends

from oneepis_api.core.config import Settings, get_settings
from oneepis_api.schemas.health import HealthCheck

router = APIRouter(tags=["health"])
SettingsDep = Annotated[Settings, Depends(get_settings)]


@router.get("/health", response_model=HealthCheck)
def health(settings: SettingsDep) -> HealthCheck:
    return HealthCheck(
        status="ok",
        service=settings.app_name,
        environment=settings.environment,
    )
