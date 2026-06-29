from fastapi.testclient import TestClient


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
    deleted_audit = next(
        item
        for item in audit_events
        if item["action"] == "clinical_entry.deleted" and item["entity_id"] == entry_id
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
    deleted_before = deleted_audit["extra_data"]["before"]
    assert set(created_after) == expected_fields
    assert set(deleted_before) == expected_fields
    assert created_after["patient_id"] == patient_id
    assert created_after["kind"] == "progress"
    assert deleted_before["status"] == "draft"
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
            deleted_audit["extra_data"],
        ]
    )
    assert "sensible" not in audit_payload
    assert "Metadata" not in audit_payload
