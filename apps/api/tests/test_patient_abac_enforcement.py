import uuid
from collections.abc import Iterator
from contextlib import contextmanager

from access_boundary_helpers import (
    assign_actor_to_care_team,
    assign_patient_to_care_team,
    create_care_team,
)
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from oneepis_api.core.config import Settings, get_settings
from oneepis_api.db.session import get_session
from oneepis_api.main import app
from oneepis_api.models.patient import Patient


def test_get_patient_abac_enforcement_denies_without_active_relationship(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
    audit_events_for_patient,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient_for_permissions(client, auth)
    _enable_development_abac_enforcement()

    response = client.get(f"/api/v1/patients/{patient_id}", headers=auth)

    assert response.status_code == 403
    assert response.json() == {
        "detail": "Patient access is outside the active care relationship."
    }
    events = audit_events_for_patient(patient_id)
    denied_event = next(event for event in events if event["action"] == "access_context.denied")
    assert denied_event["actor_id"] == "medico@oneepis.local"
    assert denied_event["extra_data"] == {
        "policy": "contextual_abac",
        "runtime_enforced": True,
        "reason_keys": ["active_care_relationship_or_access_reason"],
        "metadata_retention": "requirement_keys_only",
    }
    assert "patient.read" not in [event["action"] for event in events]


def test_get_patient_abac_enforcement_allows_active_relationship(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient_for_permissions(client, auth)
    _assign_patient_scope(
        patient_id=patient_id,
        actor_id="medico@oneepis.local",
    )
    _enable_development_abac_enforcement()

    response = client.get(f"/api/v1/patients/{patient_id}", headers=auth)

    assert response.status_code == 200
    assert response.json()["id"] == patient_id


def test_get_patient_abac_enforcement_keeps_admin_breakout_explicit(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
) -> None:
    patient_id = create_patient_for_permissions(client, auth_headers(client))
    admin_auth = auth_headers(client, email="admin@oneepis.local", password="admin")
    _enable_development_abac_enforcement()

    response = client.get(f"/api/v1/patients/{patient_id}", headers=admin_auth)

    assert response.status_code == 200
    assert response.json()["id"] == patient_id


def _enable_development_abac_enforcement() -> None:
    app.dependency_overrides[get_settings] = lambda: Settings(
        ai_provider="local_rules",
        abac_enforcement_enabled=True,
    )


def _assign_patient_scope(*, patient_id: str, actor_id: str) -> None:
    with _test_session() as session:
        patient = session.get(Patient, uuid.UUID(patient_id))
        assert patient is not None
        care_team = create_care_team(session)
        assign_actor_to_care_team(
            session,
            actor_id=actor_id,
            care_team=care_team,
        )
        assign_patient_to_care_team(
            session,
            patient=patient,
            care_team=care_team,
        )


@contextmanager
def _test_session() -> Iterator[Session]:
    session_provider = app.dependency_overrides[get_session]
    session_iterator = session_provider()
    session = next(session_iterator)
    try:
        yield session
    finally:
        session_iterator.close()
