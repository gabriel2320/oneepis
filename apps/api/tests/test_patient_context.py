from fastapi.testclient import TestClient
from patient_ai_helpers import (
    audit_events,
    create_lab_panel,
    create_patient,
    create_problem,
)


def test_patient_context_derives_active_hospitalization_without_writing(
    client: TestClient,
    auth_headers,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient(client, auth, first_name="Contexto", last_name="Canonico")
    ambulatory_response = client.post(
        f"/api/v1/patients/{patient_id}/encounters",
        headers=auth,
        json={
            "type": "ambulatory",
            "status": "completed",
            "reason": "Control previo",
            "started_at": "2026-06-18T10:00:00Z",
            "ended_at": "2026-06-18T10:30:00Z",
        },
    )
    assert ambulatory_response.status_code == 201
    hospital_response = client.post(
        f"/api/v1/patients/{patient_id}/encounters",
        headers=auth,
        json={
            "type": "hospitalization",
            "status": "in_progress",
            "reason": "Neumonia",
            "started_at": "2026-06-20T08:00:00Z",
            "location_label": "Medicina interna",
        },
    )
    assert hospital_response.status_code == 201
    hospital_encounter_id = hospital_response.json()["id"]
    create_problem(client, auth, patient_id, title="Hipertension arterial", code="I10")
    create_lab_panel(client, auth, patient_id, panel_name="Perfil renal contexto")
    before_audit = audit_events(client, auth, patient_id)

    response = client.get(f"/api/v1/patients/{patient_id}/context", headers=auth)

    assert response.status_code == 200
    payload = response.json()
    assert payload["patient_id"] == patient_id
    assert payload["applies_changes"] is False
    assert payload["derived_care_context"] == "hospitalization"
    assert payload["active_encounter"]["id"] == hospital_encounter_id
    assert payload["active_encounter"]["workflow_kind"] == "general"
    assert payload["active_hospitalization"]["id"] == hospital_encounter_id
    assert payload["recent_ambulatory_encounters"][0]["id"] == ambulatory_response.json()["id"]
    assert payload["active_problems"][0]["label"] == "Hipertension arterial"
    assert payload["recent_labs"][0]["label"] == "Perfil renal contexto"
    assert audit_events(client, auth, patient_id) == before_audit


def test_patient_context_allows_readonly_user(
    client: TestClient,
    auth_headers,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient(client, auth, first_name="Contexto", last_name="Lectura")
    readonly_auth = auth_headers(client, email="lector@oneepis.local", password="lector")

    response = client.get(f"/api/v1/patients/{patient_id}/context", headers=readonly_auth)

    assert response.status_code == 200
    assert response.json()["patient_id"] == patient_id
