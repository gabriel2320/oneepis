from __future__ import annotations

import uuid

from oneepis_api.models.clinical_record import (
    ActiveProblem,
    Allergy,
    ClinicalEncounter,
    ClinicalEntry,
    EncounterType,
    Medication,
)
from oneepis_api.models.clinical_risk import ClinicalRisk
from oneepis_api.models.lab import LabPanel
from oneepis_api.schemas.clinical_record import (
    PatientContextEncounter,
    PatientContextListItem,
    PatientContextTimelineItem,
)


def encounter_context(encounter: ClinicalEncounter | None) -> PatientContextEncounter | None:
    if encounter is None:
        return None
    return PatientContextEncounter(
        id=encounter.id,
        type=encounter.type,
        status=encounter.status,
        workflow_kind=encounter.workflow_kind,
        reason=encounter.reason,
        started_at=encounter.started_at,
        ended_at=encounter.ended_at,
        location_label=encounter.location_label,
    )


def derived_care_context(encounter: ClinicalEncounter | None) -> str:
    if encounter is None or encounter.type == EncounterType.UNKNOWN:
        return "unknown"
    if encounter.type == EncounterType.HOSPITALIZATION:
        return "hospitalization"
    return encounter.type.value


def problem_item(patient_id: uuid.UUID, problem: ActiveProblem) -> PatientContextListItem:
    return PatientContextListItem(
        id=problem.id,
        label=problem.title,
        summary=problem.notes or problem.code or problem.status.value,
        source_type="problem",
        source_path=f"/api/v1/patients/{patient_id}/problems/{problem.id}",
    )


def allergy_item(patient_id: uuid.UUID, allergy: Allergy) -> PatientContextListItem:
    return PatientContextListItem(
        id=allergy.id,
        label=allergy.substance,
        summary=allergy.reaction or allergy.severity.value,
        source_type="allergy",
        source_path=f"/api/v1/patients/{patient_id}/allergies/{allergy.id}",
    )


def medication_item(patient_id: uuid.UUID, medication: Medication) -> PatientContextListItem:
    return PatientContextListItem(
        id=medication.id,
        label=medication.name,
        summary=", ".join(
            value
            for value in (medication.dose, medication.route, medication.frequency)
            if value
        )
        or medication.status.value,
        source_type="medication",
        source_path=f"/api/v1/patients/{patient_id}/medications/{medication.id}",
    )


def risk_item(patient_id: uuid.UUID, risk: ClinicalRisk) -> PatientContextListItem:
    return PatientContextListItem(
        id=risk.id,
        label=risk.risk_type.value,
        summary=risk.reason,
        source_type="clinical_risk",
        source_path=f"/api/v1/patients/{patient_id}/clinical-risks/{risk.id}",
        encounter_id=risk.encounter_id,
        encounter_type=risk.encounter.type if risk.encounter else None,
    )


def lab_item(patient_id: uuid.UUID, panel: LabPanel) -> PatientContextListItem:
    return PatientContextListItem(
        id=panel.id,
        label=panel.panel_name,
        summary=panel.summary or panel.source_type.value,
        source_type="lab_panel",
        source_path=f"/api/v1/patients/{patient_id}/lab-panels/{panel.id}",
        encounter_id=panel.encounter_id,
        encounter_type=panel.encounter.type if panel.encounter else None,
    )


def entry_timeline_item(patient_id: uuid.UUID, entry: ClinicalEntry) -> PatientContextTimelineItem:
    summary = " / ".join(
        value
        for value in (entry.subjective, entry.objective, entry.assessment, entry.plan)
        if value
    )
    return PatientContextTimelineItem(
        item_type="clinical_entry",
        item_id=entry.id,
        occurred_at=entry.occurred_at,
        label=entry.title,
        summary=truncate(summary or entry.kind.value),
        source_path=f"/api/v1/patients/{patient_id}/clinical-entries/{entry.id}",
        encounter_id=entry.encounter_id,
        encounter_type=entry.encounter.type if entry.encounter else None,
    )


def truncate(value: str, max_length: int = 320) -> str:
    normalized = " ".join(value.split())
    if len(normalized) <= max_length:
        return normalized or "Sin resumen estructurado."
    return f"{normalized[: max_length - 3].rstrip()}..."
