import uuid

from access_boundary_helpers import (
    assign_actor_to_care_team,
    assign_patient_to_care_team,
    create_abac_patient,
    create_care_team,
)
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from oneepis_api.api.v1.routes.patient_shared import record_patient_scoped_read
from oneepis_api.db.base import Base
from oneepis_api.models.audit import AuditEvent
from oneepis_api.services.access_context_audit import PASSIVE_ACCESS_CONTEXT_DECISION_ACTION
from oneepis_api.services.audit import (
    AuditRequestContext,
    clear_audit_request_context,
    set_audit_request_context,
)


def test_patient_scoped_read_records_passive_abac_decision_without_relationship() -> None:
    session = _session()
    patient_id = uuid.uuid4()
    set_audit_request_context(
        AuditRequestContext(
            correlation_id="passive-abac-unit-001",
            request_method="GET",
            request_path=f"/api/v1/patients/{patient_id}/record",
        )
    )
    try:
        record_patient_scoped_read(
            session,
            patient_id=patient_id,
            actor_id="medico@oneepis.local",
            action="record.read",
        )
    finally:
        clear_audit_request_context()

    events = session.scalars(select(AuditEvent).order_by(AuditEvent.created_at.asc())).all()
    assert [event.action for event in events] == [
        "record.read",
        PASSIVE_ACCESS_CONTEXT_DECISION_ACTION,
    ]
    passive_event = events[1]
    assert passive_event.entity_type == "patient"
    assert passive_event.entity_id == patient_id
    assert passive_event.actor_id == "medico@oneepis.local"
    assert passive_event.correlation_id == "passive-abac-unit-001"
    assert passive_event.request_method == "GET"
    assert passive_event.request_path == f"/api/v1/patients/{patient_id}/record"
    assert passive_event.extra_data == {
        "mode": "passive",
        "source_action": "record.read",
        "policy": "contextual_abac",
        "runtime_enforced": False,
        "allowed": True,
        "would_deny_if_enforced": True,
        "denial_reason_count": 4,
        "denial_reason_keys": [
            "institution_or_tenant",
            "care_team_or_service",
            "active_care_relationship_or_access_reason",
            "audited_break_glass",
        ],
        "patient_scope": {
            "status": "none",
            "matched_care_team_count": 0,
            "actor_active_care_team_count": 0,
            "patient_active_care_team_count": 0,
            "runtime_enforced": False,
        },
        "metadata_retention": "requirement_keys_only",
    }


def test_patient_scoped_read_records_minimized_resolved_patient_scope() -> None:
    session = _session()
    patient = create_abac_patient(session)
    care_team = create_care_team(session)
    assign_actor_to_care_team(
        session,
        actor_id="medico@oneepis.local",
        care_team=care_team,
        membership_reason="texto libre de cobertura que no debe quedar",
    )
    assign_patient_to_care_team(
        session,
        patient=patient,
        care_team=care_team,
        relationship_reason="texto libre clinico que no debe quedar",
    )
    set_audit_request_context(
        AuditRequestContext(
            correlation_id="passive-abac-unit-002",
            request_method="GET",
            request_path=f"/api/v1/patients/{patient.id}",
        )
    )
    try:
        record_patient_scoped_read(
            session,
            patient_id=patient.id,
            actor_id="medico@oneepis.local",
            action="patient.read",
        )
    finally:
        clear_audit_request_context()

    passive_event = session.scalars(
        select(AuditEvent)
        .where(AuditEvent.action == PASSIVE_ACCESS_CONTEXT_DECISION_ACTION)
        .order_by(AuditEvent.created_at.asc())
    ).one()

    assert passive_event.extra_data["patient_scope"] == {
        "status": "resolved",
        "matched_care_team_count": 1,
        "actor_active_care_team_count": 1,
        "patient_active_care_team_count": 1,
        "runtime_enforced": False,
    }
    assert str(care_team.id) not in repr(passive_event.extra_data)
    assert "texto libre de cobertura" not in repr(passive_event.extra_data)
    assert "texto libre clinico" not in repr(passive_event.extra_data)


def _session() -> Session:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    testing_session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    return testing_session()
