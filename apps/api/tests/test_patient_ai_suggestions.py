from fastapi.testclient import TestClient
from patient_ai_helpers import create_patient, create_vitals

from oneepis_api.services.medication_catalog import DEMO_ANALGESIC_ID


def test_patient_ai_suggestions_use_snapshot_without_persisting(
    client: TestClient,
    auth_headers,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient(client, auth, first_name="C", last_name="Paciente")

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


def test_patient_ai_suggestions_include_active_medication_read_context(
    client: TestClient,
    auth_headers,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient(client, auth, first_name="F", last_name="Farmacos")
    create_vitals(client, auth, patient_id, measured_at="2026-06-20T10:00:00Z")
    catalog_medication = client.post(
        f"/api/v1/patients/{patient_id}/medications",
        headers=auth,
        json={
            "catalog_item_id": str(DEMO_ANALGESIC_ID),
            "name": "Analgesico demo 500 mg comprimido",
            "dose": "500 mg",
            "route": "oral",
            "frequency": "cada 8 horas",
            "started_on": "2026-06-20",
        },
    )
    manual_medication = client.post(
        f"/api/v1/patients/{patient_id}/medications",
        headers=auth,
        json={
            "name": "Medicamento externo",
            "dose": "1 comprimido",
            "route": "oral",
            "frequency": "cada 24 horas",
            "started_on": "2026-06-20",
        },
    )
    assert catalog_medication.status_code == 201
    assert manual_medication.status_code == 201

    response = client.post(
        f"/api/v1/patients/{patient_id}/ai/suggestions",
        headers=auth,
        json={"focus": "safety"},
    )

    assert response.status_code == 200
    payload = response.json()
    titles = [item["title"] for item in payload["suggestions"]]
    details = " ".join(item["detail"] for item in payload["suggestions"])
    assert "Medicacion activa con fuente: Analgesico demo 500 mg comprimido" in titles
    assert "Medicacion activa incompleta: Medicamento externo" in titles
    assert "Fixture demo OneEpis; no uso clinico" in details
    assert "Fuente pendiente" in details
    assert "Faltantes: source" in details
    assert "no propone receta" in details
    assert all("Interaccion" not in title for title in titles)
    assert any("no prescribe" in note for note in payload["safety_notes"])


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
