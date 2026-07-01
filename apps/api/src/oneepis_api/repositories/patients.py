from __future__ import annotations

import uuid

from sqlalchemy import Select, select
from sqlalchemy.orm import Session, selectinload

from oneepis_api.models.access_boundary import (
    AccessBoundaryStatus,
    ActorCareTeamMembership,
    CareTeam,
    ClinicalInstitution,
    ClinicalService,
    ClinicalTenant,
    PatientCareTeamRelationship,
)
from oneepis_api.models.clinical_record import (
    ActiveProblem,
    Allergy,
    ClinicalEntry,
    ClinicalEntryStatus,
    ClinicalEvent,
    ClinicalEventType,
    Medication,
    RecordStatus,
    VitalSign,
)
from oneepis_api.models.clinical_risk import ClinicalRisk
from oneepis_api.models.patient import Patient


def get_patient(session: Session, patient_id: uuid.UUID) -> Patient | None:
    return session.get(Patient, patient_id)


def list_patients(
    session: Session,
    *,
    search: str | None = None,
    limit: int = 25,
    offset: int = 0,
) -> list[Patient]:
    statement = _patient_index_statement(search=search)
    statement = _order_patient_index(statement, limit=limit, offset=offset)
    return list(session.scalars(statement))


def list_patients_for_active_care_relationship(
    session: Session,
    *,
    actor_id: str,
    search: str | None = None,
    limit: int = 25,
    offset: int = 0,
) -> list[Patient]:
    statement = (
        _patient_index_statement(search=search)
        .join(PatientCareTeamRelationship, PatientCareTeamRelationship.patient_id == Patient.id)
        .join(CareTeam, PatientCareTeamRelationship.care_team_id == CareTeam.id)
        .join(ActorCareTeamMembership, ActorCareTeamMembership.care_team_id == CareTeam.id)
        .join(ClinicalService, CareTeam.service_id == ClinicalService.id)
        .join(ClinicalTenant, ClinicalService.tenant_id == ClinicalTenant.id)
        .join(ClinicalInstitution, ClinicalTenant.institution_id == ClinicalInstitution.id)
        .where(
            ActorCareTeamMembership.actor_id == actor_id,
            ActorCareTeamMembership.status == AccessBoundaryStatus.ACTIVE,
            PatientCareTeamRelationship.status == AccessBoundaryStatus.ACTIVE,
            CareTeam.status == AccessBoundaryStatus.ACTIVE,
            ClinicalService.status == AccessBoundaryStatus.ACTIVE,
            ClinicalTenant.status == AccessBoundaryStatus.ACTIVE,
            ClinicalInstitution.status == AccessBoundaryStatus.ACTIVE,
        )
        .distinct()
    )
    statement = _order_patient_index(statement, limit=limit, offset=offset)
    return list(session.scalars(statement))


def _patient_index_statement(*, search: str | None = None) -> Select[tuple[Patient]]:
    statement: Select[tuple[Patient]] = select(Patient)
    if search:
        like = f"%{search}%"
        statement = statement.where(
            Patient.first_name.ilike(like)
            | Patient.last_name.ilike(like)
            | Patient.clinical_identifier.ilike(like)
        )
    return statement


def _order_patient_index(
    statement: Select[tuple[Patient]],
    *,
    limit: int,
    offset: int,
) -> Select[tuple[Patient]]:
    return statement.order_by(Patient.created_at.desc()).offset(offset).limit(limit)


def get_recent_entries(
    session: Session, patient_id: uuid.UUID, limit: int = 10
) -> list[ClinicalEntry]:
    statement = (
        select(ClinicalEntry)
        .where(
            ClinicalEntry.patient_id == patient_id,
            ClinicalEntry.status != ClinicalEntryStatus.ENTERED_IN_ERROR,
        )
        .order_by(ClinicalEntry.occurred_at.desc())
        .limit(limit)
    )
    return list(session.scalars(statement))


def get_recent_events(
    session: Session, patient_id: uuid.UUID, limit: int = 50
) -> list[ClinicalEvent]:
    statement = (
        select(ClinicalEvent)
        .where(ClinicalEvent.patient_id == patient_id)
        .order_by(ClinicalEvent.occurred_at.desc())
        .limit(limit)
    )
    return list(session.scalars(statement))


def get_diagnosis_events(session: Session, patient_id: uuid.UUID) -> list[ClinicalEvent]:
    statement = (
        select(ClinicalEvent)
        .where(
            ClinicalEvent.patient_id == patient_id,
            ClinicalEvent.event_type == ClinicalEventType.DIAGNOSIS,
        )
        .order_by(ClinicalEvent.occurred_at.desc())
    )
    return list(session.scalars(statement))


def get_latest_vitals(session: Session, patient_id: uuid.UUID) -> VitalSign | None:
    statement = (
        select(VitalSign)
        .where(
            VitalSign.patient_id == patient_id,
            VitalSign.status != RecordStatus.ENTERED_IN_ERROR,
        )
        .order_by(VitalSign.measured_at.desc())
        .limit(1)
    )
    return session.scalars(statement).first()


def get_recent_vitals(
    session: Session, patient_id: uuid.UUID, limit: int = 5
) -> list[VitalSign]:
    statement = (
        select(VitalSign)
        .where(
            VitalSign.patient_id == patient_id,
            VitalSign.status != RecordStatus.ENTERED_IN_ERROR,
        )
        .order_by(VitalSign.measured_at.desc())
        .limit(limit)
    )
    return list(session.scalars(statement))


def get_active_allergies(session: Session, patient_id: uuid.UUID) -> list[Allergy]:
    statement = (
        select(Allergy)
        .where(Allergy.patient_id == patient_id, Allergy.status == RecordStatus.ACTIVE)
        .order_by(Allergy.recorded_at.desc())
    )
    return list(session.scalars(statement))


def get_active_medications(session: Session, patient_id: uuid.UUID) -> list[Medication]:
    statement = (
        select(Medication)
        .options(selectinload(Medication.catalog_item))
        .where(Medication.patient_id == patient_id, Medication.status == RecordStatus.ACTIVE)
        .order_by(Medication.started_on.desc().nullslast())
    )
    return list(session.scalars(statement))


def get_active_problems(session: Session, patient_id: uuid.UUID) -> list[ActiveProblem]:
    statement = (
        select(ActiveProblem)
        .where(ActiveProblem.patient_id == patient_id, ActiveProblem.status == RecordStatus.ACTIVE)
        .order_by(ActiveProblem.created_at.desc())
    )
    return list(session.scalars(statement))


def get_active_risks(session: Session, patient_id: uuid.UUID) -> list[ClinicalRisk]:
    statement = (
        select(ClinicalRisk)
        .where(ClinicalRisk.patient_id == patient_id, ClinicalRisk.status == RecordStatus.ACTIVE)
        .order_by(ClinicalRisk.created_at.desc())
    )
    return list(session.scalars(statement))
