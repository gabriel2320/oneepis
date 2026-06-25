from __future__ import annotations

import uuid

from oneepis_api.models.clinical_record import (
    ActiveProblem,
    Allergy,
    ClinicalEncounter,
    ClinicalEntry,
    ClinicalEvent,
    Medication,
)
from oneepis_api.models.vital_sign import VitalSign
from oneepis_api.schemas.clinical_record import AssistantSearchResult

from .patient_assistant_common import (
    clinical_event_source_path,
    date_or_created_at,
    matched_fields,
    snippet,
    vital_summary,
)


def encounter_results(query: str, patient_id: uuid.UUID, encounters: list[ClinicalEncounter]):
    return [
        AssistantSearchResult(
            item_type="encounter",
            item_id=encounter.id,
            occurred_at=encounter.started_at,
            label="Encuentro clinico",
            snippet=snippet(query, encounter.reason, encounter.location_label, encounter.notes),
            matched_fields=matched_fields(
                query,
                {
                    "reason": encounter.reason,
                    "location_label": encounter.location_label,
                    "notes": encounter.notes,
                },
            ),
            source_label="encounters",
            source_path=f"/api/v1/patients/{patient_id}/encounters/{encounter.id}",
        )
        for encounter in encounters
    ]


def entry_results(query: str, patient_id: uuid.UUID, entries: list[ClinicalEntry]):
    return [
        AssistantSearchResult(
            item_type="clinical_entry",
            item_id=entry.id,
            occurred_at=entry.occurred_at,
            label=entry.title,
            snippet=snippet(
                query,
                entry.title,
                entry.subjective,
                entry.objective,
                entry.assessment,
                entry.plan,
            ),
            matched_fields=matched_fields(
                query,
                {
                    "title": entry.title,
                    "subjective": entry.subjective,
                    "objective": entry.objective,
                    "assessment": entry.assessment,
                    "plan": entry.plan,
                },
            ),
            source_label="clinical_entries",
            source_path=f"/api/v1/patients/{patient_id}/clinical-entries/{entry.id}",
        )
        for entry in entries
    ]


def event_results(query: str, patient_id: uuid.UUID, events: list[ClinicalEvent]):
    return [
        AssistantSearchResult(
            item_type="clinical_event",
            item_id=event.id,
            occurred_at=event.occurred_at,
            label=event.event_type.value,
            snippet=snippet(query, event.summary),
            matched_fields=matched_fields(query, {"summary": event.summary}),
            source_label="clinical_events",
            source_path=clinical_event_source_path(patient_id, event.id),
        )
        for event in events
    ]


def vital_results(query: str, patient_id: uuid.UUID, vitals: list[VitalSign]):
    return [
        AssistantSearchResult(
            item_type="vital_sign",
            item_id=vital.id,
            occurred_at=vital.measured_at,
            label="Signos vitales",
            snippet=snippet(query, vital.notes, vital_summary(vital)),
            matched_fields=matched_fields(query, {"notes": vital.notes}),
            source_label="vital_signs",
            source_path=f"/api/v1/patients/{patient_id}/vital-signs/{vital.id}",
        )
        for vital in vitals
    ]


def medication_results(query: str, patient_id: uuid.UUID, medications: list[Medication]):
    return [
        AssistantSearchResult(
            item_type="medication",
            item_id=medication.id,
            occurred_at=date_or_created_at(medication.started_on, medication.created_at),
            label=medication.name,
            snippet=snippet(
                query,
                medication.name,
                medication.dose,
                medication.route,
                medication.frequency,
            ),
            matched_fields=matched_fields(
                query,
                {
                    "name": medication.name,
                    "dose": medication.dose,
                    "route": medication.route,
                    "frequency": medication.frequency,
                },
            ),
            source_label="medications",
            source_path=f"/api/v1/patients/{patient_id}/medications/{medication.id}",
        )
        for medication in medications
    ]


def problem_results(query: str, patient_id: uuid.UUID, problems: list[ActiveProblem]):
    return [
        AssistantSearchResult(
            item_type="problem",
            item_id=problem.id,
            occurred_at=date_or_created_at(problem.onset_date, problem.created_at),
            label=problem.title,
            snippet=snippet(query, problem.title, problem.code, problem.notes),
            matched_fields=matched_fields(
                query,
                {"title": problem.title, "code": problem.code, "notes": problem.notes},
            ),
            source_label="problems",
            source_path=f"/api/v1/patients/{patient_id}/problems/{problem.id}",
        )
        for problem in problems
    ]


def allergy_results(query: str, patient_id: uuid.UUID, allergies: list[Allergy]):
    return [
        AssistantSearchResult(
            item_type="allergy",
            item_id=allergy.id,
            occurred_at=allergy.recorded_at,
            label=allergy.substance,
            snippet=snippet(query, allergy.substance, allergy.reaction),
            matched_fields=matched_fields(
                query,
                {"substance": allergy.substance, "reaction": allergy.reaction},
            ),
            source_label="allergies",
            source_path=f"/api/v1/patients/{patient_id}/allergies/{allergy.id}",
        )
        for allergy in allergies
    ]
