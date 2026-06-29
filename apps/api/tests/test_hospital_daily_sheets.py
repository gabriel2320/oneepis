from fastapi.testclient import TestClient


def test_hospital_daily_sheet_create_list_update_and_audit(
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
            "reason": "Ingreso para hoja diaria",
            "started_at": "2026-06-20T07:00:00Z",
        },
    )
    assert encounter_response.status_code == 201
    encounter_id = encounter_response.json()["id"]

    create_response = client.post(
        f"/api/v1/hospitalization/patients/{patient_id}/daily-sheets",
        headers=auth,
        json={
            "sheet_date": "2026-06-20",
            "clinical_summary": "Evolucion hospitalaria estable.",
            "overnight_events": "Sin eventos nocturnos criticos.",
            "active_plan": "Continuar observacion clinica.",
            "pending_tasks": "Revisar signos vitales de control.",
            "safety_notes": "Documento de desarrollo.",
        },
    )
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["patient_id"] == patient_id
    assert created["encounter_id"] == encounter_id
    assert created["status"] == "draft"
    assert created["created_by"] == "medico@oneepis.local"

    duplicate_response = client.post(
        f"/api/v1/hospitalization/patients/{patient_id}/daily-sheets",
        headers=auth,
        json={
            "sheet_date": "2026-06-20",
            "clinical_summary": "Duplicada",
        },
    )
    assert duplicate_response.status_code == 409

    list_response = client.get(
        f"/api/v1/hospitalization/patients/{patient_id}/daily-sheets",
        headers=auth,
    )
    assert list_response.status_code == 200
    assert list_response.json()[0]["id"] == created["id"]

    update_response = client.patch(
        f"/api/v1/hospitalization/patients/{patient_id}/daily-sheets/{created['id']}",
        headers=auth,
        json={"active_plan": "Mantener plan y preparar reevaluacion."},
    )
    assert update_response.status_code == 200
    assert update_response.json()["active_plan"] == "Mantener plan y preparar reevaluacion."

    close_response = client.patch(
        f"/api/v1/hospitalization/patients/{patient_id}/daily-sheets/{created['id']}",
        headers=auth,
        json={"status": "closed"},
    )
    assert close_response.status_code == 200
    assert close_response.json()["status"] == "closed"

    locked_update_response = client.patch(
        f"/api/v1/hospitalization/patients/{patient_id}/daily-sheets/{created['id']}",
        headers=auth,
        json={"active_plan": "No debe permitir edicion posterior."},
    )
    assert locked_update_response.status_code == 409

    events = audit_events_for_patient(patient_id)
    assert any(item["action"] == "hospital_daily_sheet.created" for item in events)
    update_event = next(
        item
        for item in events
        if item["action"] == "hospital_daily_sheet.updated"
        and item["extra_data"]["after"].get("active_plan")
        == "Mantener plan y preparar reevaluacion."
    )
    assert update_event["extra_data"]["patient_id"] == patient_id
    assert update_event["extra_data"]["encounter_id"] == encounter_id
    assert update_event["extra_data"]["status"] == "draft"
    assert update_event["extra_data"]["before"] == {
        "active_plan": "Continuar observacion clinica."
    }
    assert update_event["extra_data"]["after"] == {
        "active_plan": "Mantener plan y preparar reevaluacion."
    }
    close_event = next(
        item
        for item in events
        if item["action"] == "hospital_daily_sheet.updated"
        and item["extra_data"]["after"].get("status") == "closed"
    )
    assert close_event["extra_data"]["before"] == {"status": "draft"}
    assert close_event["extra_data"]["after"] == {"status": "closed"}


