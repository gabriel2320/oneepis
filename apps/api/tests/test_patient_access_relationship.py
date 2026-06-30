from collections.abc import Iterator

import pytest
from access_boundary_helpers import (
    assign_actor_to_care_team,
    assign_patient_to_care_team,
    create_abac_patient,
    create_care_team,
)
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from oneepis_api.core.access_boundary_contract import ACCESS_BOUNDARY_RUNTIME_STATUS
from oneepis_api.db.base import Base
from oneepis_api.models.access_boundary import AccessBoundaryStatus
from oneepis_api.services.patient_access_relationship import (
    resolve_patient_access_relationship_dry_run,
)


def test_patient_access_relationship_dry_run_resolves_shared_active_care_team(
    session: Session,
) -> None:
    patient = create_abac_patient(session)
    care_team = create_care_team(session)
    assign_actor_to_care_team(
        session,
        actor_id="medico@oneepis.local",
        care_team=care_team,
    )
    assign_patient_to_care_team(session, patient=patient, care_team=care_team)

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


@pytest.mark.parametrize(
    ("status_kwarg", "inactive_status"),
    [
        ("care_team_status", AccessBoundaryStatus.DRAFT),
        ("care_team_status", AccessBoundaryStatus.RETIRED),
        ("service_status", AccessBoundaryStatus.DRAFT),
        ("service_status", AccessBoundaryStatus.RETIRED),
        ("tenant_status", AccessBoundaryStatus.DRAFT),
        ("tenant_status", AccessBoundaryStatus.RETIRED),
        ("institution_status", AccessBoundaryStatus.DRAFT),
        ("institution_status", AccessBoundaryStatus.RETIRED),
    ],
)
def test_patient_access_relationship_dry_run_requires_active_boundary_chain(
    session: Session,
    status_kwarg: str,
    inactive_status: AccessBoundaryStatus,
) -> None:
    patient = create_abac_patient(session)
    care_team = create_care_team(session, **{status_kwarg: inactive_status})
    assign_actor_to_care_team(
        session,
        actor_id="medico@oneepis.local",
        care_team=care_team,
    )
    assign_patient_to_care_team(session, patient=patient, care_team=care_team)

    result = resolve_patient_access_relationship_dry_run(
        session,
        actor_id="medico@oneepis.local",
        patient_id=patient.id,
    )

    assert result.resolved is False
    assert result.status == "none"
    assert result.matched_care_team_ids == ()
    assert result.actor_active_care_team_count == 0
    assert result.patient_active_care_team_count == 0


def test_patient_access_relationship_dry_run_ignores_draft_and_retired_links(
    session: Session,
) -> None:
    patient = create_abac_patient(session)
    active_actor_team = create_care_team(session, key="team-actor")
    retired_patient_team = create_care_team(session, key="team-patient")
    assign_actor_to_care_team(
        session,
        actor_id="medico@oneepis.local",
        care_team=active_actor_team,
    )
    assign_patient_to_care_team(
        session,
        patient=patient,
        care_team=active_actor_team,
        status=AccessBoundaryStatus.DRAFT,
    )
    assign_patient_to_care_team(
        session,
        patient=patient,
        care_team=retired_patient_team,
        status=AccessBoundaryStatus.RETIRED,
    )

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

    patient = create_abac_patient(session)

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
