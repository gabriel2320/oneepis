from fastapi.testclient import TestClient


def test_encounter_update_and_cancel_are_audited(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
    audit_events_for_patient,
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

    events = audit_events_for_patient(patient_id)
    encounter_create = next(item for item in events if item["action"] == "encounter.created")
    encounter_update = next(item for item in events if item["action"] == "encounter.updated")
    assert encounter_create["extra_data"]["after"] == {
        "ended_at": None,
        "patient_id": patient_id,
        "started_at": "2026-06-20T08:00:00+00:00",
        "status": "in_progress",
        "type": "hospitalization",
        "workflow_kind": "general",
    }
    assert encounter_update["extra_data"]["fields"] == ["ended_at", "notes", "status"]
    assert encounter_update["extra_data"]["before"] == {
        "status": "in_progress",
        "ended_at": None,
    }
    assert encounter_update["extra_data"]["after"] == {
        "status": "completed",
        "ended_at": "2026-06-20T18:00:00+00:00",
    }
    encounter_audit_payload = str(
        [encounter_create["extra_data"], encounter_update["extra_data"]]
    )
    assert "Ingreso hospitalario" not in encounter_audit_payload
    assert "Sala 2" not in encounter_audit_payload
    assert "Cierre administrativo" not in encounter_audit_payload
    encounter_cancel = next(item for item in events if item["action"] == "encounter.cancelled")
    assert encounter_cancel["extra_data"]["after"] == {"status": "cancelled"}


def test_clinical_entry_can_be_linked_and_unlinked_from_encounter(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
    audit_events_for_patient,
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

    updates = [
        item
        for item in audit_events_for_patient(patient_id)
        if item["action"] == "clinical_entry.updated"
    ]
    assert any(
        item["extra_data"]["after"] == {"encounter_id": encounter_id} for item in updates
    )
    assert any(item["extra_data"]["after"] == {"encounter_id": None} for item in updates)


def test_nursing_can_create_ambulatory_preconsult_encounter(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
    audit_events_for_patient,
) -> None:
    patient_id = create_patient_for_permissions(client, auth_headers(client))
    nursing_auth = auth_headers(
        client,
        email="enfermeria@oneepis.local",
        password="enfermeria",
    )

    response = client.post(
        f"/api/v1/patients/{patient_id}/encounters",
        headers=nursing_auth,
        json={
            "type": "ambulatory",
            "status": "in_progress",
            "workflow_kind": "ambulatory_preconsult",
            "reason": "Preconsulta ambulatoria",
            "started_at": "2026-06-20T12:00:00Z",
            "notes": "Preconsulta vinculada a cita ambulatoria.",
        },
    )

    assert response.status_code == 201
    created = response.json()
    assert created["type"] == "ambulatory"
    assert created["status"] == "in_progress"
    assert created["workflow_kind"] == "ambulatory_preconsult"

    created_audit = next(
        item
        for item in audit_events_for_patient(patient_id)
        if item["action"] == "encounter.created"
    )
    assert created_audit["actor_id"] == "enfermeria@oneepis.local"


def test_nursing_preconsult_permission_does_not_open_general_encounters(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
) -> None:
    patient_id = create_patient_for_permissions(client, auth_headers(client))
    nursing_auth = auth_headers(
        client,
        email="enfermeria@oneepis.local",
        password="enfermeria",
    )

    general_response = client.post(
        f"/api/v1/patients/{patient_id}/encounters",
        headers=nursing_auth,
        json={
            "type": "ambulatory",
            "status": "in_progress",
            "reason": "Control ambulatorio",
            "started_at": "2026-06-20T12:00:00Z",
        },
    )
    assert general_response.status_code == 403

    hospitalization_response = client.post(
        f"/api/v1/patients/{patient_id}/encounters",
        headers=nursing_auth,
        json={
            "type": "hospitalization",
            "status": "in_progress",
            "reason": "Ingreso hospitalario",
            "started_at": "2026-06-20T12:05:00Z",
            "workflow_kind": "ambulatory_preconsult",
            "notes": "Preconsulta vinculada a cita ambulatoria.",
        },
    )
    assert hospitalization_response.status_code == 403

    text_prefix_response = client.post(
        f"/api/v1/patients/{patient_id}/encounters",
        headers=nursing_auth,
        json={
            "type": "ambulatory",
            "status": "in_progress",
            "reason": "Control ambulatorio",
            "started_at": "2026-06-20T12:08:00Z",
            "notes": "Preconsulta vinculada a cita 11111111-1111-4111-8111-111111111111.",
        },
    )
    assert text_prefix_response.status_code == 403

    preconsult_response = client.post(
        f"/api/v1/patients/{patient_id}/encounters",
        headers=nursing_auth,
        json={
            "type": "ambulatory",
            "status": "in_progress",
            "workflow_kind": "ambulatory_preconsult",
            "reason": "Preconsulta ambulatoria",
            "started_at": "2026-06-20T12:10:00Z",
            "notes": "Preconsulta vinculada a cita ambulatoria.",
        },
    )
    assert preconsult_response.status_code == 201

    update_response = client.patch(
        f"/api/v1/patients/{patient_id}/encounters/{preconsult_response.json()['id']}",
        headers=nursing_auth,
        json={"status": "completed"},
    )
    assert update_response.status_code == 403


def test_discharge_summary_requires_hospitalization_encounter(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
    audit_events_for_patient,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient_for_permissions(client, auth)
    hospital_encounter = client.post(
        f"/api/v1/patients/{patient_id}/encounters",
        headers=auth,
        json={
            "type": "hospitalization",
            "status": "in_progress",
            "reason": "Hospitalizacion para epicrisis",
            "started_at": "2026-06-20T09:00:00Z",
        },
    ).json()
    ambulatory_encounter = client.post(
        f"/api/v1/patients/{patient_id}/encounters",
        headers=auth,
        json={
            "type": "ambulatory",
            "status": "in_progress",
            "reason": "Control ambulatorio",
            "started_at": "2026-06-20T12:00:00Z",
        },
    ).json()

    invalid_response = client.post(
        f"/api/v1/patients/{patient_id}/clinical-entries",
        headers=auth,
        json={
            "encounter_id": ambulatory_encounter["id"],
            "kind": "discharge_summary",
            "occurred_at": "2026-06-21T10:00:00Z",
            "title": "Epicrisis fuera de hospitalizacion",
        },
    )
    assert invalid_response.status_code == 422

    created_response = client.post(
        f"/api/v1/patients/{patient_id}/clinical-entries",
        headers=auth,
        json={
            "encounter_id": hospital_encounter["id"],
            "kind": "discharge_summary",
            "occurred_at": "2026-06-21T10:00:00Z",
            "title": "Epicrisis preliminar",
            "assessment": "Diagnostico de egreso en borrador.",
            "plan": "Control y seguimiento documentado.",
        },
    )
    assert created_response.status_code == 201
    created = created_response.json()
    assert created["kind"] == "discharge_summary"
    assert created["status"] == "draft"
    assert created["encounter_id"] == hospital_encounter["id"]

    created_audit = next(
        item
        for item in audit_events_for_patient(patient_id)
        if item["action"] == "clinical_entry.created"
        and item["extra_data"]["kind"] == "discharge_summary"
    )
    assert created_audit["entity_id"] == created["id"]
