from __future__ import annotations

import uuid

from fastapi import APIRouter

from oneepis_api.schemas.assistant import (
    AssistantChartRequest,
    AssistantChartResponse,
    AssistantSearchRequest,
    AssistantSearchResponse,
    AssistantTimelineResponse,
)
from oneepis_api.services.assistant_timeline import (
    build_assistant_chart,
    build_assistant_timeline,
    search_assistant_timeline,
)

from .patient_shared import PATIENT_ROUTER_OPTIONS, LimitQuery, SessionDep, require_patient

router = APIRouter(**PATIENT_ROUTER_OPTIONS)


@router.get("/{patient_id}/assistant/timeline", response_model=AssistantTimelineResponse)
def get_assistant_timeline(
    patient_id: uuid.UUID,
    session: SessionDep,
    limit: LimitQuery = 100,
) -> AssistantTimelineResponse:
    require_patient(session, patient_id)
    return build_assistant_timeline(session, patient_id, limit=limit)


@router.post("/{patient_id}/assistant/search", response_model=AssistantSearchResponse)
def search_assistant_sources(
    patient_id: uuid.UUID,
    payload: AssistantSearchRequest,
    session: SessionDep,
) -> AssistantSearchResponse:
    require_patient(session, patient_id)
    return search_assistant_timeline(session, patient_id, payload)


@router.post("/{patient_id}/assistant/chart", response_model=AssistantChartResponse)
def get_assistant_chart(
    patient_id: uuid.UUID,
    payload: AssistantChartRequest,
    session: SessionDep,
) -> AssistantChartResponse:
    require_patient(session, patient_id)
    return build_assistant_chart(session, patient_id, payload)
