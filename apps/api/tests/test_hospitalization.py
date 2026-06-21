from fastapi.testclient import TestClient


def test_hospitalization_board_lists_active_hospitalizations_only(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
) -> None:
    auth = auth_headers(client)
    active_patient_id = create_patient_for_permissions(client, auth)
    completed_patient_id = create_patient_for_permissions(client, auth)

    active_response = client.post(
        f"/api/v1/patients/{active_patient_id}/encounters",
        headers=auth,
        json={
            "type": "hospitalization",
            "status": "in_progress",
            "reason": "Ingreso activo",
            "started_at": "2026-06-20T07:00:00Z",
            "location_label": "Sala A / Cama 1",
        },
    )
    assert active_response.status_code == 201
    active_encounter_id = active_response.json()["id"]

    completed_response = client.post(
        f"/api/v1/patients/{completed_patient_id}/encounters",
        headers=auth,
        json={
            "type": "hospitalization",
            "status": "completed",
            "reason": "Ingreso cerrado",
            "started_at": "2026-06-19T07:00:00Z",
            "ended_at": "2026-06-20T07:00:00Z",
        },
    )
    assert completed_response.status_code == 201

    ambulatory_response = client.post(
        f"/api/v1/patients/{active_patient_id}/encounters",
        headers=auth,
        json={
            "type": "ambulatory",
            "status": "in_progress",
            "reason": "Consulta activa",
            "started_at": "2026-06-20T08:00:00Z",
        },
    )
    assert ambulatory_response.status_code == 201

    board_response = client.get("/api/v1/hospitalization/active", headers=auth)
    assert board_response.status_code == 200
    payload = board_response.json()
    assert len(payload) == 1
    assert payload[0]["patient"]["id"] == active_patient_id
    assert payload[0]["encounter"]["id"] == active_encounter_id
    assert payload[0]["encounter"]["location_label"] == "Sala A / Cama 1"


