from fastapi.testclient import TestClient


def test_appointments_are_persisted_listed_and_audited(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
    audit_events_for_patient,
) -> None:
    auth = auth_headers(client)
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
        headers=auth,
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
    updated_audit = next(item for item in events if item["action"] == "appointment.updated")
    assert updated_audit["extra_data"]["after"] == {
        "notes": "Paciente en sala de espera.",
        "status": "check_in",
    }


def test_appointment_permissions_and_patient_ownership(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
) -> None:
    auth = auth_headers(client)
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
    list_response = client.get("/api/v1/appointments", headers=readonly_auth)
    assert list_response.status_code == 200

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
