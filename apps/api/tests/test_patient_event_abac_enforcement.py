from __future__ import annotations

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


def test_patient_events_abac_denies_without_active_relationship(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
    audit_events_for_patient,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient_for_permissions(client, auth)
    event = _create_event(client, auth, patient_id)
    _enable_development_abac_enforcement()

    list_response = client.get(f"/api/v1/patients/{patient_id}/clinical-events", headers=auth)
    detail_response = client.get(
        f"/api/v1/patients/{patient_id}/clinical-events/{event['id']}",
        headers=auth,
    )
    timeline_response = client.get(f"/api/v1/patients/{patient_id}/timeline", headers=auth)

    assert list_response.status_code == 403
    assert detail_response.status_code == 403
    assert timeline_response.status_code == 403
    actions = [event["action"] for event in audit_events_for_patient(patient_id)]
    assert actions.count("access_context.denied") == 3
    assert "clinical_events.read" not in actions
    assert "clinical_event.read" not in actions
    assert "timeline.read" not in actions


def test_patient_events_abac_allows_active_relationship(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient_for_permissions(client, auth)
    event = _create_event(client, auth, patient_id)
    _assign_patient_scope(
        patient_id=patient_id,
        actor_id="medico@oneepis.local",
    )
    _enable_development_abac_enforcement()

    list_response = client.get(f"/api/v1/patients/{patient_id}/clinical-events", headers=auth)
    detail_response = client.get(
        f"/api/v1/patients/{patient_id}/clinical-events/{event['id']}",
        headers=auth,
    )
    timeline_response = client.get(f"/api/v1/patients/{patient_id}/timeline", headers=auth)

    assert list_response.status_code == 200
    assert [item["id"] for item in list_response.json()] == [event["id"]]
    assert detail_response.status_code == 200
    assert detail_response.json()["id"] == event["id"]
    assert timeline_response.status_code == 200
    assert [item["id"] for item in timeline_response.json()["events"]] == [event["id"]]


def test_patient_events_write_abac_denies_without_active_relationship(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
    audit_events_for_patient,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient_for_permissions(client, auth)
    event = _create_event(client, auth, patient_id)
    unknown_event_id = uuid.uuid4()
    _enable_development_abac_enforcement()

    create_response = client.post(
        f"/api/v1/patients/{patient_id}/clinical-events",
        headers=auth,
        json=_event_payload(summary="Evento sin relacion activa"),
    )
    update_response = client.patch(
        f"/api/v1/patients/{patient_id}/clinical-events/{event['id']}",
        headers=auth,
        json={"summary": "No debe actualizarse"},
    )
    missing_update_response = client.patch(
        f"/api/v1/patients/{patient_id}/clinical-events/{unknown_event_id}",
        headers=auth,
        json={"summary": "No debe revelar existencia"},
    )

    assert create_response.status_code == 403
    assert update_response.status_code == 403
    assert missing_update_response.status_code == 403
    actions = [event["action"] for event in audit_events_for_patient(patient_id)]
    assert actions.count("access_context.denied") == 3
    assert actions.count("clinical_event.created") == 1
    assert "clinical_event.updated" not in actions


def test_patient_events_write_abac_allows_active_relationship(
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

    create_response = client.post(
        f"/api/v1/patients/{patient_id}/clinical-events",
        headers=auth,
        json=_event_payload(summary="Evento permitido por relacion activa"),
    )
    event_id = create_response.json()["id"]
    update_response = client.patch(
        f"/api/v1/patients/{patient_id}/clinical-events/{event_id}",
        headers=auth,
        json={"summary": "Evento actualizado"},
    )

    assert create_response.status_code == 201
    assert update_response.status_code == 200
    assert update_response.json()["summary"] == "Evento actualizado"


def test_patient_events_write_abac_allows_admin_breakout(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
) -> None:
    auth = auth_headers(client)
    admin_auth = auth_headers(client, email="admin@oneepis.local", password="admin")
    patient_id = create_patient_for_permissions(client, auth)
    _enable_development_abac_enforcement()

    response = client.post(
        f"/api/v1/patients/{patient_id}/clinical-events",
        headers=admin_auth,
        json=_event_payload(summary="Evento creado por breakout admin/dev"),
    )

    assert response.status_code == 201


def _create_event(client: TestClient, auth: dict[str, str], patient_id: str) -> dict:
    response = client.post(
        f"/api/v1/patients/{patient_id}/clinical-events",
        headers=auth,
        json=_event_payload(summary="Evento ABAC"),
    )
    assert response.status_code == 201
    return response.json()


def _event_payload(*, summary: str) -> dict[str, str]:
    return {
        "event_type": "clinical_note",
        "occurred_at": "2026-06-20T09:30:00Z",
        "summary": summary,
    }


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