def test_hospital_bed_assignment_enriches_board_and_audit(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient_for_permissions(client, auth)

    encounter_response = client.post(
        f"/api/v1/patients/{patient_id}/encounters",
        headers=auth,
        json={
            "type": "hospitalization",
            "status": "in_progress",
            "reason": "Ingreso con cama",
            "started_at": "2026-06-20T09:00:00Z",
            "location_label": "Ubicacion libre",
        },
    )
    assert encounter_response.status_code == 201
    encounter_id = encounter_response.json()["id"]

    bed_response = client.post(
        "/api/v1/hospitalization/beds",
        headers=auth,
        json={
            "ward": "Medicina",
            "room": "301",
            "bed_label": "A",
            "status": "occupied",
            "encounter_id": encounter_id,
        },
    )
    assert bed_response.status_code == 201
    bed_payload = bed_response.json()
    assert bed_payload["encounter_id"] == encounter_id

    beds_response = client.get("/api/v1/hospitalization/beds", headers=auth)
    assert beds_response.status_code == 200
    assert beds_response.json()[0]["ward"] == "Medicina"

    board_response = client.get("/api/v1/hospitalization/active", headers=auth)
    assert board_response.status_code == 200
    board_payload = board_response.json()
    assert board_payload[0]["bed"]["id"] == bed_payload["id"]
    assert board_payload[0]["bed"]["room"] == "301"

    audit_response = client.get(f"/api/v1/patients/{patient_id}/audit-events", headers=auth)
    assert audit_response.status_code == 200
    assert any(
        event["action"] == "hospital_bed.created"
        and event["extra_data"]["encounter_id"] == encounter_id
        for event in audit_response.json()
    )


def test_hospital_bed_assignment_requires_active_hospitalization(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient_for_permissions(client, auth)

    missing_encounter_response = client.post(
        "/api/v1/hospitalization/beds",
        headers=auth,
        json={
            "ward": "Medicina",
            "room": "302",
            "bed_label": "A",
            "status": "occupied",
        },
    )
    assert missing_encounter_response.status_code == 409

    ambulatory_response = client.post(
        f"/api/v1/patients/{patient_id}/encounters",
        headers=auth,
        json={
            "type": "ambulatory",
            "status": "in_progress",
            "reason": "Consulta activa",
            "started_at": "2026-06-20T10:00:00Z",
        },
    )
    assert ambulatory_response.status_code == 201

    invalid_assignment_response = client.post(
        "/api/v1/hospitalization/beds",
        headers=auth,
        json={
            "ward": "Medicina",
            "room": "302",
            "bed_label": "B",
            "status": "occupied",
            "encounter_id": ambulatory_response.json()["id"],
        },
    )
    assert invalid_assignment_response.status_code == 409


def test_hospital_bed_can_be_assigned_released_and_reassigned(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
) -> None:
    auth = auth_headers(client)
    first_patient_id = create_patient_for_permissions(client, auth)
    second_patient_id = create_patient_for_permissions(client, auth)

    first_encounter_response = client.post(
        f"/api/v1/patients/{first_patient_id}/encounters",
        headers=auth,
        json={
            "type": "hospitalization",
            "status": "in_progress",
            "reason": "Primer ingreso",
            "started_at": "2026-06-20T11:00:00Z",
        },
    )
    assert first_encounter_response.status_code == 201
    first_encounter_id = first_encounter_response.json()["id"]
    second_encounter_response = client.post(
        f"/api/v1/patients/{second_patient_id}/encounters",
        headers=auth,
        json={
            "type": "hospitalization",
            "status": "in_progress",
            "reason": "Segundo ingreso",
            "started_at": "2026-06-20T12:00:00Z",
        },
    )
    assert second_encounter_response.status_code == 201
    second_encounter_id = second_encounter_response.json()["id"]

    bed_response = client.post(
        "/api/v1/hospitalization/beds",
        headers=auth,
        json={
            "ward": "Cirugia",
            "room": "401",
            "bed_label": "A",
            "status": "available",
        },
    )
    assert bed_response.status_code == 201
    bed_id = bed_response.json()["id"]

    assignment_response = client.patch(
        f"/api/v1/hospitalization/beds/{bed_id}",
        headers=auth,
        json={"status": "occupied", "encounter_id": first_encounter_id},
    )
    assert assignment_response.status_code == 200
    assert assignment_response.json()["encounter_id"] == first_encounter_id

    duplicate_bed_response = client.post(
        "/api/v1/hospitalization/beds",
        headers=auth,
        json={
            "ward": "Cirugia",
            "room": "401",
            "bed_label": "B",
            "status": "available",
        },
    )
    assert duplicate_bed_response.status_code == 201
    duplicate_assignment_response = client.patch(
        f"/api/v1/hospitalization/beds/{duplicate_bed_response.json()['id']}",
        headers=auth,
        json={"status": "occupied", "encounter_id": first_encounter_id},
    )
    assert duplicate_assignment_response.status_code == 409

    direct_reassignment_response = client.patch(
        f"/api/v1/hospitalization/beds/{bed_id}",
        headers=auth,
        json={"status": "occupied", "encounter_id": second_encounter_id},
    )
    assert direct_reassignment_response.status_code == 409

    release_response = client.patch(
        f"/api/v1/hospitalization/beds/{bed_id}",
        headers=auth,
        json={"status": "available", "encounter_id": None},
    )
    assert release_response.status_code == 200
    assert release_response.json()["encounter_id"] is None

    first_audit_response = client.get(
        f"/api/v1/patients/{first_patient_id}/audit-events",
        headers=auth,
    )
    assert first_audit_response.status_code == 200
    assert any(
        event["action"] == "hospital_bed.updated"
        and event["extra_data"]["encounter_id"] == first_encounter_id
        and event["extra_data"]["after"]["encounter_id"] is None
        for event in first_audit_response.json()
    )

    reassignment_response = client.patch(
        f"/api/v1/hospitalization/beds/{bed_id}",
        headers=auth,
        json={"status": "occupied", "encounter_id": second_encounter_id},
    )
    assert reassignment_response.status_code == 200
    assert reassignment_response.json()["encounter_id"] == second_encounter_id


def test_hospitalization_board_requires_authentication(client: TestClient) -> None:
    response = client.get("/api/v1/hospitalization/active")

    assert response.status_code == 401
