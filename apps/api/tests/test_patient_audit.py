from fastapi.testclient import TestClient


def test_audit_events_include_correlation_and_before_after(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
    audit_events_for_patient,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient_for_permissions(client, auth)
    headers = {**auth, "X-OneEpis-Correlation-ID": "corr-test-001"}

    update_response = client.patch(
        f"/api/v1/patients/{patient_id}",
        headers=headers,
        json={"last_name": "Auditado"},
    )
    assert update_response.status_code == 200
    assert update_response.headers["X-OneEpis-Correlation-ID"] == "corr-test-001"

    audit_auth = auth_headers(client, email="admin@oneepis.local", password="admin")
    audit_response = client.get(
        f"/api/v1/patients/{patient_id}/audit-events",
        headers=audit_auth,
    )
    assert audit_response.status_code == 200
    public_patient_update = next(
        item for item in audit_response.json() if item["action"] == "patient.updated"
    )

    assert set(public_patient_update) == {
        "id",
        "action",
        "entity_type",
        "entity_id",
        "actor_id",
        "correlation_id",
        "request_method",
        "request_path",
        "created_at",
    }
    public_payload_text = str(public_patient_update)
    assert "extra_data" not in public_patient_update
    assert "before" not in public_payload_text
    assert "after" not in public_payload_text
    assert "note" not in public_payload_text
    assert "description" not in public_payload_text
    assert "detail" not in public_payload_text
    assert "snapshot" not in public_payload_text
    assert "Paciente" not in public_payload_text
    assert "Auditado" not in public_payload_text
    assert public_patient_update["correlation_id"] == "corr-test-001"
    assert public_patient_update["request_method"] == "PATCH"
    assert public_patient_update["request_path"] == f"/api/v1/patients/{patient_id}"

    patient_update = next(
        item
        for item in audit_events_for_patient(patient_id)
        if item["action"] == "patient.updated"
    )
    assert patient_update["correlation_id"] == "corr-test-001"
    assert patient_update["request_method"] == "PATCH"
    assert patient_update["request_path"] == f"/api/v1/patients/{patient_id}"
    assert patient_update["extra_data"]["before"] == {"last_name": "Paciente"}
    assert patient_update["extra_data"]["after"] == {"last_name": "Auditado"}


def test_patient_status_and_problem_update_are_audited(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
    audit_events_for_patient,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient_for_permissions(client, auth)

    status_response = client.patch(
        f"/api/v1/patients/{patient_id}",
        headers=auth,
        json={"clinical_status": "closed", "current_care_context": "ambulatory"},
    )
    assert status_response.status_code == 200
    assert status_response.json()["clinical_status"] == "closed"
    assert status_response.json()["current_care_context"] == "ambulatory"

    problem_response = client.post(
        f"/api/v1/patients/{patient_id}/problems",
        headers=auth,
        json={"title": "Diabetes tipo 2", "status": "active"},
    )
    assert problem_response.status_code == 201
    problem_id = problem_response.json()["id"]

    update_response = client.patch(
        f"/api/v1/patients/{patient_id}/problems/{problem_id}",
        headers=auth,
        json={"status": "resolved", "resolved_on": "2026-06-20"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["status"] == "resolved"

    snapshot_response = client.get(f"/api/v1/patients/{patient_id}/record", headers=auth)
    assert snapshot_response.status_code == 200
    assert snapshot_response.json()["active_problems"] == []

    list_response = client.get(f"/api/v1/patients/{patient_id}/problems", headers=auth)
    assert list_response.status_code == 200
    assert list_response.json() == []

    problem_update = next(
        item
        for item in audit_events_for_patient(patient_id)
        if item["action"] == "problem.updated"
    )
    assert problem_update["extra_data"]["before"] == {
        "status": "active",
        "resolved_on": None,
    }
    assert problem_update["extra_data"]["after"] == {
        "status": "resolved",
        "resolved_on": "2026-06-20",
    }
