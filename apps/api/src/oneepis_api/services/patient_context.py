from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from oneepis_api.models.clinical_record import (
    ActiveProblem,
    Allergy,
    ClinicalEncounter,
    ClinicalEntry,
    EncounterStatus,
    EncounterType,
    Medication,
    RecordStatus,
)
from oneepis_api.models.clinical_risk import ClinicalRisk
from oneepis_api.models.lab import LabPanel
from oneepis_api.models.patient import Patient
from oneepis_api.schemas.clinical_record import (
    PatientContextPatient,
    PatientContextResponse,
)
from oneepis_api.services.patient_context_mappers import (
    allergy_item,
    derived_care_context,
    encounter_context,
    entry_timeline_item,
    lab_item,
    medication_item,
    problem_item,
    risk_item,
)

CONTEXT_LIMIT = 10


def build_patient_context(session: Session, patient: Patient) -> PatientContextResponse:
    active_encounters = _active_encounters(session, patient.id)
    active_encounter = _primary_active_encounter(active_encounters)
    active_hospitalization = next(
        (
            encounter
            for encounter in active_encounters
            if encounter.type == EncounterType.HOSPITALIZATION
        ),
        None,
    )
    recent_ambulatory = _recent_encounters(session, patient.id, EncounterType.AMBULATORY)
    problems = _active_problems(session, patient.id)
    allergies = _active_allergies(session, patient.id)
    medications = _active_medications(session, patient.id)
    risks = _active_risks(session, patient.id)
    labs = _recent_labs(session, patient.id)
    timeline_entries = _recent_entries(session, patient.id)

    return PatientContextResponse(
        patient_id=patient.id,
        patient=PatientContextPatient(
            id=patient.id,
            first_name=patient.first_name,
            last_name=patient.last_name,
            preferred_name=patient.preferred_name,
            sex_at_birth=patient.sex_at_birth,
            clinical_status=patient.clinical_status,
            current_care_context=patient.current_care_context,
            clinical_identifier=patient.clinical_identifier,
        ),
        derived_care_context=derived_care_context(active_encounter),
        active_encounter=encounter_context(active_encounter),
        active_hospitalization=encounter_context(active_hospitalization),
        recent_ambulatory_encounters=[
            encounter_context(encounter) for encounter in recent_ambulatory
        ],
        active_problems=[problem_item(patient.id, problem) for problem in problems],
        allergies=[allergy_item(patient.id, allergy) for allergy in allergies],
        active_medications=[medication_item(patient.id, medication) for medication in medications],
        active_risks=[risk_item(patient.id, risk) for risk in risks],
        recent_labs=[lab_item(patient.id, panel) for panel in labs],
        timeline=[entry_timeline_item(patient.id, entry) for entry in timeline_entries],
        missing_data=_missing_data(
            active_encounter=active_encounter,
            problems=problems,
            allergies=allergies,
            medications=medications,
            labs=labs,
        ),
        limits=[f"Contexto limitado a {CONTEXT_LIMIT} registros recientes por dominio."],
    )


def _active_encounters(session: Session, patient_id: uuid.UUID) -> list[ClinicalEncounter]:
    return list(
        session.scalars(
            select(ClinicalEncounter)
            .where(
                ClinicalEncounter.patient_id == patient_id,
                ClinicalEncounter.status == EncounterStatus.IN_PROGRESS,
            )
            .order_by(ClinicalEncounter.started_at.desc())
            .limit(CONTEXT_LIMIT)
        )
    )


def _primary_active_encounter(
    encounters: list[ClinicalEncounter],
) -> ClinicalEncounter | None:
    priority = {
        EncounterType.HOSPITALIZATION: 0,
        EncounterType.EMERGENCY: 1,
        EncounterType.AMBULATORY: 2,
        EncounterType.UNKNOWN: 3,
    }
    return min(encounters, key=lambda encounter: priority[encounter.type], default=None)


def _recent_encounters(
    session: Session,
    patient_id: uuid.UUID,
    encounter_type: EncounterType,
) -> list[ClinicalEncounter]:
    return list(
        session.scalars(
            select(ClinicalEncounter)
            .where(
                ClinicalEncounter.patient_id == patient_id,
                ClinicalEncounter.type == encounter_type,
            )
            .order_by(ClinicalEncounter.started_at.desc())
            .limit(CONTEXT_LIMIT)
        )
    )


def _active_problems(session: Session, patient_id: uuid.UUID) -> list[ActiveProblem]:
    return list(
        session.scalars(
            select(ActiveProblem)
            .where(
                ActiveProblem.patient_id == patient_id,
                ActiveProblem.status == RecordStatus.ACTIVE,
            )
            .order_by(ActiveProblem.created_at.desc())
            .limit(CONTEXT_LIMIT)
        )
    )


def _active_allergies(session: Session, patient_id: uuid.UUID) -> list[Allergy]:
    return list(
        session.scalars(
            select(Allergy)
            .where(Allergy.patient_id == patient_id, Allergy.status == RecordStatus.ACTIVE)
            .order_by(Allergy.recorded_at.desc())
            .limit(CONTEXT_LIMIT)
        )
    )


def _active_medications(session: Session, patient_id: uuid.UUID) -> list[Medication]:
    return list(
        session.scalars(
            select(Medication)
            .where(Medication.patient_id == patient_id, Medication.status == RecordStatus.ACTIVE)
            .order_by(Medication.created_at.desc())
            .limit(CONTEXT_LIMIT)
        )
    )


def _active_risks(session: Session, patient_id: uuid.UUID) -> list[ClinicalRisk]:
    return list(
        session.scalars(
            select(ClinicalRisk)
            .options(selectinload(ClinicalRisk.encounter))
            .where(
                ClinicalRisk.patient_id == patient_id,
                ClinicalRisk.status == RecordStatus.ACTIVE,
            )
            .order_by(ClinicalRisk.created_at.desc())
            .limit(CONTEXT_LIMIT)
        )
    )


def _recent_labs(session: Session, patient_id: uuid.UUID) -> list[LabPanel]:
    return list(
        session.scalars(
            select(LabPanel)
            .options(selectinload(LabPanel.encounter))
            .where(LabPanel.patient_id == patient_id, LabPanel.status == RecordStatus.ACTIVE)
            .order_by(LabPanel.occurred_at.desc())
            .limit(CONTEXT_LIMIT)
        )
    )


def _recent_entries(session: Session, patient_id: uuid.UUID) -> list[ClinicalEntry]:
    return list(
        session.scalars(
            select(ClinicalEntry)
            .options(selectinload(ClinicalEntry.encounter))
            .where(ClinicalEntry.patient_id == patient_id)
            .order_by(ClinicalEntry.occurred_at.desc())
            .limit(CONTEXT_LIMIT)
        )
    )


def _missing_data(
    *,
    active_encounter: ClinicalEncounter | None,
    problems: list[ActiveProblem],
    allergies: list[Allergy],
    medications: list[Medication],
    labs: list[LabPanel],
) -> list[str]:
    missing = []
    if active_encounter is None:
        missing.append("No hay encuentro clinico activo estructurado.")
    if not problems:
        missing.append("No hay problemas activos estructurados.")
    if not allergies:
        missing.append("No hay alergias activas estructuradas.")
    if not medications:
        missing.append("No hay medicacion activa estructurada.")
    if not labs:
        missing.append("No hay laboratorios recientes estructurados.")
    return missing
