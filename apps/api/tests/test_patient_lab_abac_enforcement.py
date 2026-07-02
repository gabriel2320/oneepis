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


def test_patient_labs_abac_denies_without_active_relationship(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
    audit_events_for_patient,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient_for_permissions(client, auth)
    panel = _create_lab_panel(client, auth, patient_id)
    result = panel["results"][0]
    _enable_development_abac_enforcement()

    list_response = client.get(f"/api/v1/patients/{patient_id}/lab-panels", headers=auth)
    panel_response = client.get(
        f"/api/v1/patients/{patient_id}/lab-panels/{panel['id']}",
        headers=auth,
    )
    result_response = client.get(
        f"/api/v1/patients/{patient_id}/lab-panels/{panel['id']}/results/{result['id']}",
        headers=auth,
    )

    assert list_response.status_code == 403
    assert panel_response.status_code == 403
    assert result_response.status_code == 403
    actions = [event["action"] for event in audit_events_for_patient(patient_id)]
    assert actions.count("access_context.denied") == 3
    assert "lab_panels.read" not in actions
    assert "lab_panel.read" not in actions
    assert "lab_result.read" not in actions


def test_patient_labs_abac_allows_active_relationship(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient_for_permissions(client, auth)
    panel = _create_lab_panel(client, auth, patient_id)
    result = panel["results"][0]
    _assign_patient_scope(
        patient_id=patient_id,
        actor_id="medico@oneepis.local",
    )
    _enable_development_abac_enforcement()

    list_response = client.get(f"/api/v1/patients/{patient_id}/lab-panels", headers=auth)
    panel_response = client.get(
        f"/api/v1/patients/{patient_id}/lab-panels/{panel['id']}",
        headers=auth,
    )
    result_response = client.get(
        f"/api/v1/patients/{patient_id}/lab-panels/{panel['id']}/results/{result['id']}",
        headers=auth,
    )

    assert list_response.status_code == 200
    assert [item["id"] for item in list_response.json()] == [panel["id"]]
    assert panel_response.status_code == 200
    assert panel_response.json()["id"] == panel["id"]
    assert result_response.status_code == 200
    assert result_response.json()["id"] == result["id"]


def test_patient_labs_write_abac_denies_without_active_relationship(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
    audit_events_for_patient,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient_for_permissions(client, auth)
    panel = _create_lab_panel(client, auth, patient_id)
    result = panel["results"][0]
    unknown_panel_id = uuid.uuid4()
    unknown_result_id = uuid.uuid4()
    _enable_development_abac_enforcement()

    create_response = client.post(
        f"/api/v1/patients/{patient_id}/lab-panels",
        headers=auth,
        json={
            "occurred_at": "2026-06-21T09:00:00Z",
            "panel_name": "Panel denegado",
            "results": [
                {
                    "code": "hb",
                    "name": "Hemoglobina",
                    "value": "13.8",
                    "numeric_value": "13.8",
                    "unit": "g/dL",
                }
            ],
        },
    )
    update_panel_response = client.patch(
        f"/api/v1/patients/{patient_id}/lab-panels/{panel['id']}",
        headers=auth,
        json={"summary": "No permitido"},
    )
    missing_panel_response = client.patch(
        f"/api/v1/patients/{patient_id}/lab-panels/{unknown_panel_id}",
        headers=auth,
        json={"summary": "No revelar existencia"},
    )
    update_result_response = client.patch(
        f"/api/v1/patients/{patient_id}/lab-panels/{panel['id']}/results/{result['id']}",
        headers=auth,
        json={"status": "entered_in_error"},
    )
    missing_result_response = client.patch(
        f"/api/v1/patients/{patient_id}/lab-panels/{panel['id']}/results/{unknown_result_id}",
        headers=auth,
        json={"status": "entered_in_error"},
    )

    assert create_response.status_code == 403
    assert update_panel_response.status_code == 403
    assert missing_panel_response.status_code == 403
    assert update_result_response.status_code == 403
    assert missing_result_response.status_code == 403
    actions = [event["action"] for event in audit_events_for_patient(patient_id)]
    assert actions.count("access_context.denied") == 5
    assert actions.count("lab_panel.created") == 1
    assert "lab_panel.updated" not in actions
    assert "lab_result.updated" not in actions


def test_patient_labs_write_abac_allows_active_relationship(
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
        f"/api/v1/patients/{patient_id}/lab-panels",
        headers=auth,
        json={
            "occurred_at": "2026-06-21T09:00:00Z",
            "panel_name": "Panel permitido",
            "results": [
                {
                    "code": "hb",
                    "name": "Hemoglobina",
                    "value": "13.8",
                    "numeric_value": "13.8",
                    "unit": "g/dL",
                }
            ],
        },
    )
    panel = create_response.json()
    result = panel["results"][0]
    update_panel_response = client.patch(
        f"/api/v1/patients/{patient_id}/lab-panels/{panel['id']}",
        headers=auth,
        json={"summary": "Control permitido"},
    )
    update_result_response = client.patch(
        f"/api/v1/patients/{patient_id}/lab-panels/{panel['id']}/results/{result['id']}",
        headers=auth,
        json={"status": "entered_in_error"},
    )

    assert create_response.status_code == 201
    assert update_panel_response.status_code == 200
    assert update_panel_response.json()["summary"] == "Control permitido"
    assert update_result_response.status_code == 200
    assert update_result_response.json()["status"] == "entered_in_error"


def test_patient_labs_write_abac_allows_admin_breakout(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
) -> None:
    auth = auth_headers(client)
    admin_auth = auth_headers(client, email="admin@oneepis.local", password="admin")
    patient_id = create_patient_for_permissions(client, auth)
    _enable_development_abac_enforcement()

    response = client.post(
        f"/api/v1/patients/{patient_id}/lab-panels",
        headers=admin_auth,
        json={
            "occurred_at": "2026-06-21T09:00:00Z",
            "panel_name": "Panel admin",
            "results": [
                {
                    "code": "hb",
                    "name": "Hemoglobina",
                    "value": "13.8",
                    "numeric_value": "13.8",
                    "unit": "g/dL",
                }
            ],
        },
    )

    assert response.status_code == 201


def _create_lab_panel(client: TestClient, auth: dict[str, str], patient_id: str) -> dict:
    response = client.post(
        f"/api/v1/patients/{patient_id}/lab-panels",
        headers=auth,
        json={
            "occurred_at": "2026-06-20T09:00:00Z",
            "panel_name": "Panel ABAC laboratorio",
            "results": [
                {
                    "code": "hb",
                    "name": "Hemoglobina",
                    "value": "13.4",
                    "numeric_value": "13.4",
                    "unit": "g/dL",
                }
            ],
        },
    )
    assert response.status_code == 201
    return response.json()


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
