from fastapi.testclient import TestClient

from oneepis_api.main import app

client = TestClient(app)


def test_health_check() -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_openapi_includes_patient_routes() -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert "/api/v1/patients" in response.json()["paths"]
