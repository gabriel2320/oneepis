from fastapi.testclient import TestClient


def test_encounter_update_and_cancel_are_audited(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient_for_permissions(client, auth)

    create_response = client.post(
        f"/api/v1/patients/{patient_id}/encounters",
        headers=auth,
        json={
            "type": "hospitalization",
            "status": "in_progress",
            "reason": "Ingreso hospitalario",
            "started_at": "2026-06-20T08:00:00Z",
            "location_label": "Sala 2",
        },
    )
    assert create_response.status_code == 201
    encounter_id = create_response.json()["id"]

    list_response = client.get(f"/api/v1/patients/{patient_id}/encounters", headers=auth)
    assert list_response.status_code == 200
    assert list_response.json()[0]["id"] == encounter_id

    update_response = client.patch(
        f"/api/v1/patients/{patient_id}/encounters/{encounter_id}",
        headers=auth,
        json={
            "status": "completed",
            "ended_at": "2026-06-20T18:00:00Z",
            "notes": "Cierre administrativo de desarrollo",
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["status"] == "completed"

    cancel_response = client.delete(
        f"/api/v1/patients/{patient_id}/encounters/{encounter_id}",
        headers=auth,
    )
    assert cancel_response.status_code == 204

    get_response = client.get(
        f"/api/v1/patients/{patient_id}/encounters/{encounter_id}",
        headers=auth,
    )
    assert get_response.status_code == 200
    assert get_response.json()["status"] == "cancelled"

    audit_response = client.get(f"/api/v1/patients/{patient_id}/audit-events", headers=auth)
    assert audit_response.status_code == 200
    events = audit_response.json()
    encounter_update = next(item for item in events if item["action"] == "encounter.updated")
    assert encounter_update["extra_data"]["before"] == {
        "status": "in_progress",
        "ended_at": None,
        "notes": None,
    }
    assert encounter_update["extra_data"]["after"] == {
        "status": "completed",
        "ended_at": "2026-06-20T18:00:00+00:00",
        "notes": "Cierre administrativo de desarrollo",
    }
    encounter_cancel = next(item for item in events if item["action"] == "encounter.cancelled")
    assert encounter_cancel["extra_data"]["after"] == {"status": "cancelled"}


def test_clinical_entry_can_be_linked_and_unlinked_from_encounter(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient_for_permissions(client, auth)
    encounter_response = client.post(
        f"/api/v1/patients/{patient_id}/encounters",
        headers=auth,
        json={
            "type": "ambulatory",
            "reason": "Control longitudinal",
            "started_at": "2026-06-20T09:00:00Z",
        },
    )
    assert encounter_response.status_code == 201
    encounter_id = encounter_response.json()["id"]

    entry_response = client.post(
        f"/api/v1/patients/{patient_id}/clinical-entries",
        headers=auth,
        json={
            "kind": "progress",
            "occurred_at": "2026-06-20T09:30:00Z",
            "title": "SOAP sin encuentro",
        },
    )
    assert entry_response.status_code == 201
    entry_id = entry_response.json()["id"]
    assert entry_response.json()["encounter_id"] is None

    link_response = client.patch(
        f"/api/v1/patients/{patient_id}/clinical-entries/{entry_id}",
        headers=auth,
        json={"encounter_id": encounter_id},
    )
    assert link_response.status_code == 200
    assert link_response.json()["encounter_id"] == encounter_id

    unlink_response = client.patch(
        f"/api/v1/patients/{patient_id}/clinical-entries/{entry_id}",
        headers=auth,
        json={"encounter_id": None},
    )
    assert unlink_response.status_code == 200
    assert unlink_response.json()["encounter_id"] is None

    audit_response = client.get(f"/api/v1/patients/{patient_id}/audit-events", headers=auth)
    assert audit_response.status_code == 200
    updates = [
        item
        for item in audit_response.json()
        if item["action"] == "clinical_entry.updated"
    ]
    assert any(
        item["extra_data"]["after"] == {"encounter_id": encounter_id} for item in updates
    )
    assert any(item["extra_data"]["after"] == {"encounter_id": None} for item in updates)
