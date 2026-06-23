from __future__ import annotations

import uuid
from datetime import date, datetime, time

from fastapi import APIRouter
from sqlalchemy import select

from oneepis_api.models.clinical_record import (
    ActiveProblem,
    Allergy,
    ClinicalEncounter,
    ClinicalEntry,
    ClinicalEvent,
    Medication,
    RecordStatus,
    VitalSign,
)
from oneepis_api.schemas.clinical_record import AssistantTimelineItem, AssistantTimelineResponse

from .patient_shared import PATIENT_ROUTER_OPTIONS, LimitQuery, SessionDep, require_patient

router = APIRouter(**PATIENT_ROUTER_OPTIONS)


@router.get("/{patient_id}/assistant/timeline", response_model=AssistantTimelineResponse)
def get_assistant_timeline(
    patient_id: uuid.UUID,
    session: SessionDep,
    limit: LimitQuery = 50,
) -> AssistantTimelineResponse:
    require_patient(session, patient_id)
    query_limit = limit + 1
    encounters = list(
        session.scalars(
            select(ClinicalEncounter)
            .where(ClinicalEncounter.patient_id == patient_id)
            .order_by(ClinicalEncounter.started_at.desc())
            .limit(query_limit)
        )
    )
    entries = list(
        session.scalars(
            select(ClinicalEntry)
            .where(ClinicalEntry.patient_id == patient_id)
            .order_by(ClinicalEntry.occurred_at.desc())
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
    vitals = list(
        session.scalars(
            select(VitalSign)
            .where(VitalSign.patient_id == patient_id)
            .order_by(VitalSign.measured_at.desc())
            .limit(query_limit)
        )
    )
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
    items = [
        *_encounter_items(patient_id, encounters),
        *_entry_items(patient_id, entries),
        *_event_items(patient_id, events),
        *_vital_items(patient_id, vitals),
        *_medication_items(patient_id, medications),
        *_problem_items(patient_id, problems),
        *_allergy_items(patient_id, allergies),
    ]
    items.sort(key=lambda item: item.occurred_at, reverse=True)
    has_more = len(items) > limit or any(
        len(domain_items) > limit
        for domain_items in (encounters, entries, events, vitals, medications, problems, allergies)
    )
    return AssistantTimelineResponse(
        patient_id=patient_id,
        items=items[:limit],
        missing_data=_missing_data(
            encounters=encounters,
            entries=entries,
            events=events,
            vitals=vitals,
            medications=medications,
            problems=problems,
            allergies=allergies,
        ),
        warnings=_warnings(has_more=has_more, limit=limit),
        limit=limit,
        has_more=has_more,
    )


def _encounter_items(
    patient_id: uuid.UUID,
    encounters: list[ClinicalEncounter],
) -> list[AssistantTimelineItem]:
    return [
        AssistantTimelineItem(
            item_type="encounter",
            item_id=encounter.id,
            occurred_at=encounter.started_at,
            label="Encuentro clinico",
            summary=f"{encounter.reason} ({encounter.type.value}, {encounter.status.value})",
            source_label="encounters",
            source_path=f"/api/v1/patients/{patient_id}/encounters/{encounter.id}",
        )
        for encounter in encounters
    ]


def _entry_items(
    patient_id: uuid.UUID,
    entries: list[ClinicalEntry],
) -> list[AssistantTimelineItem]:
    return [
        AssistantTimelineItem(
            item_type="clinical_entry",
            item_id=entry.id,
            occurred_at=entry.occurred_at,
            label=entry.title,
            summary=_truncate(" / ".join(_entry_sections(entry)) or entry.kind.value),
            source_label="clinical_entries",
            source_path=f"/api/v1/patients/{patient_id}/clinical-entries/{entry.id}",
        )
        for entry in entries
    ]


def _event_items(
    patient_id: uuid.UUID,
    events: list[ClinicalEvent],
) -> list[AssistantTimelineItem]:
    return [
        AssistantTimelineItem(
            item_type="clinical_event",
            item_id=event.id,
            occurred_at=event.occurred_at,
            label=event.event_type.value,
            summary=event.summary,
            source_label="clinical_events",
            source_path=f"/api/v1/patients/{patient_id}/clinical-events",
        )
        for event in events
    ]


def _vital_items(
    patient_id: uuid.UUID,
    vitals: list[VitalSign],
) -> list[AssistantTimelineItem]:
    return [
        AssistantTimelineItem(
            item_type="vital_sign",
            item_id=vital.id,
            occurred_at=vital.measured_at,
            label="Signos vitales",
            summary=_vital_summary(vital),
            source_label="vital_signs",
            source_path=f"/api/v1/patients/{patient_id}/vital-signs/{vital.id}",
        )
        for vital in vitals
    ]


def _medication_items(
    patient_id: uuid.UUID,
    medications: list[Medication],
) -> list[AssistantTimelineItem]:
    return [
        AssistantTimelineItem(
            item_type="medication",
            item_id=medication.id,
            occurred_at=_date_or_created_at(medication.started_on, medication.created_at),
            label=medication.name,
            summary=_medication_summary(medication),
            source_label="medications",
            source_path=f"/api/v1/patients/{patient_id}/medications/{medication.id}",
        )
        for medication in medications
    ]


def _problem_items(
    patient_id: uuid.UUID,
    problems: list[ActiveProblem],
) -> list[AssistantTimelineItem]:
    return [
        AssistantTimelineItem(
            item_type="problem",
            item_id=problem.id,
            occurred_at=_date_or_created_at(problem.onset_date, problem.created_at),
            label=problem.title,
            summary=_truncate(problem.notes or problem.code or problem.status.value),
            source_label="problems",
            source_path=f"/api/v1/patients/{patient_id}/problems/{problem.id}",
        )
        for problem in problems
    ]


def _allergy_items(
    patient_id: uuid.UUID,
    allergies: list[Allergy],
) -> list[AssistantTimelineItem]:
    return [
        AssistantTimelineItem(
            item_type="allergy",
            item_id=allergy.id,
            occurred_at=allergy.recorded_at,
            label=allergy.substance,
            summary=_truncate(allergy.reaction or allergy.severity.value),
            source_label="allergies",
            source_path=f"/api/v1/patients/{patient_id}/allergies/{allergy.id}",
        )
        for allergy in allergies
    ]


def _entry_sections(entry: ClinicalEntry) -> list[str]:
    return [
        text
        for text in (entry.subjective, entry.objective, entry.assessment, entry.plan)
        if text
    ]


def _vital_summary(vital: VitalSign) -> str:
    values = []
    if vital.temperature_c is not None:
        values.append(f"T {vital.temperature_c} C")
    if vital.systolic_bp is not None and vital.diastolic_bp is not None:
        values.append(f"PA {vital.systolic_bp}/{vital.diastolic_bp}")
    if vital.heart_rate_bpm is not None:
        values.append(f"FC {vital.heart_rate_bpm}")
    if vital.respiratory_rate_bpm is not None:
        values.append(f"FR {vital.respiratory_rate_bpm}")
    if vital.oxygen_saturation_pct is not None:
        values.append(f"SatO2 {vital.oxygen_saturation_pct}%")
    return _truncate(", ".join(values) or vital.notes or "Signos vitales registrados")


def _medication_summary(medication: Medication) -> str:
    values = [
        value
        for value in (
            medication.dose,
            medication.route,
            medication.frequency,
            medication.status.value,
        )
        if value
    ]
    return _truncate(", ".join(values) or medication.status.value)


def _date_or_created_at(value: date | None, fallback: datetime) -> datetime:
    if value is None:
        return fallback
    return datetime.combine(value, time.min, tzinfo=fallback.tzinfo)


def _missing_data(
    *,
    encounters: list[ClinicalEncounter],
    entries: list[ClinicalEntry],
    events: list[ClinicalEvent],
    vitals: list[VitalSign],
    medications: list[Medication],
    problems: list[ActiveProblem],
    allergies: list[Allergy],
) -> list[str]:
    missing = []
    if not encounters:
        missing.append("No hay encuentros clinicos estructurados.")
    if not entries:
        missing.append("No hay evoluciones o notas clinicas estructuradas.")
    if not events:
        missing.append("No hay eventos clinicos longitudinales.")
    if not vitals:
        missing.append("No hay signos vitales estructurados.")
    if not medications:
        missing.append("No hay medicacion activa estructurada.")
    if not problems:
        missing.append("No hay problemas activos estructurados.")
    if not allergies:
        missing.append("No hay alergias activas estructuradas.")
    return missing


def _warnings(*, has_more: bool, limit: int) -> list[str]:
    if not has_more:
        return []
    return [f"Timeline limitado a {limit} items; aumenta limit o consulta dominios fuente."]


def _truncate(value: str, max_length: int = 320) -> str:
    normalized = " ".join(value.split())
    if len(normalized) <= max_length:
        return normalized
    return f"{normalized[: max_length - 3].rstrip()}..."
