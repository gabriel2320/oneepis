from fastapi.testclient import TestClient


def test_hospital_indication_create_list_update_close_and_audit(
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
            "type": "hospitalization",
            "status": "in_progress",
            "reason": "Ingreso para indicaciones",
            "started_at": "2026-06-20T09:00:00Z",
        },
    )
    assert encounter_response.status_code == 201
    encounter_id = encounter_response.json()["id"]

    create_response = client.post(
        f"/api/v1/hospitalization/patients/{patient_id}/indications",
        headers=auth,
        json={
            "indicated_at": "2026-06-20T10:00:00Z",
            "title": "Indicacion de observacion",
            "indication_text": "Mantener observacion clinica y registrar cambios relevantes.",
            "rationale": "Borrador para continuidad hospitalaria.",
            "safety_notes": "No equivale a orden firmada.",
        },
    )
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["patient_id"] == patient_id
    assert created["encounter_id"] == encounter_id
    assert created["status"] == "draft"
    assert created["created_by"] == "medico@oneepis.local"

    list_response = client.get(
        f"/api/v1/hospitalization/patients/{patient_id}/indications",
        headers=auth,
    )
    assert list_response.status_code == 200
    assert list_response.json()[0]["id"] == created["id"]

    update_response = client.patch(
        f"/api/v1/hospitalization/patients/{patient_id}/indications/{created['id']}",
        headers=auth,
        json={"title": "Indicacion actualizada"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["title"] == "Indicacion actualizada"

    close_response = client.patch(
        f"/api/v1/hospitalization/patients/{patient_id}/indications/{created['id']}",
        headers=auth,
        json={"status": "closed"},
    )
    assert close_response.status_code == 200
    assert close_response.json()["status"] == "closed"

    locked_update_response = client.patch(
        f"/api/v1/hospitalization/patients/{patient_id}/indications/{created['id']}",
        headers=auth,
        json={"title": "No debe editarse"},
    )
    assert locked_update_response.status_code == 409

    events = audit_events_for_patient(patient_id)
    create_event = next(item for item in events if item["action"] == "hospital_indication.created")
    assert create_event["extra_data"]["after"]["status"] == "draft"
    assert create_event["extra_data"]["after"]["encounter_id"] == encounter_id
    assert "title" not in create_event["extra_data"]["after"]
    assert "indication_text" not in create_event["extra_data"]["after"]
    assert "rationale" not in create_event["extra_data"]["after"]
    assert "safety_notes" not in create_event["extra_data"]["after"]
    assert "Mantener observacion clinica" not in str(create_event["extra_data"])
    title_event = next(
        item
        for item in events
        if item["action"] == "hospital_indication.updated"
        and item["extra_data"].get("fields") == ["title"]
    )
    assert title_event["extra_data"]["before"] == {}
    assert title_event["extra_data"]["after"] == {}
    assert "Indicacion actualizada" not in str(title_event["extra_data"])
    close_event = next(
        item
        for item in events
        if item["action"] == "hospital_indication.updated"
        and item["extra_data"]["after"].get("status") == "closed"
    )
    assert close_event["extra_data"]["patient_id"] == patient_id
    assert close_event["extra_data"]["encounter_id"] == encounter_id
    assert close_event["extra_data"]["before"] == {"status": "draft"}
    assert close_event["extra_data"]["after"] == {"status": "closed"}


def test_hospital_indication_requires_active_hospitalization(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient_for_permissions(client, auth)

    response = client.post(
        f"/api/v1/hospitalization/patients/{patient_id}/indications",
        headers=auth,
        json={
            "indicated_at": "2026-06-20T10:00:00Z",
            "title": "Indicacion sin ingreso",
            "indication_text": "No debe crearse sin ingreso activo.",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Hospital indication requires an active hospitalization encounter"
    )


def test_hospital_indication_write_requires_medical_role(
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
            "type": "hospitalization",
            "status": "in_progress",
            "reason": "Ingreso activo",
            "started_at": "2026-06-20T07:00:00Z",
        },
    )
    assert encounter_response.status_code == 201
    nursing_auth = auth_headers(
        client,
        email="enfermeria@oneepis.local",
        password="enfermeria",
    )

    list_response = client.get(
        f"/api/v1/hospitalization/patients/{patient_id}/indications",
        headers=nursing_auth,
    )
    assert list_response.status_code == 200

    create_response = client.post(
        f"/api/v1/hospitalization/patients/{patient_id}/indications",
        headers=nursing_auth,
        json={
            "indicated_at": "2026-06-20T10:00:00Z",
            "title": "Indicacion enfermeria",
            "indication_text": "Enfermeria no debe crear indicaciones medicas.",
        },
    )
    assert create_response.status_code == 403
