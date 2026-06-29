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
    after_audit = audit_events(client, auth, patient_id)
    _assert_only_read_audit_added(
        before_audit,
        after_audit,
        action="patient_context.read",
        method="GET",
        path=f"/api/v1/patients/{patient_id}/context",
    )


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


def _assert_only_read_audit_added(
    before_audit: list[dict],
    after_audit: list[dict],
    *,
    action: str,
    method: str,
    path: str,
) -> None:
    before_ids = {item["id"] for item in before_audit}
    new_events = [item for item in after_audit if item["id"] not in before_ids]
    assert len(new_events) == 1
    read_event = new_events[0]
    assert read_event["action"] == action
    assert read_event["actor_id"] == "medico@oneepis.local"
    assert read_event["request_method"] == method
    assert read_event["request_path"] == path
    assert read_event["extra_data"] == {}
