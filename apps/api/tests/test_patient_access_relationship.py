import uuid
from collections.abc import Iterator
from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from oneepis_api.core.access_boundary_contract import ACCESS_BOUNDARY_RUNTIME_STATUS
from oneepis_api.db.base import Base
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
from oneepis_api.services.patient_access_relationship import (
    resolve_patient_access_relationship_dry_run,
)


def test_patient_access_relationship_dry_run_resolves_shared_active_care_team(
    session: Session,
) -> None:
    patient = _patient(session)
    care_team = _care_team(session)
    session.add_all(
        [
            ActorCareTeamMembership(
                actor_id="medico@oneepis.local",
                care_team_id=care_team.id,
                status=AccessBoundaryStatus.ACTIVE,
            ),
            PatientCareTeamRelationship(
                patient_id=patient.id,
                care_team_id=care_team.id,
                status=AccessBoundaryStatus.ACTIVE,
            ),
        ]
    )
    session.commit()

    result = resolve_patient_access_relationship_dry_run(
        session,
        actor_id="medico@oneepis.local",
        patient_id=patient.id,
    )

    assert result.resolved is True
    assert result.status == "resolved"
    assert result.matched_care_team_ids == (care_team.id,)
    assert result.actor_active_care_team_count == 1
    assert result.patient_active_care_team_count == 1
    assert result.runtime_enforced is False
    assert result.as_metadata() == {
        "status": "resolved",
        "matched_care_team_count": 1,
        "actor_active_care_team_count": 1,
        "patient_active_care_team_count": 1,
        "runtime_enforced": False,
    }


def test_patient_access_relationship_dry_run_ignores_draft_and_retired_links(
    session: Session,
) -> None:
    patient = _patient(session)
    active_actor_team = _care_team(session, key="team-actor")
    retired_patient_team = _care_team(session, key="team-patient")
    session.add_all(
        [
            ActorCareTeamMembership(
                actor_id="medico@oneepis.local",
                care_team_id=active_actor_team.id,
                status=AccessBoundaryStatus.ACTIVE,
            ),
            PatientCareTeamRelationship(
                patient_id=patient.id,
                care_team_id=active_actor_team.id,
                status=AccessBoundaryStatus.DRAFT,
            ),
            PatientCareTeamRelationship(
                patient_id=patient.id,
                care_team_id=retired_patient_team.id,
                status=AccessBoundaryStatus.RETIRED,
            ),
        ]
    )
    session.commit()

    result = resolve_patient_access_relationship_dry_run(
        session,
        actor_id="medico@oneepis.local",
        patient_id=patient.id,
    )

    assert result.resolved is False
    assert result.status == "none"
    assert result.matched_care_team_ids == ()
    assert result.actor_active_care_team_count == 1
    assert result.patient_active_care_team_count == 0


def test_patient_access_relationship_dry_run_does_not_enable_abac_runtime(
    session: Session,
) -> None:
    assert ACCESS_BOUNDARY_RUNTIME_STATUS["patient_scoping_enabled"] is False
    assert ACCESS_BOUNDARY_RUNTIME_STATUS["abac_runtime_enforced"] is False

    patient = _patient(session)

    result = resolve_patient_access_relationship_dry_run(
        session,
        actor_id="medico@oneepis.local",
        patient_id=patient.id,
    )

    assert result.runtime_enforced is False
    assert result.as_metadata()["runtime_enforced"] is False


@pytest.fixture
def session() -> Iterator[Session]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    testing_session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    with testing_session() as active_session:
        yield active_session
    Base.metadata.drop_all(engine)


def _patient(session: Session) -> Patient:
    patient = Patient(
        first_name="ABAC",
        last_name="Paciente",
        birth_date=date(1990, 1, 1),
        sex_at_birth=SexAtBirth.UNKNOWN,
    )
    session.add(patient)
    session.commit()
    return patient


def _care_team(session: Session, *, key: str = "team-a") -> CareTeam:
    suffix = uuid.uuid4().hex[:8]
    institution = ClinicalInstitution(
        key=f"institution-{key}-{suffix}",
        display_name="Institucion ABAC",
        status=AccessBoundaryStatus.ACTIVE,
    )
    tenant = ClinicalTenant(
        institution=institution,
        key=f"tenant-{key}-{suffix}",
        display_name="Tenant ABAC",
        status=AccessBoundaryStatus.ACTIVE,
    )
    service = ClinicalService(
        tenant=tenant,
        key=f"service-{key}-{suffix}",
        display_name="Servicio ABAC",
        status=AccessBoundaryStatus.ACTIVE,
    )
    care_team = CareTeam(
        service=service,
        key=f"care-team-{key}-{suffix}",
        display_name="Equipo ABAC",
        status=AccessBoundaryStatus.ACTIVE,
    )
    session.add(care_team)
    session.commit()
    return care_team
