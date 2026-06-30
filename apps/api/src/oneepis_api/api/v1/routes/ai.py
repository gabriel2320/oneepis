from typing import Annotated

from fastapi import APIRouter, Depends

from oneepis_api.api.deps import AiAccessDep
from oneepis_api.core.config import Settings, get_settings
from oneepis_api.schemas.ai import AIProviderStatus, ClinicalInsightRequest, ClinicalInsightResponse
from oneepis_api.services.ai.provider import get_ai_provider

router = APIRouter(prefix="/ai", tags=["ai"])
SettingsDep = Annotated[Settings, Depends(get_settings)]


@router.post("/clinical-insights", response_model=ClinicalInsightResponse)
def create_clinical_insight(
    payload: ClinicalInsightRequest,
    settings: SettingsDep,
    _user: AiAccessDep,
) -> ClinicalInsightResponse:
    provider = get_ai_provider(settings)
    return provider.create_insight(payload)


@router.get("/status", response_model=AIProviderStatus)
def get_ai_status(settings: SettingsDep, _user: AiAccessDep) -> AIProviderStatus:
    provider = get_ai_provider(settings)
    status = provider.status()
    if settings.environment.strip().lower() != "development":
        return status.model_copy(update={"base_url": None})
    return status
