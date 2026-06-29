import uuid

from fastapi.testclient import TestClient
from sqlalchemy import select

from oneepis_api.db.session import get_session
from oneepis_api.main import app
from oneepis_api.models.clinical_record import ClinicalEntry, ClinicalEntryStatus


def test_clinical_entry_audit_snapshots_use_allowlist(
    client: TestClient,
    auth_headers,
    audit_events_for_patient,
) -> None:
    auth = auth_headers(client)
    patient_response = client.post(
        "/api/v1/patients",
        headers=auth,
        json={
            "first_name": "Entrada",
            "last_name": "Auditada",
            "birth_date": "1985-05-12",
            "sex_at_birth": "female",
        },
    )
    assert patient_response.status_code == 201
    patient_id = patient_response.json()["id"]

    create_response = client.post(
        f"/api/v1/patients/{patient_id}/clinical-entries",
        headers=auth,
        json={
            "kind": "progress",
            "status": "draft",
            "occurred_at": "2026-06-22T10:05:00Z",
            "title": "Titulo narrativo sensible",
            "subjective": "Subjetivo sensible.",
            "objective": "Objetivo sensible.",
            "assessment": "Evaluacion sensible.",
            "plan": "Plan sensible.",
            "extra_data": {"note": "Metadata narrativa sensible."},
        },
    )
    assert create_response.status_code == 201
    entry_id = create_response.json()["id"]

    update_response = client.patch(
        f"/api/v1/patients/{patient_id}/clinical-entries/{entry_id}",
        headers=auth,
        json={
            "title": "Titulo actualizado sensible",
            "subjective": "Subjetivo actualizado sensible.",
            "assessment": "Evaluacion actualizada sensible.",
            "extra_data": {"note": "Metadata actualizada sensible."},
        },
    )
    assert update_response.status_code == 200

    delete_response = client.delete(
        f"/api/v1/patients/{patient_id}/clinical-entries/{entry_id}",
        headers=auth,
    )
    assert delete_response.status_code == 204

    audit_events = audit_events_for_patient(patient_id)
    created_audit = next(
        item
        for item in audit_events
        if item["action"] == "clinical_entry.created" and item["entity_id"] == entry_id
    )
    updated_audit = next(
        item
        for item in audit_events
        if item["action"] == "clinical_entry.updated" and item["entity_id"] == entry_id
    )
    entered_in_error_audit = next(
        item
        for item in audit_events
        if item["action"] == "clinical_entry.entered_in_error" and item["entity_id"] == entry_id
    )
    expected_fields = {
        "created_by",
        "encounter_id",
        "kind",
        "occurred_at",
        "patient_id",
        "status",
    }
    created_after = created_audit["extra_data"]["after"]
    entered_in_error_before = entered_in_error_audit["extra_data"]["before"]
    assert set(created_after) == expected_fields
    assert set(entered_in_error_before) == {"status"}
    assert created_after["patient_id"] == patient_id
    assert created_after["kind"] == "progress"
    assert entered_in_error_before["status"] == "draft"
    assert entered_in_error_audit["extra_data"]["after"] == {"status": "entered_in_error"}
    assert entered_in_error_audit["extra_data"]["reason_code"] == "entered_in_error"
    assert updated_audit["extra_data"]["fields"] == [
        "assessment",
        "extra_data",
        "subjective",
        "title",
    ]
    assert updated_audit["extra_data"]["before"] == {}
    assert updated_audit["extra_data"]["after"] == {}
    audit_payload = str(
        [
            created_audit["extra_data"],
            updated_audit["extra_data"],
            entered_in_error_audit["extra_data"],
        ]
    )
    assert "sensible" not in audit_payload
    assert "Metadata" not in audit_payload


def test_clinical_entry_delete_marks_entered_in_error_and_hides_entry(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient_for_permissions(client, auth)
    blocked_create = client.post(
        f"/api/v1/patients/{patient_id}/clinical-entries",
        headers=auth,
        json={
            "kind": "progress",
            "status": "entered_in_error",
            "occurred_at": "2026-06-22T10:05:00Z",
            "title": "No debe crearse oculto",
        },
    )
    assert blocked_create.status_code == 422

    create_response = client.post(
        f"/api/v1/patients/{patient_id}/clinical-entries",
        headers=auth,
        json={
            "kind": "progress",
            "status": "draft",
            "occurred_at": "2026-06-22T10:05:00Z",
            "title": "Entrada visible antes de borrar",
        },
    )
    assert create_response.status_code == 201
    entry_id = create_response.json()["id"]
    blocked_patch = client.patch(
        f"/api/v1/patients/{patient_id}/clinical-entries/{entry_id}",
        headers=auth,
        json={"status": "entered_in_error"},
    )
    assert blocked_patch.status_code == 422

    delete_response = client.delete(
        f"/api/v1/patients/{patient_id}/clinical-entries/{entry_id}",
        headers=auth,
    )
    assert delete_response.status_code == 204
    assert _clinical_entry_status(entry_id) == ClinicalEntryStatus.ENTERED_IN_ERROR

    list_response = client.get(f"/api/v1/patients/{patient_id}/clinical-entries", headers=auth)
    detail_response = client.get(
        f"/api/v1/patients/{patient_id}/clinical-entries/{entry_id}",
        headers=auth,
    )
    timeline_response = client.get(f"/api/v1/patients/{patient_id}/timeline", headers=auth)
    record_response = client.get(f"/api/v1/patients/{patient_id}/record", headers=auth)
    assistant_timeline_response = client.get(
        f"/api/v1/patients/{patient_id}/assistant/timeline",
        headers=auth,
    )
    assistant_search_response = client.get(
        f"/api/v1/patients/{patient_id}/assistant/search?q=visible",
        headers=auth,
    )
    second_delete_response = client.delete(
        f"/api/v1/patients/{patient_id}/clinical-entries/{entry_id}",
        headers=auth,
    )

    assert list_response.status_code == 200
    assert list_response.json() == []
    assert detail_response.status_code == 404
    assert timeline_response.status_code == 200
    assert timeline_response.json()["entries"] == []
    assert record_response.status_code == 200
    assert record_response.json()["recent_entries"] == []
    assert assistant_timeline_response.status_code == 200
    assert all(
        item["item_id"] != entry_id for item in assistant_timeline_response.json()["items"]
    )
    assert assistant_search_response.status_code == 200
    assert assistant_search_response.json()["results"] == []
    assert second_delete_response.status_code == 404


def _clinical_entry_status(entry_id: str) -> ClinicalEntryStatus:
    override_session = app.dependency_overrides[get_session]
    session_iterator = override_session()
    session = next(session_iterator)
    try:
        entry = session.scalar(select(ClinicalEntry).where(ClinicalEntry.id == uuid.UUID(entry_id)))
        assert entry is not None
        return entry.status
    finally:
        session_iterator.close()
