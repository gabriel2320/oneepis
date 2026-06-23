from fastapi.testclient import TestClient

from oneepis_api.main import app

client = TestClient(app)


def test_health_check() -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["correlation_id"].startswith("oneepis-")


def test_health_check_echoes_correlation_id() -> None:
    response = client.get(
        "/api/v1/health",
        headers={"X-OneEpis-Correlation-ID": "walkthrough-v04"},
    )

    assert response.status_code == 200
    assert response.json()["correlation_id"] == "walkthrough-v04"
    assert response.headers["X-OneEpis-Correlation-ID"] == "walkthrough-v04"


def test_openapi_includes_patient_routes() -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert "/api/v1/patients" in response.json()["paths"]
