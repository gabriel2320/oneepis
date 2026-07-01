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


def test_allergy_audit_uses_structural_allowlist(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
    audit_events_for_patient,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient_for_permissions(client, auth)

    create_response = client.post(
        f"/api/v1/patients/{patient_id}/allergies",
        headers=auth,
        json={
            "substance": "Alergeno sensible ALR-177",
            "reaction": "Reaccion libre sensible inicial",
            "severity": "moderate",
            "recorded_at": "2026-06-20T10:30:00Z",
        },
    )
    assert create_response.status_code == 201
    allergy_id = create_response.json()["id"]

    update_response = client.patch(
        f"/api/v1/patients/{patient_id}/allergies/{allergy_id}",
        headers=auth,
        json={
            "substance": "Alergeno sensible actualizado",
            "reaction": "Reaccion libre sensible actualizada",
            "severity": "severe",
        },
    )
    assert update_response.status_code == 200

    allergy_events = audit_events_for_patient(patient_id)
    allergy_create = next(
        item for item in allergy_events if item["action"] == "allergy.created"
    )
    assert allergy_create["extra_data"]["after"] == {
        "patient_id": patient_id,
        "recorded_at": "2026-06-20T10:30:00+00:00",
        "severity": "moderate",
        "status": "active",
    }

    allergy_update = next(
        item for item in allergy_events if item["action"] == "allergy.updated"
    )
    assert allergy_update["extra_data"]["fields"] == [
        "reaction",
        "severity",
        "substance",
    ]
    assert allergy_update["extra_data"]["before"] == {"severity": "moderate"}
    assert allergy_update["extra_data"]["after"] == {"severity": "severe"}

    audit_payload = str([allergy_create["extra_data"], allergy_update["extra_data"]])
    assert "Alergeno sensible" not in audit_payload
    assert "Reaccion libre sensible" not in audit_payload


def test_patient_allergies_abac_enforcement_denies_without_active_relationship(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
    audit_events_for_patient,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient_for_permissions(client, auth)
    allergy = _create_allergy(client, auth, patient_id)
    _enable_development_abac_enforcement()

    list_response = client.get(f"/api/v1/patients/{patient_id}/allergies", headers=auth)
    detail_response = client.get(
        f"/api/v1/patients/{patient_id}/allergies/{allergy['id']}",
        headers=auth,
    )

    assert list_response.status_code == 403
    assert detail_response.status_code == 403
    actions = [event["action"] for event in audit_events_for_patient(patient_id)]
    assert actions.count("access_context.denied") == 2
    assert "allergies.read" not in actions
    assert "allergy.read" not in actions


def test_patient_allergies_abac_enforcement_allows_active_relationship(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient_for_permissions(client, auth)
    allergy = _create_allergy(client, auth, patient_id)
    _assign_patient_scope(
        patient_id=patient_id,
        actor_id="medico@oneepis.local",
    )
    _enable_development_abac_enforcement()

    list_response = client.get(f"/api/v1/patients/{patient_id}/allergies", headers=auth)
    detail_response = client.get(
        f"/api/v1/patients/{patient_id}/allergies/{allergy['id']}",
        headers=auth,
    )

    assert list_response.status_code == 200
    assert [item["id"] for item in list_response.json()] == [allergy["id"]]
    assert detail_response.status_code == 200
    assert detail_response.json()["id"] == allergy["id"]


def _create_allergy(client: TestClient, auth: dict[str, str], patient_id: str) -> dict:
    response = client.post(
        f"/api/v1/patients/{patient_id}/allergies",
        headers=auth,
        json={
            "substance": "Alergeno ABAC allergy",
            "reaction": "Reaccion ABAC allergy",
            "severity": "moderate",
            "recorded_at": "2026-06-20T10:30:00Z",
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
