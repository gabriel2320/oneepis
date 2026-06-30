from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy.orm import Session

from oneepis_api.models.access_boundary import (
    AccessBoundaryStatus,
    ActorCareTeamMembership,
    CareTeam,
    ClinicalInstitution,
    ClinicalService,
    ClinicalTenant,
    PatientCareTeamRelationship,
)
from oneepis_api.models.patient import Patient, SexAtBirth


def create_abac_patient(session: Session, *, first_name: str = "ABAC") -> Patient:
    patient = Patient(
        first_name=first_name,
        last_name="Paciente",
        birth_date=date(1990, 1, 1),
        sex_at_birth=SexAtBirth.UNKNOWN,
    )
    session.add(patient)
    session.commit()
    return patient


def create_care_team(
    session: Session,
    *,
    key: str = "team-a",
    status: AccessBoundaryStatus = AccessBoundaryStatus.ACTIVE,
) -> CareTeam:
    suffix = uuid.uuid4().hex[:8]
    institution = ClinicalInstitution(
        key=f"institution-{key}-{suffix}",
        display_name="Institucion ABAC",
        status=status,
    )
    tenant = ClinicalTenant(
        institution=institution,
        key=f"tenant-{key}-{suffix}",
        display_name="Tenant ABAC",
        status=status,
    )
    service = ClinicalService(
        tenant=tenant,
        key=f"service-{key}-{suffix}",
        display_name="Servicio ABAC",
        status=status,
    )
    care_team = CareTeam(
        service=service,
        key=f"care-team-{key}-{suffix}",
        display_name="Equipo ABAC",
        status=status,
    )
    session.add(care_team)
    session.commit()
    return care_team


def assign_actor_to_care_team(
    session: Session,
    *,
    actor_id: str,
    care_team: CareTeam,
    status: AccessBoundaryStatus = AccessBoundaryStatus.ACTIVE,
    membership_reason: str | None = None,
) -> ActorCareTeamMembership:
    membership = ActorCareTeamMembership(
        actor_id=actor_id,
        care_team_id=care_team.id,
        status=status,
        membership_reason=membership_reason,
    )
    session.add(membership)
    session.commit()
    return membership


def assign_patient_to_care_team(
    session: Session,
    *,
    patient: Patient,
    care_team: CareTeam,
    status: AccessBoundaryStatus = AccessBoundaryStatus.ACTIVE,
    relationship_reason: str | None = None,
) -> PatientCareTeamRelationship:
    relationship = PatientCareTeamRelationship(
        patient_id=patient.id,
        care_team_id=care_team.id,
        status=status,
        relationship_reason=relationship_reason,
    )
    session.add(relationship)
    session.commit()
    return relationship
