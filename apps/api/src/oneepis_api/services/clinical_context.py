from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from oneepis_api.models.clinical_record import ClinicalEvent
from oneepis_api.repositories import patients as patient_repo
from oneepis_api.schemas.patient import PatientRecordSnapshot


@dataclass(frozen=True)
class ClinicalEventContext:
    snapshot: PatientRecordSnapshot
    events: list[ClinicalEvent]


def build_event_context(
    session: Session,
    patient_id: uuid.UUID,
    event_ids: list[uuid.UUID],
) -> ClinicalEventContext:
    patient = patient_repo.get_patient(session, patient_id)
    if patient is None:
        raise ValueError("Patient not found")

    snapshot = PatientRecordSnapshot(
        patient=patient,
        latest_vitals=patient_repo.get_latest_vitals(session, patient_id),
        active_allergies=patient_repo.get_active_allergies(session, patient_id),
        active_medications=patient_repo.get_active_medications(session, patient_id),
        active_problems=patient_repo.get_active_problems(session, patient_id),
        recent_entries=patient_repo.get_recent_entries(session, patient_id),
    )
    events = list(
        session.scalars(
            select(ClinicalEvent).where(
                ClinicalEvent.patient_id == patient_id,
                ClinicalEvent.id.in_(event_ids),
            )
        )
    )
    events.sort(key=lambda item: item.occurred_at)
    return ClinicalEventContext(snapshot=snapshot, events=events)
