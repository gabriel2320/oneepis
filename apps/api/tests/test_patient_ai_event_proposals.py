from fastapi.testclient import TestClient
from patient_ai_helpers import audit_events, create_entry, create_patient


def test_event_proposals_from_entry_are_reviewable_and_do_not_persist(
    client: TestClient,
    auth_headers,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient(client, auth, first_name="Propuesta", last_name="Evento")
    entry_id = create_entry(
        client,
        auth,
        patient_id,
        title="Evolucion con plan",
        assessment="Dolor controlado y sin fiebre.",
        plan="Mantener hidratacion. Controlar signos vitales.",
    )

    response = client.post(
        f"/api/v1/patients/{patient_id}/ai/event-proposals-from-entry",
        headers=auth,
        json={"entry_id": entry_id},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["applies_changes"] is False
    assert payload["requires_human_confirmation"] is True
    assert [proposal["summary"] for proposal in payload["proposals"]] == [
        "Dolor controlado y sin fiebre",
        "Mantener hidratacion",
        "Controlar signos vitales",
    ]
    assert payload["proposals"][1]["event_type"] == "care_plan"
    assert payload["proposals"][1]["source_type"] == "clinical_entry"
    assert payload["proposals"][1]["patch"]["target"] == "clinical_event"
    assert payload["proposals"][1]["patch"]["requires_human_confirmation"] is True
    assert {
        operation["path"] for operation in payload["proposals"][1]["patch"]["operations"]
    } >= {"/event_type", "/occurred_at", "/summary", "/source_type", "/source_ref", "/payload"}
    events_response = client.get(
        f"/api/v1/patients/{patient_id}/clinical-events",
        headers=auth,
    )
    assert events_response.status_code == 200
    assert events_response.json() == []

    patient_audit_events = audit_events(client, auth, patient_id)
    assert any(
        event["action"] == "ai.entry_event_proposals.created"
        and event["extra_data"]["proposal_count"] == 3
        for event in patient_audit_events
    )
