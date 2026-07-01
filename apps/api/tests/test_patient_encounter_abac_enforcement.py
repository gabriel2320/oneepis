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


def test_patient_encounters_abac_denies_without_active_relationship(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
    audit_events_for_patient,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient_for_permissions(client, auth)
    encounter = _create_encounter(client, auth, patient_id)
    _enable_development_abac_enforcement()

    list_response = client.get(f"/api/v1/patients/{patient_id}/encounters", headers=auth)
    detail_response = client.get(
        f"/api/v1/patients/{patient_id}/encounters/{encounter['id']}",
        headers=auth,
    )

    assert list_response.status_code == 403
    assert detail_response.status_code == 403
    actions = [event["action"] for event in audit_events_for_patient(patient_id)]
    assert actions.count("access_context.denied") == 2
    assert "encounters.read" not in actions
    assert "encounter.read" not in actions


def test_patient_encounters_abac_allows_active_relationship(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient_for_permissions(client, auth)
    encounter = _create_encounter(client, auth, patient_id)
    _assign_patient_scope(
        patient_id=patient_id,
        actor_id="medico@oneepis.local",
    )
    _enable_development_abac_enforcement()

    list_response = client.get(f"/api/v1/patients/{patient_id}/encounters", headers=auth)
    detail_response = client.get(
        f"/api/v1/patients/{patient_id}/encounters/{encounter['id']}",
        headers=auth,
    )

    assert list_response.status_code == 200
    assert [item["id"] for item in list_response.json()] == [encounter["id"]]
    assert detail_response.status_code == 200
    assert detail_response.json()["id"] == encounter["id"]


def test_patient_encounters_write_abac_denies_without_active_relationship(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
    audit_events_for_patient,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient_for_permissions(client, auth)
    encounter = _create_encounter(client, auth, patient_id)
    unknown_encounter_id = uuid.uuid4()
    _enable_development_abac_enforcement()

    create_response = client.post(
        f"/api/v1/patients/{patient_id}/encounters",
        headers=auth,
        json=_encounter_payload(reason="Intento sin relacion activa"),
    )
    update_response = client.patch(
        f"/api/v1/patients/{patient_id}/encounters/{encounter['id']}",
        headers=auth,
        json={"status": "completed", "ended_at": "2026-06-20T10:00:00Z"},
    )
    missing_update_response = client.patch(
        f"/api/v1/patients/{patient_id}/encounters/{unknown_encounter_id}",
        headers=auth,
        json={"status": "completed", "ended_at": "2026-06-20T10:00:00Z"},
    )
    cancel_response = client.delete(
        f"/api/v1/patients/{patient_id}/encounters/{encounter['id']}",
        headers=auth,
    )

    assert create_response.status_code == 403
    assert update_response.status_code == 403
    assert missing_update_response.status_code == 403
    assert cancel_response.status_code == 403
    actions = [event["action"] for event in audit_events_for_patient(patient_id)]
    assert actions.count("access_context.denied") == 4
    assert actions.count("encounter.created") == 1
    assert "encounter.updated" not in actions
    assert "encounter.cancelled" not in actions


def test_patient_encounters_write_abac_allows_active_relationship(
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
        f"/api/v1/patients/{patient_id}/encounters",
        headers=auth,
        json=_encounter_payload(reason="Permitido por relacion activa"),
    )
    encounter_id = create_response.json()["id"]
    update_response = client.patch(
        f"/api/v1/patients/{patient_id}/encounters/{encounter_id}",
        headers=auth,
        json={"status": "completed", "ended_at": "2026-06-20T10:00:00Z"},
    )
    cancel_response = client.delete(
        f"/api/v1/patients/{patient_id}/encounters/{encounter_id}",
        headers=auth,
    )

    assert create_response.status_code == 201
    assert update_response.status_code == 200
    assert update_response.json()["status"] == "completed"
    assert cancel_response.status_code == 204


def test_patient_encounters_write_abac_allows_admin_breakout(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
) -> None:
    auth = auth_headers(client)
    admin_auth = auth_headers(client, email="admin@oneepis.local", password="admin")
    patient_id = create_patient_for_permissions(client, auth)
    _enable_development_abac_enforcement()

    response = client.post(
        f"/api/v1/patients/{patient_id}/encounters",
        headers=admin_auth,
        json=_encounter_payload(reason="Breakout admin/dev"),
    )

    assert response.status_code == 201


def _create_encounter(client: TestClient, auth: dict[str, str], patient_id: str) -> dict:
    response = client.post(
        f"/api/v1/patients/{patient_id}/encounters",
        headers=auth,
        json=_encounter_payload(reason="Control ABAC de encuentro"),
    )
    assert response.status_code == 201
    return response.json()


def _encounter_payload(*, reason: str) -> dict[str, str]:
    return {
        "type": "ambulatory",
        "reason": reason,
        "started_at": "2026-06-20T09:00:00Z",
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
