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


def test_hospitalization_board_requires_authentication(client: TestClient) -> None:
    response = client.get("/api/v1/hospitalization/active")

    assert response.status_code == 401
