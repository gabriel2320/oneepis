from __future__ import annotations

import uuid

from oneepis_api.models.clinical_record import (
    ActiveProblem,
    Allergy,
    ClinicalEncounter,
    ClinicalEntry,
    ClinicalEvent,
    Medication,
    VitalSign,
)
from oneepis_api.schemas.clinical_record import AssistantTimelineItem
from oneepis_api.schemas.patient import HistoricalDiagnosisRead

from .patient_assistant_common import (
    clinical_event_source_path,
    date_or_created_at,
    entry_sections,
    medication_summary,
    truncate,
    vital_summary,
)


def encounter_items(
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
            **_encounter_metadata(encounter),
        )
        for encounter in encounters
    ]


def entry_items(
    patient_id: uuid.UUID,
    entries: list[ClinicalEntry],
) -> list[AssistantTimelineItem]:
    return [
        AssistantTimelineItem(
            item_type="clinical_entry",
            item_id=entry.id,
            occurred_at=entry.occurred_at,
            label=entry.title,
            summary=truncate(" / ".join(entry_sections(entry)) or entry.kind.value),
            source_label="clinical_entries",
            source_path=f"/api/v1/patients/{patient_id}/clinical-entries/{entry.id}",
            **_encounter_metadata(entry.encounter),
        )
        for entry in entries
    ]


def event_items(patient_id: uuid.UUID, events: list[ClinicalEvent]) -> list[AssistantTimelineItem]:
    return [
        AssistantTimelineItem(
            item_type="clinical_event",
            item_id=event.id,
            occurred_at=event.occurred_at,
            label=event.event_type.value,
            summary=event.summary,
            source_label="clinical_events",
            source_path=clinical_event_source_path(patient_id, event.id),
            **_encounter_metadata(event.encounter),
        )
        for event in events
    ]


def historical_diagnosis_items(
    patient_id: uuid.UUID,
    diagnoses: list[HistoricalDiagnosisRead],
    source_events: dict[uuid.UUID, ClinicalEvent],
) -> list[AssistantTimelineItem]:
    return [
        AssistantTimelineItem(
            item_type="clinical_event",
            item_id=diagnosis.source_event_id,
            occurred_at=diagnosis.occurred_at,
            label=diagnosis.title,
            summary=_historical_diagnosis_summary(diagnosis),
            source_label=diagnosis.source_label,
            source_path=clinical_event_source_path(patient_id, diagnosis.source_event_id),
            **_encounter_metadata(_historical_source_encounter(diagnosis, source_events)),
        )
        for diagnosis in diagnoses
    ]


def vital_items(patient_id: uuid.UUID, vitals: list[VitalSign]) -> list[AssistantTimelineItem]:
    return [
        AssistantTimelineItem(
            item_type="vital_sign",
            item_id=vital.id,
            occurred_at=vital.measured_at,
            label="Signos vitales",
            summary=vital_summary(vital),
            source_label="vital_signs",
            source_path=f"/api/v1/patients/{patient_id}/vital-signs/{vital.id}",
        )
        for vital in vitals
    ]


def medication_items(
    patient_id: uuid.UUID,
    medications: list[Medication],
) -> list[AssistantTimelineItem]:
    return [
        AssistantTimelineItem(
            item_type="medication",
            item_id=medication.id,
            occurred_at=date_or_created_at(medication.started_on, medication.created_at),
            label=medication.name,
            summary=medication_summary(medication),
            source_label="medications",
            source_path=f"/api/v1/patients/{patient_id}/medications/{medication.id}",
        )
        for medication in medications
    ]


def problem_items(
    patient_id: uuid.UUID,
    problems: list[ActiveProblem],
) -> list[AssistantTimelineItem]:
    return [
        AssistantTimelineItem(
            item_type="problem",
            item_id=problem.id,
            occurred_at=date_or_created_at(problem.onset_date, problem.created_at),
            label=problem.title,
            summary=truncate(problem.notes or problem.code or problem.status.value),
            source_label="problems",
            source_path=f"/api/v1/patients/{patient_id}/problems/{problem.id}",
        )
        for problem in problems
    ]


def allergy_items(patient_id: uuid.UUID, allergies: list[Allergy]) -> list[AssistantTimelineItem]:
    return [
        AssistantTimelineItem(
            item_type="allergy",
            item_id=allergy.id,
            occurred_at=allergy.recorded_at,
            label=allergy.substance,
            summary=truncate(allergy.reaction or allergy.severity.value),
            source_label="allergies",
            source_path=f"/api/v1/patients/{patient_id}/allergies/{allergy.id}",
        )
        for allergy in allergies
    ]


def timeline_missing_data(
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


def timeline_warnings(*, has_more: bool, limit: int) -> list[str]:
    if not has_more:
        return []
    return [f"Timeline limitado a {limit} items; aumenta limit o consulta dominios fuente."]


def _historical_diagnosis_summary(diagnosis: HistoricalDiagnosisRead) -> str:
    code = f" ({diagnosis.code_system or 'Codigo'}: {diagnosis.code})" if diagnosis.code else ""
    return truncate(f"{diagnosis.source_label}: {diagnosis.limit}{code}")


def _historical_source_encounter(
    diagnosis: HistoricalDiagnosisRead,
    source_events: dict[uuid.UUID, ClinicalEvent],
) -> ClinicalEncounter | None:
    event = source_events.get(diagnosis.source_event_id)
    if event is None:
        return None
    return event.encounter


def _encounter_metadata(encounter: ClinicalEncounter | None) -> dict[str, object]:
    if encounter is None:
        return {"scope": "longitudinal"}
    return {
        "encounter_id": encounter.id,
        "encounter_type": encounter.type,
        "encounter_status": encounter.status,
        "scope": encounter.type.value if encounter.type.value != "unknown" else "unknown",
    }
