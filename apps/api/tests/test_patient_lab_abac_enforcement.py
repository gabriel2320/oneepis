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
