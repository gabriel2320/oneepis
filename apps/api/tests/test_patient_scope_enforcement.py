import uuid

import pytest
from access_boundary_helpers import (
    assign_actor_to_care_team,
    assign_patient_to_care_team,
    create_abac_patient,
    create_care_team,
)
from fastapi import HTTPException
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from oneepis_api.core.config import Settings
from oneepis_api.db.base import Base
from oneepis_api.models.access_boundary import AccessBoundaryStatus
from oneepis_api.models.audit import AuditEvent
from oneepis_api.services.auth import UserRole
from oneepis_api.services.patient_scope_enforcement import (
    PATIENT_SCOPE_DENIAL_DETAIL,
    enforce_patient_scope_for_read,
)


def test_patient_scope_enforcement_is_noop_when_flag_disabled() -> None:
    session = _session()
    patient_id = uuid.uuid4()

    enforce_patient_scope_for_read(
        session,
        patient_id=patient_id,
        actor_id="medico@oneepis.local",
        roles=frozenset({UserRole.MEDICO}),
        settings=Settings(ai_provider="local_rules"),
    )

    assert session.scalars(select(AuditEvent)).all() == []


def test_patient_scope_enforcement_denies_and_audits_missing_relationship() -> None:
    session = _session()
    patient_id = uuid.uuid4()

    with pytest.raises(HTTPException) as exc:
        enforce_patient_scope_for_read(
            session,
            patient_id=patient_id,
            actor_id="medico@oneepis.local",
            roles=frozenset({UserRole.MEDICO}),
            settings=Settings(
                ai_provider="local_rules",
                abac_enforcement_enabled=True,
            ),
        )

    assert exc.value.status_code == 403
    assert exc.value.detail == PATIENT_SCOPE_DENIAL_DETAIL
    event = session.scalars(select(AuditEvent)).one()
    assert event.action == "access_context.denied"
    assert event.entity_type == "patient"
    assert event.entity_id == patient_id
    assert event.actor_id == "medico@oneepis.local"
    assert event.extra_data == {
        "policy": "contextual_abac",
        "runtime_enforced": True,
        "reason_keys": ["active_care_relationship_or_access_reason"],
        "metadata_retention": "requirement_keys_only",
    }


def test_patient_scope_enforcement_allows_shared_active_care_team() -> None:
    session = _session()
    patient = create_abac_patient(session)
    care_team = create_care_team(session)
    assign_actor_to_care_team(
        session,
        actor_id="medico@oneepis.local",
        care_team=care_team,
    )
    assign_patient_to_care_team(session, patient=patient, care_team=care_team)

    enforce_patient_scope_for_read(
        session,
        patient_id=patient.id,
        actor_id="medico@oneepis.local",
        roles=frozenset({UserRole.MEDICO}),
        settings=Settings(
            ai_provider="local_rules",
            abac_enforcement_enabled=True,
        ),
    )

    assert session.scalars(select(AuditEvent)).all() == []


def test_patient_scope_enforcement_denies_relationship_on_retired_boundary_chain() -> None:
    session = _session()
    patient = create_abac_patient(session)
    care_team = create_care_team(session, care_team_status=AccessBoundaryStatus.RETIRED)
    assign_actor_to_care_team(
        session,
        actor_id="medico@oneepis.local",
        care_team=care_team,
    )
    assign_patient_to_care_team(session, patient=patient, care_team=care_team)

    with pytest.raises(HTTPException) as exc:
        enforce_patient_scope_for_read(
            session,
            patient_id=patient.id,
            actor_id="medico@oneepis.local",
            roles=frozenset({UserRole.MEDICO}),
            settings=Settings(
                ai_provider="local_rules",
                abac_enforcement_enabled=True,
            ),
        )

    assert exc.value.status_code == 403
    assert exc.value.detail == PATIENT_SCOPE_DENIAL_DETAIL
    event = session.scalars(select(AuditEvent)).one()
    assert event.action == "access_context.denied"
    assert event.entity_id == patient.id


def test_patient_scope_enforcement_keeps_admin_and_dev_breakout() -> None:
    for role in (UserRole.ADMIN, UserRole.DEV):
        session = _session()

        enforce_patient_scope_for_read(
            session,
            patient_id=uuid.uuid4(),
            actor_id=f"{role.value}@oneepis.local",
            roles=frozenset({role}),
            settings=Settings(
                ai_provider="local_rules",
                abac_enforcement_enabled=True,
            ),
        )

        assert session.scalars(select(AuditEvent)).all() == []


def _session() -> Session:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    testing_session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    return testing_session()
