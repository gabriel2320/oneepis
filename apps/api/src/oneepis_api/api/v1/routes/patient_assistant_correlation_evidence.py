from __future__ import annotations

import uuid

from oneepis_api.models.clinical_record import ClinicalEvent, Medication
from oneepis_api.models.vital_sign import VitalSign
from oneepis_api.schemas.clinical_record import AssistantCorrelationEvidence

from .patient_assistant_common import (
    clinical_event_source_path,
    date_or_created_at,
    medication_summary,
    vital_summary,
)


def vital_evidence(
    patient_id: uuid.UUID,
    vitals: list[VitalSign],
    *,
    label: str,
) -> list[AssistantCorrelationEvidence]:
    return [
        AssistantCorrelationEvidence(
            source_type="vital_sign",
            source_id=vital.id,
            occurred_at=vital.measured_at,
            label=label,
            summary=vital_summary(vital),
            source_path=f"/api/v1/patients/{patient_id}/vital-signs/{vital.id}",
        )
        for vital in vitals
    ]


def event_evidence(
    patient_id: uuid.UUID,
    events: list[ClinicalEvent],
    *,
    label: str,
) -> list[AssistantCorrelationEvidence]:
    return [
        AssistantCorrelationEvidence(
            source_type="clinical_event",
            source_id=event.id,
            occurred_at=event.occurred_at,
            label=label,
            summary=event.summary,
            source_path=clinical_event_source_path(patient_id, event.id),
        )
        for event in events
    ]


def medication_evidence(
    patient_id: uuid.UUID,
    medications: list[Medication],
    *,
    label: str,
) -> list[AssistantCorrelationEvidence]:
    return [
        AssistantCorrelationEvidence(
            source_type="medication",
            source_id=medication.id,
            occurred_at=date_or_created_at(medication.started_on, medication.created_at),
            label=label,
            summary=f"{medication.name}: {medication_summary(medication)}",
            source_path=f"/api/v1/patients/{patient_id}/medications/{medication.id}",
        )
        for medication in medications
    ]
