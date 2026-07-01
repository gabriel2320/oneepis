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


def test_patient_vitals_abac_denies_without_active_relationship(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
    audit_events_for_patient,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient_for_permissions(client, auth)
    vital = _create_vital(client, auth, patient_id)
    _enable_development_abac_enforcement()

    list_response = client.get(f"/api/v1/patients/{patient_id}/vital-signs", headers=auth)
    detail_response = client.get(
        f"/api/v1/patients/{patient_id}/vital-signs/{vital['id']}",
        headers=auth,
    )

    assert list_response.status_code == 403
    assert detail_response.status_code == 403
    actions = [event["action"] for event in audit_events_for_patient(patient_id)]
    assert actions.count("access_context.denied") == 2
    assert "vital_signs.read" not in actions
    assert "vital_sign.read" not in actions


def test_patient_vitals_abac_allows_active_relationship(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient_for_permissions(client, auth)
    vital = _create_vital(client, auth, patient_id)
    _assign_patient_scope(
        patient_id=patient_id,
        actor_id="medico@oneepis.local",
    )
    _enable_development_abac_enforcement()

    list_response = client.get(f"/api/v1/patients/{patient_id}/vital-signs", headers=auth)
    detail_response = client.get(
        f"/api/v1/patients/{patient_id}/vital-signs/{vital['id']}",
        headers=auth,
    )

    assert list_response.status_code == 200
    assert [item["id"] for item in list_response.json()] == [vital["id"]]
    assert detail_response.status_code == 200
    assert detail_response.json()["id"] == vital["id"]


def test_patient_vitals_write_abac_denies_without_active_relationship(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
    audit_events_for_patient,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient_for_permissions(client, auth)
    vital = _create_vital(client, auth, patient_id)
    unknown_vital_id = uuid.uuid4()
    _enable_development_abac_enforcement()

    create_response = client.post(
        f"/api/v1/patients/{patient_id}/vital-signs",
        headers=auth,
        json={
            "measured_at": "2026-06-21T12:00:00Z",
            "systolic_bp": 120,
            "heart_rate_bpm": 80,
        },
    )
    update_response = client.patch(
        f"/api/v1/patients/{patient_id}/vital-signs/{vital['id']}",
        headers=auth,
        json={"heart_rate_bpm": 84},
    )
    missing_update_response = client.patch(
        f"/api/v1/patients/{patient_id}/vital-signs/{unknown_vital_id}",
        headers=auth,
        json={"heart_rate_bpm": 84},
    )
    delete_response = client.delete(
        f"/api/v1/patients/{patient_id}/vital-signs/{vital['id']}",
        headers=auth,
    )

    assert create_response.status_code == 403
    assert update_response.status_code == 403
    assert missing_update_response.status_code == 403
    assert delete_response.status_code == 403
    actions = [event["action"] for event in audit_events_for_patient(patient_id)]
    assert actions.count("access_context.denied") == 4
    assert actions.count("vital_sign.created") == 1
    assert "vital_sign.updated" not in actions
    assert "vital_sign.entered_in_error" not in actions


def test_patient_vitals_write_abac_allows_active_relationship(
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
        f"/api/v1/patients/{patient_id}/vital-signs",
        headers=auth,
        json={
            "measured_at": "2026-06-21T12:00:00Z",
            "systolic_bp": 120,
            "heart_rate_bpm": 80,
        },
    )
    vital_id = create_response.json()["id"]
    update_response = client.patch(
        f"/api/v1/patients/{patient_id}/vital-signs/{vital_id}",
        headers=auth,
        json={"heart_rate_bpm": 84},
    )
    delete_response = client.delete(
        f"/api/v1/patients/{patient_id}/vital-signs/{vital_id}",
        headers=auth,
    )

    assert create_response.status_code == 201
    assert update_response.status_code == 200
    assert update_response.json()["heart_rate_bpm"] == 84
    assert delete_response.status_code == 204


def test_patient_vitals_write_abac_allows_admin_breakout(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
) -> None:
    auth = auth_headers(client)
    admin_auth = auth_headers(client, email="admin@oneepis.local", password="admin")
    patient_id = create_patient_for_permissions(client, auth)
    _enable_development_abac_enforcement()

    response = client.post(
        f"/api/v1/patients/{patient_id}/vital-signs",
        headers=admin_auth,
        json={
            "measured_at": "2026-06-21T12:00:00Z",
            "systolic_bp": 120,
            "heart_rate_bpm": 80,
        },
    )

    assert response.status_code == 201


def _create_vital(client: TestClient, auth: dict[str, str], patient_id: str) -> dict:
    response = client.post(
        f"/api/v1/patients/{patient_id}/vital-signs",
        headers=auth,
        json={
            "measured_at": "2026-06-20T12:00:00Z",
            "systolic_bp": 110,
            "diastolic_bp": 70,
            "heart_rate_bpm": 82,
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
