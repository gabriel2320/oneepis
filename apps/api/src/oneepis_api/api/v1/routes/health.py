from typing import Annotated

from fastapi import APIRouter, Depends

from oneepis_api.core.config import Settings, get_settings
from oneepis_api.schemas.health import HealthCheck
from oneepis_api.services.audit import get_audit_request_context

router = APIRouter(tags=["health"])
SettingsDep = Annotated[Settings, Depends(get_settings)]


@router.get("/health", response_model=HealthCheck)
def health(settings: SettingsDep) -> HealthCheck:
    request_context = get_audit_request_context()
    return HealthCheck(
        status="ok",
        service=settings.app_name,
        environment=settings.environment,
        correlation_id=request_context.correlation_id if request_context else None,
    )
