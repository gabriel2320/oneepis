import uuid
from collections.abc import Iterator
from contextlib import contextmanager

from access_boundary_helpers import (
    assign_actor_to_care_team,
    assign_patient_to_care_team,
    create_care_team,
)
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from oneepis_api.core.config import Settings, get_settings
from oneepis_api.db.session import get_session
from oneepis_api.main import app
from oneepis_api.models.audit import AuditEvent
from oneepis_api.models.patient import Patient


def test_appointments_are_persisted_listed_and_audited(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
    audit_events_for_patient,
) -> None:
    auth = auth_headers(client)
    admin_auth = auth_headers(client, email="admin@oneepis.local", password="admin")
    patient_id = create_patient_for_permissions(client, auth)

    create_response = client.post(
        f"/api/v1/patients/{patient_id}/appointments",
        headers=auth,
        json={
            "starts_at": "2026-06-24T09:00:00Z",
            "ends_at": "2026-06-24T09:30:00Z",
            "reason": "Control ambulatorio",
            "location_label": "Box 1",
            "clinician_label": "Equipo demo",
        },
    )
    assert create_response.status_code == 201
    appointment = create_response.json()
    assert appointment["patient_id"] == patient_id
    assert appointment["status"] == "scheduled"
    assert appointment["created_by"] == "medico@oneepis.local"

    list_response = client.get(
        "/api/v1/appointments?date_from=2026-06-24T00:00:00Z&date_to=2026-06-25T00:00:00Z",
        headers=admin_auth,
    )
    assert list_response.status_code == 200
    assert [item["id"] for item in list_response.json()] == [appointment["id"]]

    patient_list_response = client.get(
        f"/api/v1/patients/{patient_id}/appointments",
        headers=auth,
    )
    assert patient_list_response.status_code == 200
    assert patient_list_response.json()[0]["id"] == appointment["id"]

    update_response = client.patch(
        f"/api/v1/patients/{patient_id}/appointments/{appointment['id']}",
        headers=auth,
        json={"status": "check_in", "notes": "Paciente en sala de espera."},
    )
    assert update_response.status_code == 200
    assert update_response.json()["status"] == "check_in"

    invalid_time = client.patch(
        f"/api/v1/patients/{patient_id}/appointments/{appointment['id']}",
        headers=auth,
        json={"ends_at": "2026-06-24T08:30:00Z"},
    )
    assert invalid_time.status_code == 422

    events = audit_events_for_patient(patient_id)
    created_audit = next(item for item in events if item["action"] == "appointment.created")
    assert created_audit["entity_id"] == appointment["id"]
    assert created_audit["extra_data"]["after"] == {
        "ends_at": "2026-06-24T09:30:00+00:00",
        "patient_id": patient_id,
        "starts_at": "2026-06-24T09:00:00+00:00",
        "status": "scheduled",
    }
    updated_audit = next(item for item in events if item["action"] == "appointment.updated")
    assert updated_audit["extra_data"]["fields"] == ["notes", "status"]
    assert updated_audit["extra_data"]["before"] == {"status": "scheduled"}
    assert updated_audit["extra_data"]["after"] == {"status": "check_in"}
    appointment_audit_payload = str([created_audit["extra_data"], updated_audit["extra_data"]])
    assert "Control ambulatorio" not in appointment_audit_payload
    assert "Box 1" not in appointment_audit_payload
    assert "Equipo demo" not in appointment_audit_payload
    assert "Paciente en sala" not in appointment_audit_payload


def test_appointment_permissions_and_patient_ownership(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
) -> None:
    auth = auth_headers(client)
    admin_auth = auth_headers(client, email="admin@oneepis.local", password="admin")
    first_patient_id = create_patient_for_permissions(client, auth)
    second_patient_id = create_patient_for_permissions(client, auth)
    appointment = client.post(
        f"/api/v1/patients/{first_patient_id}/appointments",
        headers=auth,
        json={
            "starts_at": "2026-06-24T10:00:00Z",
            "reason": "Control de permisos",
        },
    ).json()

    readonly_auth = auth_headers(client, email="lector@oneepis.local", password="lector")
    readonly_list_response = client.get("/api/v1/appointments", headers=readonly_auth)
    medico_list_response = client.get("/api/v1/appointments", headers=auth)
    assert readonly_list_response.status_code == 403
    assert medico_list_response.status_code == 403
    assert _audit_actions("appointments_index.read") == []

    admin_list_response = client.get("/api/v1/appointments", headers=admin_auth)
    assert admin_list_response.status_code == 200
    assert [item["id"] for item in admin_list_response.json()] == [appointment["id"]]
    assert _audit_actions("appointments_index.read") == ["appointments_index.read"]

    readonly_create = client.post(
        f"/api/v1/patients/{first_patient_id}/appointments",
        headers=readonly_auth,
        json={
            "starts_at": "2026-06-24T11:00:00Z",
            "reason": "No permitido",
        },
    )
    assert readonly_create.status_code == 403

    cross_patient = client.get(
        f"/api/v1/patients/{second_patient_id}/appointments/{appointment['id']}",
        headers=auth,
    )
    assert cross_patient.status_code == 404


