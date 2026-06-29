from __future__ import annotations

import uuid

from fastapi import APIRouter
from sqlalchemy import select

from oneepis_api.models.clinical_record import ClinicalEvent, Medication, RecordStatus, VitalSign
from oneepis_api.schemas.clinical_record import (
    AssistantCorrelationRequest,
    AssistantCorrelationResponse,
)

from .patient_assistant_common import ASSISTANT_CORRELATION_PRESETS
from .patient_assistant_correlation_rules import (
    correlate_preset,
    correlation_missing_data,
    correlation_warnings,
)
from .patient_assistant_labs import fetch_lab_results_for_assistant
from .patient_shared import SessionDep, require_patient

router = APIRouter()


@router.post("/{patient_id}/assistant/correlate", response_model=AssistantCorrelationResponse)
def correlate_assistant_read_layer(
    patient_id: uuid.UUID,
    payload: AssistantCorrelationRequest,
    session: SessionDep,
) -> AssistantCorrelationResponse:
    require_patient(session, patient_id)
    query_limit = payload.limit + 1
    vitals = list(
        session.scalars(
            select(VitalSign)
            .where(
                VitalSign.patient_id == patient_id,
                VitalSign.status != RecordStatus.ENTERED_IN_ERROR,
            )
            .order_by(VitalSign.measured_at.desc())
            .limit(query_limit)
        )
    )
    events = list(
        session.scalars(
            select(ClinicalEvent)
            .where(ClinicalEvent.patient_id == patient_id)
            .order_by(ClinicalEvent.occurred_at.desc())
            .limit(query_limit)
        )
    )
    lab_results = fetch_lab_results_for_assistant(session, patient_id, query_limit)
    medications = list(
        session.scalars(
            select(Medication)
            .where(Medication.patient_id == patient_id, Medication.status == RecordStatus.ACTIVE)
            .order_by(Medication.created_at.desc())
            .limit(query_limit)
        )
    )
    selected = payload.presets or list(ASSISTANT_CORRELATION_PRESETS)
    correlations = [
        correlate_preset(
            preset=preset,
            patient_id=patient_id,
            vitals=vitals[: payload.limit],
            events=events[: payload.limit],
            lab_results=lab_results[: payload.limit],
            medications=medications[: payload.limit],
        )
        for preset in selected
    ]
    has_more = (
        len(vitals) > payload.limit
        or len(events) > payload.limit
        or len(lab_results) > payload.limit
        or len(medications) > payload.limit
    )
    return AssistantCorrelationResponse(
        patient_id=patient_id,
        correlations=correlations,
        missing_data=correlation_missing_data(
            vitals=vitals,
            events=events,
            lab_results=lab_results,
            medications=medications,
        ),
        warnings=correlation_warnings(has_more=has_more, limit=payload.limit),
        limit=payload.limit,
        has_more=has_more,
    )
