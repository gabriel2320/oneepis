from __future__ import annotations

import uuid

from fastapi import APIRouter
from sqlalchemy import select

from oneepis_api.api.deps import ReadAccessDep
from oneepis_api.models.clinical_record import (
    ActiveProblem,
    Allergy,
    ClinicalEncounter,
    ClinicalEntry,
    ClinicalEntryStatus,
    ClinicalEvent,
    Medication,
    RecordStatus,
    VitalSign,
)
from oneepis_api.schemas.clinical_record import AssistantTimelineResponse
from oneepis_api.services.historical_diagnoses import historical_diagnoses_from_events

from .patient_assistant_lab_timeline import fetch_lab_results_for_timeline, lab_timeline_items
from .patient_assistant_scope import enforce_and_record_assistant_read
from .patient_assistant_timeline_items import (
    allergy_items,
    encounter_items,
    entry_items,
    event_items,
    historical_diagnosis_items,
    medication_items,
    problem_items,
    timeline_missing_data,
    timeline_warnings,
    vital_items,
)
from .patient_shared import LimitQuery, SessionDep, SettingsDep, require_patient

router = APIRouter()


@router.get("/{patient_id}/assistant/timeline", response_model=AssistantTimelineResponse)
def get_assistant_timeline(
    patient_id: uuid.UUID,
    session: SessionDep,
    user: ReadAccessDep,
    settings: SettingsDep,
    limit: LimitQuery = 50,
) -> AssistantTimelineResponse:
    require_patient(session, patient_id)
    enforce_and_record_assistant_read(
        session,
        patient_id=patient_id,
        user=user,
        settings=settings,
        action="assistant_timeline.read",
    )
    query_limit = limit + 1
    encounters = _recent(
        session,
        ClinicalEncounter,
        patient_id,
        ClinicalEncounter.started_at,
        query_limit,
    )
    entries = _recent(session, ClinicalEntry, patient_id, ClinicalEntry.occurred_at, query_limit)
    events = _recent(session, ClinicalEvent, patient_id, ClinicalEvent.occurred_at, query_limit)
    vitals = _recent(session, VitalSign, patient_id, VitalSign.measured_at, query_limit)
    medications = list(
        session.scalars(
            select(Medication)
            .where(Medication.patient_id == patient_id, Medication.status == RecordStatus.ACTIVE)
            .order_by(Medication.created_at.desc())
            .limit(query_limit)
        )
    )
    problems = list(
        session.scalars(
            select(ActiveProblem)
            .where(
                ActiveProblem.patient_id == patient_id,
                ActiveProblem.status == RecordStatus.ACTIVE,
            )
            .order_by(ActiveProblem.created_at.desc())
            .limit(query_limit)
        )
    )
    allergies = list(
        session.scalars(
            select(Allergy)
            .where(Allergy.patient_id == patient_id, Allergy.status == RecordStatus.ACTIVE)
            .order_by(Allergy.recorded_at.desc())
            .limit(query_limit)
        )
    )
    lab_results = fetch_lab_results_for_timeline(session, patient_id, query_limit)
    historical_diagnoses = historical_diagnoses_from_events(events)
    historical_event_ids = {diagnosis.source_event_id for diagnosis in historical_diagnoses}
    historical_events_by_id = {
        event.id: event for event in events if event.id in historical_event_ids
    }
    timeline_events = [event for event in events if event.id not in historical_event_ids]
    items = [
        *encounter_items(patient_id, encounters),
        *entry_items(patient_id, entries),
        *event_items(patient_id, timeline_events),
        *historical_diagnosis_items(patient_id, historical_diagnoses, historical_events_by_id),
        *vital_items(patient_id, vitals),
        *medication_items(patient_id, medications),
        *problem_items(patient_id, problems),
        *allergy_items(patient_id, allergies),
        *lab_timeline_items(patient_id, lab_results),
    ]
    items.sort(key=lambda item: item.occurred_at, reverse=True)
    has_more = len(items) > limit or any(
        len(domain_items) > limit
        for domain_items in (
            encounters,
            entries,
            events,
            vitals,
            medications,
            problems,
            allergies,
            lab_results,
        )
    )
    return AssistantTimelineResponse(
        patient_id=patient_id,
        items=items[:limit],
        missing_data=timeline_missing_data(
            encounters=encounters,
            entries=entries,
            events=events,
            vitals=vitals,
            medications=medications,
            problems=problems,
            allergies=allergies,
        ),
        warnings=timeline_warnings(has_more=has_more, limit=limit),
        limit=limit,
        has_more=has_more,
    )


def _recent(session, model, patient_id: uuid.UUID, order_column, limit: int):
    statement = select(model).where(model.patient_id == patient_id)
    if model is ClinicalEntry:
        statement = statement.where(ClinicalEntry.status != ClinicalEntryStatus.ENTERED_IN_ERROR)
    if model is VitalSign:
        statement = statement.where(VitalSign.status != RecordStatus.ENTERED_IN_ERROR)
    return list(
        session.scalars(
            statement.order_by(order_column.desc()).limit(limit)
        )
    )
