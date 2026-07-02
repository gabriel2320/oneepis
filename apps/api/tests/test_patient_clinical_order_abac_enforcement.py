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


def test_patient_clinical_orders_abac_denies_without_active_relationship(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
    audit_events_for_patient,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient_for_permissions(client, auth)
    _create_order(client, auth, patient_id)
    _enable_development_abac_enforcement()

    response = client.get(f"/api/v1/patients/{patient_id}/clinical-orders", headers=auth)

    assert response.status_code == 403
    actions = [event["action"] for event in audit_events_for_patient(patient_id)]
    assert actions.count("access_context.denied") == 1
    assert "clinical_orders.read" not in actions


def test_patient_clinical_orders_abac_allows_active_relationship(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient_for_permissions(client, auth)
    order = _create_order(client, auth, patient_id)
    _assign_patient_scope(
        patient_id=patient_id,
        actor_id="medico@oneepis.local",
    )
    _enable_development_abac_enforcement()

    response = client.get(f"/api/v1/patients/{patient_id}/clinical-orders", headers=auth)

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [order["id"]]


def test_patient_clinical_orders_write_abac_denies_without_active_relationship(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
    audit_events_for_patient,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient_for_permissions(client, auth)
    encounter = _create_encounter(client, auth, patient_id)
    order = _create_order_for_encounter(client, auth, patient_id, encounter["id"])
    unknown_order_id = uuid.uuid4()
    _enable_development_abac_enforcement()

    create_response = client.post(
        f"/api/v1/patients/{patient_id}/clinical-orders",
        headers=auth,
        json={
            "encounter_id": encounter["id"],
            "kind": "lab",
            "ordered_at": "2026-06-20T11:00:00Z",
            "title": "Orden denegada",
            "order_text": "No debe crear sin relacion activa.",
        },
    )
    update_response = client.patch(
        f"/api/v1/patients/{patient_id}/clinical-orders/{order['id']}",
        headers=auth,
        json={"title": "No debe actualizar sin relacion activa."},
    )
    missing_update_response = client.patch(
        f"/api/v1/patients/{patient_id}/clinical-orders/{unknown_order_id}",
        headers=auth,
        json={"title": "No debe revelar existencia."},
    )
    cancel_response = client.patch(
        f"/api/v1/patients/{patient_id}/clinical-orders/{order['id']}",
        headers=auth,
        json={"status": "cancelled"},
    )

    assert create_response.status_code == 403
    assert update_response.status_code == 403
    assert missing_update_response.status_code == 403
    assert cancel_response.status_code == 403
    actions = [event["action"] for event in audit_events_for_patient(patient_id)]
    assert actions.count("access_context.denied") == 4
    assert actions.count("clinical_order.created") == 1
    assert "clinical_order.updated" not in actions


def test_patient_clinical_orders_write_abac_allows_active_relationship(
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

    create_response = client.post(
        f"/api/v1/patients/{patient_id}/clinical-orders",
        headers=auth,
        json={
            "encounter_id": encounter["id"],
            "kind": "lab",
            "ordered_at": "2026-06-20T10:00:00Z",
            "title": "Orden permitida",
            "order_text": "Solicitar control en borrador.",
        },
    )
    order_id = create_response.json()["id"]
    update_response = client.patch(
        f"/api/v1/patients/{patient_id}/clinical-orders/{order_id}",
        headers=auth,
        json={"title": "Orden permitida actualizada"},
    )
    cancel_response = client.patch(
        f"/api/v1/patients/{patient_id}/clinical-orders/{order_id}",
        headers=auth,
        json={"status": "cancelled"},
    )

    assert create_response.status_code == 201
    assert create_response.json()["status"] == "draft"
    assert update_response.status_code == 200
    assert update_response.json()["title"] == "Orden permitida actualizada"
    assert cancel_response.status_code == 200
    assert cancel_response.json()["status"] == "cancelled"


def test_patient_clinical_orders_write_abac_allows_admin_breakout(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
) -> None:
    auth = auth_headers(client)
    admin_auth = auth_headers(client, email="admin@oneepis.local", password="admin")
    patient_id = create_patient_for_permissions(client, auth)
    encounter = _create_encounter(client, auth, patient_id)
    _enable_development_abac_enforcement()

    response = client.post(
        f"/api/v1/patients/{patient_id}/clinical-orders",
        headers=admin_auth,
        json={
            "encounter_id": encounter["id"],
            "kind": "lab",
            "ordered_at": "2026-06-20T10:00:00Z",
            "title": "Orden admin",
            "order_text": "Solicitar control en borrador.",
        },
    )

    assert response.status_code == 201
    assert response.json()["created_by"] == "admin@oneepis.local"


def _create_order(client: TestClient, auth: dict[str, str], patient_id: str) -> dict:
    encounter = _create_encounter(client, auth, patient_id)
    return _create_order_for_encounter(client, auth, patient_id, encounter["id"])


def _create_encounter(client: TestClient, auth: dict[str, str], patient_id: str) -> dict:
    response = client.post(
        f"/api/v1/patients/{patient_id}/encounters",
        headers=auth,
        json={
            "type": "ambulatory",
            "status": "in_progress",
            "reason": "Control ABAC de orden",
            "started_at": "2026-06-20T09:00:00Z",
        },
    )
    assert response.status_code == 201
    return response.json()


def _create_order_for_encounter(
    client: TestClient,
    auth: dict[str, str],
    patient_id: str,
    encounter_id: str,
) -> dict:
    response = client.post(
        f"/api/v1/patients/{patient_id}/clinical-orders",
        headers=auth,
        json={
            "encounter_id": encounter_id,
            "kind": "lab",
            "ordered_at": "2026-06-20T10:00:00Z",
            "title": "Hemograma ABAC",
            "order_text": "Solicitar hemograma en borrador.",
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