def test_patient_appointments_abac_enforcement_denies_without_active_relationship(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
    audit_events_for_patient,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient_for_permissions(client, auth)
    appointment = _create_appointment(client, auth, patient_id)
    _enable_development_abac_enforcement()

    list_response = client.get(f"/api/v1/patients/{patient_id}/appointments", headers=auth)
    detail_response = client.get(
        f"/api/v1/patients/{patient_id}/appointments/{appointment['id']}",
        headers=auth,
    )

    assert list_response.status_code == 403
    assert detail_response.status_code == 403
    events = audit_events_for_patient(patient_id)
    actions = [event["action"] for event in events]
    assert actions.count("access_context.denied") == 2
    assert "appointments.read" not in actions
    assert "appointment.read" not in actions


def test_patient_appointments_abac_enforcement_allows_active_relationship(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient_for_permissions(client, auth)
    appointment = _create_appointment(client, auth, patient_id)
    _assign_patient_scope(
        patient_id=patient_id,
        actor_id="medico@oneepis.local",
    )
    _enable_development_abac_enforcement()

    list_response = client.get(f"/api/v1/patients/{patient_id}/appointments", headers=auth)
    detail_response = client.get(
        f"/api/v1/patients/{patient_id}/appointments/{appointment['id']}",
        headers=auth,
    )

    assert list_response.status_code == 200
    assert [item["id"] for item in list_response.json()] == [appointment["id"]]
    assert detail_response.status_code == 200
    assert detail_response.json()["id"] == appointment["id"]


def test_patient_appointments_write_abac_denies_without_active_relationship(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
    audit_events_for_patient,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient_for_permissions(client, auth)
    appointment = _create_appointment(client, auth, patient_id)
    unknown_appointment_id = uuid.uuid4()
    _enable_development_abac_enforcement()

    create_response = client.post(
        f"/api/v1/patients/{patient_id}/appointments",
        headers=auth,
        json=_appointment_payload(reason="Agenda sin relacion activa"),
    )
    update_response = client.patch(
        f"/api/v1/patients/{patient_id}/appointments/{appointment['id']}",
        headers=auth,
        json={"status": "check_in"},
    )
    missing_update_response = client.patch(
        f"/api/v1/patients/{patient_id}/appointments/{unknown_appointment_id}",
        headers=auth,
        json={"status": "check_in"},
    )

    assert create_response.status_code == 403
    assert update_response.status_code == 403
    assert missing_update_response.status_code == 403
    actions = [event["action"] for event in audit_events_for_patient(patient_id)]
    assert actions.count("access_context.denied") == 3
    assert actions.count("appointment.created") == 1
    assert "appointment.updated" not in actions


def test_patient_appointments_write_abac_allows_active_relationship(
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
        f"/api/v1/patients/{patient_id}/appointments",
        headers=auth,
        json=_appointment_payload(reason="Agenda permitida por relacion activa"),
    )
    appointment_id = create_response.json()["id"]
    update_response = client.patch(
        f"/api/v1/patients/{patient_id}/appointments/{appointment_id}",
        headers=auth,
        json={"status": "check_in"},
    )

    assert create_response.status_code == 201
    assert update_response.status_code == 200
    assert update_response.json()["status"] == "check_in"


def test_patient_appointments_write_abac_allows_admin_breakout(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
) -> None:
    auth = auth_headers(client)
    admin_auth = auth_headers(client, email="admin@oneepis.local", password="admin")
    patient_id = create_patient_for_permissions(client, auth)
    _enable_development_abac_enforcement()

    response = client.post(
        f"/api/v1/patients/{patient_id}/appointments",
        headers=admin_auth,
        json=_appointment_payload(reason="Agenda creada por breakout admin"),
    )

    assert response.status_code == 201


def _create_appointment(client: TestClient, auth: dict[str, str], patient_id: str) -> dict:
    response = client.post(
        f"/api/v1/patients/{patient_id}/appointments",
        headers=auth,
        json=_appointment_payload(reason="Control ABAC appointments"),
    )
    assert response.status_code == 201
    return response.json()


def _appointment_payload(*, reason: str) -> dict[str, str]:
    return {
        "starts_at": "2026-06-24T12:00:00Z",
        "reason": reason,
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


def _audit_actions(action: str) -> list[str]:
    with _test_session() as session:
        return [
            event.action
            for event in session.scalars(select(AuditEvent).where(AuditEvent.action == action))
        ]


@contextmanager
def _test_session() -> Iterator[Session]:
    session_provider = app.dependency_overrides[get_session]
    session_iterator = session_provider()
    session = next(session_iterator)
    try:
        yield session
    finally:
        session_iterator.close()
