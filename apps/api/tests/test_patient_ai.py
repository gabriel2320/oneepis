from fastapi.testclient import TestClient


def test_patient_ai_suggestions_use_snapshot_without_persisting(
    client: TestClient,
    auth_headers,
) -> None:
    auth = auth_headers(client)
    patient_response = client.post(
        "/api/v1/patients",
        headers=auth,
        json={
            "first_name": "C",
            "last_name": "Paciente",
            "birth_date": "1992-01-01",
            "sex_at_birth": "unknown",
        },
    )
    assert patient_response.status_code == 201
    patient_id = patient_response.json()["id"]

    response = client.post(
        f"/api/v1/patients/{patient_id}/ai/suggestions",
        headers=auth,
        json={"focus": "documentation"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["provider"] == "local_rules"
    assert payload["status"] == "draft"
    assert payload["patient_id"] == patient_id
    assert payload["suggestions"][0]["title"] == "Faltan signos vitales recientes"


def test_patient_ai_suggestions_return_404_for_missing_patient(
    client: TestClient,
    auth_headers,
) -> None:
    auth = auth_headers(client)
    response = client.post(
        "/api/v1/patients/11111111-1111-4111-8111-111111111111/ai/suggestions",
        headers=auth,
        json={"focus": "summary"},
    )

    assert response.status_code == 404
