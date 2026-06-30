from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Literal

from sqlalchemy import select
from sqlalchemy.orm import Session

from oneepis_api.core.access_boundary_contract import ACCESS_BOUNDARY_RUNTIME_STATUS
from oneepis_api.models.access_boundary import (
    AccessBoundaryStatus,
    ActorCareTeamMembership,
    CareTeam,
    ClinicalInstitution,
    ClinicalService,
    ClinicalTenant,
    PatientCareTeamRelationship,
)

PatientAccessRelationshipStatus = Literal["resolved", "none"]


@dataclass(frozen=True)
class PatientAccessRelationshipDryRun:
    actor_id: str
    patient_id: uuid.UUID
    status: PatientAccessRelationshipStatus
    matched_care_team_ids: tuple[uuid.UUID, ...]
    actor_active_care_team_count: int
    patient_active_care_team_count: int
    runtime_enforced: bool

    @property
    def resolved(self) -> bool:
        return self.status == "resolved"

    def as_metadata(self) -> dict[str, object]:
        return {
            "status": self.status,
            "matched_care_team_count": len(self.matched_care_team_ids),
            "actor_active_care_team_count": self.actor_active_care_team_count,
            "patient_active_care_team_count": self.patient_active_care_team_count,
            "runtime_enforced": self.runtime_enforced,
        }


def resolve_patient_access_relationship_dry_run(
    session: Session,
    *,
    actor_id: str,
    patient_id: uuid.UUID,
) -> PatientAccessRelationshipDryRun:
    actor_care_team_ids = _active_actor_care_team_ids(session, actor_id=actor_id)
    patient_care_team_ids = _active_patient_care_team_ids(session, patient_id=patient_id)
    matched_care_team_ids = tuple(
        sorted(actor_care_team_ids & patient_care_team_ids, key=lambda item: item.hex)
    )

    return PatientAccessRelationshipDryRun(
        actor_id=actor_id,
        patient_id=patient_id,
        status="resolved" if matched_care_team_ids else "none",
        matched_care_team_ids=matched_care_team_ids,
        actor_active_care_team_count=len(actor_care_team_ids),
        patient_active_care_team_count=len(patient_care_team_ids),
        runtime_enforced=bool(ACCESS_BOUNDARY_RUNTIME_STATUS["abac_runtime_enforced"]),
    )


def _active_actor_care_team_ids(session: Session, *, actor_id: str) -> set[uuid.UUID]:
    statement = (
        select(ActorCareTeamMembership.care_team_id)
        .join(CareTeam, ActorCareTeamMembership.care_team_id == CareTeam.id)
        .join(ClinicalService, CareTeam.service_id == ClinicalService.id)
        .join(ClinicalTenant, ClinicalService.tenant_id == ClinicalTenant.id)
        .join(ClinicalInstitution, ClinicalTenant.institution_id == ClinicalInstitution.id)
        .where(
            ActorCareTeamMembership.actor_id == actor_id,
            ActorCareTeamMembership.status == AccessBoundaryStatus.ACTIVE,
            CareTeam.status == AccessBoundaryStatus.ACTIVE,
            ClinicalService.status == AccessBoundaryStatus.ACTIVE,
            ClinicalTenant.status == AccessBoundaryStatus.ACTIVE,
            ClinicalInstitution.status == AccessBoundaryStatus.ACTIVE,
        )
    )
    return set(session.scalars(statement).all())


def _active_patient_care_team_ids(session: Session, *, patient_id: uuid.UUID) -> set[uuid.UUID]:
    statement = (
        select(PatientCareTeamRelationship.care_team_id)
        .join(CareTeam, PatientCareTeamRelationship.care_team_id == CareTeam.id)
        .join(ClinicalService, CareTeam.service_id == ClinicalService.id)
        .join(ClinicalTenant, ClinicalService.tenant_id == ClinicalTenant.id)
        .join(ClinicalInstitution, ClinicalTenant.institution_id == ClinicalInstitution.id)
        .where(
            PatientCareTeamRelationship.patient_id == patient_id,
            PatientCareTeamRelationship.status == AccessBoundaryStatus.ACTIVE,
            CareTeam.status == AccessBoundaryStatus.ACTIVE,
            ClinicalService.status == AccessBoundaryStatus.ACTIVE,
            ClinicalTenant.status == AccessBoundaryStatus.ACTIVE,
            ClinicalInstitution.status == AccessBoundaryStatus.ACTIVE,
        )
    )
    return set(session.scalars(statement).all())
