import uuid

from fastapi.testclient import TestClient
from sqlalchemy import select

from oneepis_api.db.session import get_session
from oneepis_api.main import app
from oneepis_api.models.clinical_record import RecordStatus, VitalSign


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


def test_vital_sign_audit_uses_structural_allowlist(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
    audit_events_for_patient,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient_for_permissions(client, auth)
    blocked_create = client.post(
        f"/api/v1/patients/{patient_id}/vital-signs",
        headers=auth,
        json={
            "measured_at": "2026-06-20T11:00:00Z",
            "status": "entered_in_error",
            "heart_rate_bpm": 70,
        },
    )
    assert blocked_create.status_code == 422

    create_response = client.post(
        f"/api/v1/patients/{patient_id}/vital-signs",
        headers=auth,
        json={
            "measured_at": "2026-06-20T12:00:00Z",
            "temperature_c": "38.2",
            "systolic_bp": 130,
            "diastolic_bp": 78,
            "heart_rate_bpm": 104,
            "oxygen_saturation_pct": "92.0",
            "notes": "Nota clinica sensible de signos vitales.",
        },
    )
    assert create_response.status_code == 201
    assert create_response.json()["status"] == "active"
    vital_id = create_response.json()["id"]
    blocked_patch = client.patch(
        f"/api/v1/patients/{patient_id}/vital-signs/{vital_id}",
        headers=auth,
        json={"status": "entered_in_error"},
    )
    assert blocked_patch.status_code == 422

    update_response = client.patch(
        f"/api/v1/patients/{patient_id}/vital-signs/{vital_id}",
        headers=auth,
        json={
            "heart_rate_bpm": 82,
            "oxygen_saturation_pct": "96.0",
            "notes": "Nota clinica corregida.",
        },
    )
    assert update_response.status_code == 200

    delete_response = client.delete(
        f"/api/v1/patients/{patient_id}/vital-signs/{vital_id}",
        headers=auth,
    )
    assert delete_response.status_code == 204
    assert _vital_sign_status(vital_id) == RecordStatus.ENTERED_IN_ERROR

    list_response = client.get(f"/api/v1/patients/{patient_id}/vital-signs", headers=auth)
    detail_response = client.get(
        f"/api/v1/patients/{patient_id}/vital-signs/{vital_id}",
        headers=auth,
    )
    record_response = client.get(f"/api/v1/patients/{patient_id}/record", headers=auth)
    assistant_timeline_response = client.get(
        f"/api/v1/patients/{patient_id}/assistant/timeline",
        headers=auth,
    )
    assistant_search_response = client.get(
        f"/api/v1/patients/{patient_id}/assistant/search?q=clinica",
        headers=auth,
    )
    assistant_chart_response = client.post(
        f"/api/v1/patients/{patient_id}/assistant/chart",
        headers=auth,
        json={"series": ["heart_rate_bpm"]},
    )
    second_delete_response = client.delete(
        f"/api/v1/patients/{patient_id}/vital-signs/{vital_id}",
        headers=auth,
    )

    assert list_response.status_code == 200
    assert list_response.json() == []
    assert detail_response.status_code == 404
    assert record_response.status_code == 200
    assert record_response.json()["latest_vitals"] is None
    assert assistant_timeline_response.status_code == 200
    assert all(
        item["item_id"] != vital_id for item in assistant_timeline_response.json()["items"]
    )
    assert assistant_search_response.status_code == 200
    assert assistant_search_response.json()["results"] == []
    assert assistant_chart_response.status_code == 200
    assert assistant_chart_response.json()["series"] == []
    assert second_delete_response.status_code == 404

    events = audit_events_for_patient(patient_id)
    created = next(item for item in events if item["action"] == "vital_sign.created")
    updated = next(item for item in events if item["action"] == "vital_sign.updated")
    entered_in_error = next(
        item for item in events if item["action"] == "vital_sign.entered_in_error"
    )
    created_after = created["extra_data"]["after"]
    assert created_after["patient_id"] == patient_id
    assert created_after["measured_at"].startswith("2026-06-20T12:00:00")
    assert created_after["status"] == "active"
    assert set(created_after) == {"patient_id", "measured_at", "status"}
    assert updated["extra_data"]["fields"] == [
        "heart_rate_bpm",
        "notes",
        "oxygen_saturation_pct",
    ]
    assert updated["extra_data"]["before"] == {}
    assert updated["extra_data"]["after"] == {}
    assert entered_in_error["extra_data"]["before"] == {"status": "active"}
    assert entered_in_error["extra_data"]["after"] == {"status": "entered_in_error"}
    assert entered_in_error["extra_data"]["reason_code"] == "entered_in_error"
    audit_text = str(
        [created["extra_data"], updated["extra_data"], entered_in_error["extra_data"]]
    )
    assert "temperature_c" not in audit_text
    assert "systolic_bp" not in audit_text
    assert "diastolic_bp" not in audit_text
    assert "heart_rate_bpm" in audit_text
    assert "oxygen_saturation_pct" in audit_text
    assert "Nota clinica" not in audit_text


def _vital_sign_status(vital_id: str) -> RecordStatus:
    override_session = app.dependency_overrides[get_session]
    session_iterator = override_session()
    session = next(session_iterator)
    try:
        vital = session.scalar(select(VitalSign).where(VitalSign.id == uuid.UUID(vital_id)))
        assert vital is not None
        return vital.status
    finally:
        session_iterator.close()
