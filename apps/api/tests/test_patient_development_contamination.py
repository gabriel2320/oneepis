from fastapi.testclient import TestClient


def test_development_rejects_foreign_project_patient_name(
    client: TestClient,
    auth_headers,
) -> None:
    response = client.post(
        "/api/v1/patients",
        headers=auth_headers(client),
        json={
            "first_name": "Evolab",
            "last_name": "ReadonlyVitals",
            "birth_date": "1986-06-06",
            "sex_at_birth": "unknown",
        },
    )

    assert response.status_code == 422
    assert "foreign project fixture terms" in response.json()["detail"]


def test_development_rejects_foreign_project_patient_update(
    client: TestClient,
    auth_headers,
) -> None:
    auth = auth_headers(client)
    patient_response = client.post(
        "/api/v1/patients",
        headers=auth,
        json={
            "first_name": "Paciente",
            "last_name": "Limpio",
            "birth_date": "1990-01-01",
            "sex_at_birth": "unknown",
        },
    )
    assert patient_response.status_code == 201

    response = client.patch(
        f"/api/v1/patients/{patient_response.json()['id']}",
        headers=auth,
        json={"last_name": "Pacmed"},
    )

    assert response.status_code == 422
    assert "pacmed" in response.json()["detail"]