def test_hospital_daily_sheet_date_must_match_hospitalization_window(
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
            "reason": "Ingreso con ventana definida",
            "started_at": "2026-06-20T07:00:00Z",
        },
    )
    assert encounter_response.status_code == 201
    encounter_id = encounter_response.json()["id"]

    before_start_response = client.post(
        f"/api/v1/hospitalization/patients/{patient_id}/daily-sheets",
        headers=auth,
        json={
            "sheet_date": "2026-06-19",
            "clinical_summary": "Fecha previa al ingreso.",
        },
    )
    assert before_start_response.status_code == 409
    assert before_start_response.json()["detail"] == (
        "Daily sheet date cannot be before hospitalization start"
    )

    create_response = client.post(
        f"/api/v1/hospitalization/patients/{patient_id}/daily-sheets",
        headers=auth,
        json={
            "sheet_date": "2026-06-20",
            "clinical_summary": "Fecha dentro del ingreso.",
        },
    )
    assert create_response.status_code == 201
    sheet_id = create_response.json()["id"]

    close_encounter_response = client.patch(
        f"/api/v1/patients/{patient_id}/encounters/{encounter_id}",
        headers=auth,
        json={
            "status": "completed",
            "ended_at": "2026-06-21T19:00:00Z",
        },
    )
    assert close_encounter_response.status_code == 200

    invalid_update_response = client.patch(
        f"/api/v1/hospitalization/patients/{patient_id}/daily-sheets/{sheet_id}",
        headers=auth,
        json={"sheet_date": "2026-06-22"},
    )
    assert invalid_update_response.status_code == 409
    assert invalid_update_response.json()["detail"] == (
        "Daily sheet date cannot be after hospitalization end"
    )


def test_hospital_daily_sheet_uses_chile_clinical_local_date(
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
            "reason": "Ingreso nocturno con borde UTC",
            "started_at": "2026-06-20T02:30:00Z",
        },
    )
    assert encounter_response.status_code == 201
    encounter_id = encounter_response.json()["id"]

    create_response = client.post(
        f"/api/v1/hospitalization/patients/{patient_id}/daily-sheets",
        headers=auth,
        json={
            "sheet_date": "2026-06-19",
            "clinical_summary": "Fecha local valida para ingreso nocturno.",
        },
    )
    assert create_response.status_code == 201
    sheet_id = create_response.json()["id"]

    close_encounter_response = client.patch(
        f"/api/v1/patients/{patient_id}/encounters/{encounter_id}",
        headers=auth,
        json={
            "status": "completed",
            "ended_at": "2026-06-22T02:30:00Z",
        },
    )
    assert close_encounter_response.status_code == 200

    local_end_date_response = client.patch(
        f"/api/v1/hospitalization/patients/{patient_id}/daily-sheets/{sheet_id}",
        headers=auth,
        json={"sheet_date": "2026-06-21"},
    )
    assert local_end_date_response.status_code == 200

    after_local_end_response = client.patch(
        f"/api/v1/hospitalization/patients/{patient_id}/daily-sheets/{sheet_id}",
        headers=auth,
        json={"sheet_date": "2026-06-22"},
    )
    assert after_local_end_response.status_code == 409
    assert after_local_end_response.json()["detail"] == (
        "Daily sheet date cannot be after hospitalization end"
    )


def test_hospital_daily_sheet_requires_active_hospitalization(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient_for_permissions(client, auth)

    response = client.post(
        f"/api/v1/hospitalization/patients/{patient_id}/daily-sheets",
        headers=auth,
        json={
            "sheet_date": "2026-06-20",
            "clinical_summary": "Intento sin ingreso activo.",
        },
    )

    assert response.status_code == 409


def test_hospital_daily_sheet_write_requires_medical_role(
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
        f"/api/v1/hospitalization/patients/{patient_id}/daily-sheets",
        headers=nursing_auth,
    )
    assert list_response.status_code == 200

    create_response = client.post(
        f"/api/v1/hospitalization/patients/{patient_id}/daily-sheets",
        headers=nursing_auth,
        json={
            "sheet_date": "2026-06-20",
            "clinical_summary": "Enfermeria no debe crear hoja medica.",
        },
    )
    assert create_response.status_code == 403
