from fastapi.testclient import TestClient


def test_patient_routes_require_authentication(client: TestClient) -> None:
    response = client.get("/api/v1/patients")

    assert response.status_code == 401


def test_readonly_user_cannot_write_patient(
    client: TestClient,
    auth_headers,
) -> None:
    auth = auth_headers(client, email="lector@oneepis.local", password="lector")

    response = client.post(
        "/api/v1/patients",
        headers=auth,
        json={
            "first_name": "Solo",
            "last_name": "Lectura",
            "birth_date": "1990-01-01",
            "sex_at_birth": "unknown",
        },
    )

    assert response.status_code == 403


def test_readonly_user_can_read_patient_snapshot(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
) -> None:
    patient_id = create_patient_for_permissions(client, auth_headers(client))
    readonly_auth = auth_headers(client, email="lector@oneepis.local", password="lector")

    response = client.get(f"/api/v1/patients/{patient_id}/record", headers=readonly_auth)

    assert response.status_code == 200
    assert response.json()["patient"]["id"] == patient_id


def test_nursing_can_record_vitals_but_not_medical_actions(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
) -> None:
    patient_id = create_patient_for_permissions(client, auth_headers(client))
    nursing_auth = auth_headers(
        client,
        email="enfermeria@oneepis.local",
        password="enfermeria",
    )

    vitals_response = client.post(
        f"/api/v1/patients/{patient_id}/vital-signs",
        headers=nursing_auth,
        json={
            "measured_at": "2026-06-20T12:00:00Z",
            "systolic_bp": 120,
            "diastolic_bp": 70,
            "heart_rate_bpm": 80,
        },
    )
    assert vitals_response.status_code == 201
    assert vitals_response.json()["heart_rate_bpm"] == 80

    entry_response = client.post(
        f"/api/v1/patients/{patient_id}/clinical-entries",
        headers=nursing_auth,
        json={
            "kind": "progress",
            "occurred_at": "2026-06-20T12:05:00Z",
            "title": "Evolucion SOAP",
        },
    )
    assert entry_response.status_code == 403

    medication_response = client.post(
        f"/api/v1/patients/{patient_id}/medications",
        headers=nursing_auth,
        json={"name": "Ibuprofeno", "started_on": "2026-06-20"},
    )
    assert medication_response.status_code == 403

    problem_response = client.post(
        f"/api/v1/patients/{patient_id}/problems",
        headers=nursing_auth,
        json={"title": "Dolor toracico"},
    )
    assert problem_response.status_code == 403

    encounter_response = client.post(
        f"/api/v1/patients/{patient_id}/encounters",
        headers=nursing_auth,
        json={
            "type": "hospitalization",
            "reason": "Ingreso hospitalario",
            "started_at": "2026-06-20T12:10:00Z",
        },
    )
    assert encounter_response.status_code == 403

    ai_response = client.post(
        f"/api/v1/patients/{patient_id}/ai/suggestions",
        headers=nursing_auth,
        json={"focus": "summary"},
    )
    assert ai_response.status_code == 403
