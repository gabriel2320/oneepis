from __future__ import annotations

import uuid
from collections.abc import Iterator
from contextlib import contextmanager

import pytest
from access_boundary_helpers import (
    assign_actor_to_care_team,
    assign_patient_to_care_team,
    create_care_team,
)
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from oneepis_api.api.v1.routes import patient_vitals
from oneepis_api.core.config import Settings, get_settings
from oneepis_api.db.session import get_session
from oneepis_api.main import app
from oneepis_api.models.clinical_record import VitalSign
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


def test_patient_vitals_list_accepts_before_measured_at_cursor(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient_for_permissions(client, auth)
    for index, measured_at in enumerate(
        (
            "2026-06-20T12:00:00Z",
            "2026-06-21T12:00:00Z",
            "2026-06-22T12:00:00Z",
        ),
        start=1,
    ):
        response = client.post(
            f"/api/v1/patients/{patient_id}/vital-signs",
            headers=auth,
            json={
                "measured_at": measured_at,
                "heart_rate_bpm": 80 + index,
            },
        )
        assert response.status_code == 201

    first_page = client.get(
        f"/api/v1/patients/{patient_id}/vital-signs",
        headers=auth,
        params={"limit": 2},
    )
    assert first_page.status_code == 200
    first_items = first_page.json()
    assert [item["heart_rate_bpm"] for item in first_items] == [83, 82]

    next_page = client.get(
        f"/api/v1/patients/{patient_id}/vital-signs",
        headers=auth,
        params={
            "limit": 2,
            "before_measured_at": first_items[-1]["measured_at"],
        },
    )

    assert next_page.status_code == 200
    next_items = next_page.json()
    assert [item["heart_rate_bpm"] for item in next_items] == [81]
    assert {item["id"] for item in first_items}.isdisjoint(
        {item["id"] for item in next_items}
    )


def test_patient_vitals_create_rolls_back_when_audit_write_fails(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient_for_permissions(client, auth)

    def fail_audit_write(*args, **kwargs) -> None:
        raise RuntimeError("audit write failed")

    monkeypatch.setattr(patient_vitals, "record_audit_event", fail_audit_write)

    with pytest.raises(RuntimeError, match="audit write failed"):
        client.post(
            f"/api/v1/patients/{patient_id}/vital-signs",
            headers=auth,
            json={
                "measured_at": "2026-06-21T12:00:00Z",
                "systolic_bp": 120,
                "heart_rate_bpm": 80,
            },
        )

    with _test_session() as session:
        persisted_vital = session.scalar(
            select(VitalSign).where(VitalSign.patient_id == uuid.UUID(patient_id))
        )
    assert persisted_vital is None


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
