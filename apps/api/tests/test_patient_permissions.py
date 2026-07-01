from fastapi.testclient import TestClient


def test_patient_routes_require_authentication(client: TestClient) -> None:
    response = client.get("/api/v1/patients")

    assert response.status_code == 401


def test_readonly_user_can_read_patient_index_for_navigation(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient_for_permissions(client, auth)
    readonly_auth = auth_headers(client, email="lector@oneepis.local", password="lector")

    response = client.get("/api/v1/patients?limit=50", headers=readonly_auth)

    assert response.status_code == 200
    assert patient_id in [patient["id"] for patient in response.json()]


def test_readonly_user_cannot_write_patient(
    client: TestClient,
    auth_headers,
) -> None:
    auth = auth_headers(client, email="lector@oneepis.local", password="lector")

    response = client.post(
        "/api/v1/patients",
        headers=auth,
        json={
            "first_name": "Solo",
            "last_name": "Lectura",
            "birth_date": "1990-01-01",
            "sex_at_birth": "unknown",
        },
    )

    assert response.status_code == 403


def test_readonly_user_cannot_update_patient(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
) -> None:
    patient_id = create_patient_for_permissions(client, auth_headers(client))
    readonly_auth = auth_headers(client, email="lector@oneepis.local", password="lector")

    response = client.patch(
        f"/api/v1/patients/{patient_id}",
        headers=readonly_auth,
        json={"preferred_name": "Lectura"},
    )

    assert response.status_code == 403


def test_readonly_user_can_read_patient_snapshot(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
) -> None:
    patient_id = create_patient_for_permissions(client, auth_headers(client))
    readonly_auth = auth_headers(client, email="lector@oneepis.local", password="lector")

    response = client.get(f"/api/v1/patients/{patient_id}/record", headers=readonly_auth)

    assert response.status_code == 200
    assert response.json()["patient"]["id"] == patient_id


def test_nursing_can_record_vitals_but_not_medical_actions(
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

    vitals_response = client.post(
        f"/api/v1/patients/{patient_id}/vital-signs",
        headers=nursing_auth,
        json={
            "measured_at": "2026-06-20T12:00:00Z",
            "systolic_bp": 120,
            "diastolic_bp": 70,
            "heart_rate_bpm": 80,
        },
    )
    assert vitals_response.status_code == 201
    assert vitals_response.json()["heart_rate_bpm"] == 80

    entry_response = client.post(
        f"/api/v1/patients/{patient_id}/clinical-entries",
        headers=nursing_auth,
        json={
            "kind": "progress",
            "occurred_at": "2026-06-20T12:05:00Z",
            "title": "Evolucion SOAP",
        },
    )
    assert entry_response.status_code == 403

    medication_response = client.post(
        f"/api/v1/patients/{patient_id}/medications",
        headers=nursing_auth,
        json={"name": "Ibuprofeno", "started_on": "2026-06-20"},
    )
    assert medication_response.status_code == 403

    problem_response = client.post(
        f"/api/v1/patients/{patient_id}/problems",
        headers=nursing_auth,
        json={"title": "Dolor toracico"},
    )
    assert problem_response.status_code == 403

    encounter_response = client.post(
        f"/api/v1/patients/{patient_id}/encounters",
        headers=nursing_auth,
        json={
            "type": "hospitalization",
            "reason": "Ingreso hospitalario",
            "started_at": "2026-06-20T12:10:00Z",
        },
    )
    assert encounter_response.status_code == 403

    ai_response = client.post(
        f"/api/v1/patients/{patient_id}/ai/suggestions",
        headers=nursing_auth,
        json={"focus": "summary"},
    )
    assert ai_response.status_code == 403


def test_nursing_cannot_write_allergies(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient_for_permissions(client, auth)
    nursing_auth = auth_headers(
        client,
        email="enfermeria@oneepis.local",
        password="enfermeria",
    )

    create_response = client.post(
        f"/api/v1/patients/{patient_id}/allergies",
        headers=nursing_auth,
        json={
            "substance": "Penicilina",
            "reaction": "Exantema",
            "recorded_at": "2026-06-20T12:00:00Z",
        },
    )
    assert create_response.status_code == 403

    allowed_create_response = client.post(
        f"/api/v1/patients/{patient_id}/allergies",
        headers=auth,
        json={
            "substance": "Aspirina",
            "reaction": "Urticaria",
            "recorded_at": "2026-06-20T12:05:00Z",
        },
    )
    assert allowed_create_response.status_code == 201
    allergy_id = allowed_create_response.json()["id"]

    update_response = client.patch(
        f"/api/v1/patients/{patient_id}/allergies/{allergy_id}",
        headers=nursing_auth,
        json={"severity": "severe"},
    )
    assert update_response.status_code == 403

    delete_response = client.delete(
        f"/api/v1/patients/{patient_id}/allergies/{allergy_id}",
        headers=nursing_auth,
    )
    assert delete_response.status_code == 403


def test_readonly_user_cannot_write_clinical_events(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient_for_permissions(client, auth)
    readonly_auth = auth_headers(client, email="lector@oneepis.local", password="lector")

    create_response = client.post(
        f"/api/v1/patients/{patient_id}/clinical-events",
        headers=readonly_auth,
        json={
            "event_type": "clinical_note",
            "occurred_at": "2026-06-20T12:00:00Z",
            "summary": "Evento solo lectura",
        },
    )
    assert create_response.status_code == 403

    allowed_create_response = client.post(
        f"/api/v1/patients/{patient_id}/clinical-events",
        headers=auth,
        json={
            "event_type": "clinical_note",
            "occurred_at": "2026-06-20T12:05:00Z",
            "summary": "Evento medico",
        },
    )
    assert allowed_create_response.status_code == 201
    event_id = allowed_create_response.json()["id"]

    update_response = client.patch(
        f"/api/v1/patients/{patient_id}/clinical-events/{event_id}",
        headers=readonly_auth,
        json={"summary": "Intento solo lectura"},
    )
    assert update_response.status_code == 403


def test_nursing_cannot_create_or_convert_diagnosis_events(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient_for_permissions(client, auth)
    nursing_auth = auth_headers(
        client,
        email="enfermeria@oneepis.local",
        password="enfermeria",
    )

    nursing_note = client.post(
        f"/api/v1/patients/{patient_id}/clinical-events",
        headers=nursing_auth,
        json={
            "event_type": "clinical_note",
            "occurred_at": "2026-06-20T12:00:00Z",
            "summary": "Nota contextual de enfermeria",
        },
    )
    nursing_diagnosis = client.post(
        f"/api/v1/patients/{patient_id}/clinical-events",
        headers=nursing_auth,
        json={
            "event_type": "diagnosis",
            "occurred_at": "2026-06-20T12:05:00Z",
            "summary": "Diagnostico historico no autorizado",
            "payload": {
                "antecedent": {
                    "category": "diagnostico_historico",
                    "source_label": "Historia clinica",
                    "limit": "No equivale a problema activo actual.",
                },
            },
        },
    )
    medical_note = client.post(
        f"/api/v1/patients/{patient_id}/clinical-events",
        headers=auth,
        json={
            "event_type": "clinical_note",
            "occurred_at": "2026-06-20T12:10:00Z",
            "summary": "Evento medico por clasificar",
        },
    )
    convert_to_diagnosis = client.patch(
        f"/api/v1/patients/{patient_id}/clinical-events/{medical_note.json()['id']}",
        headers=nursing_auth,
        json={"event_type": "diagnosis"},
    )
    attach_historical_payload = client.patch(
        f"/api/v1/patients/{patient_id}/clinical-events/{nursing_note.json()['id']}",
        headers=nursing_auth,
        json={
            "payload": {
                "antecedent": {
                    "category": "diagnostico_historico",
                    "source_label": "Historia clinica",
                    "limit": "Debe ser curado por rol medico.",
                },
            },
        },
    )
    allowed_diagnosis = client.post(
        f"/api/v1/patients/{patient_id}/clinical-events",
        headers=auth,
        json={
            "event_type": "diagnosis",
            "occurred_at": "2026-06-20T12:15:00Z",
            "summary": "Diagnostico historico curado por medico",
            "payload": {
                "antecedent": {
                    "category": "diagnostico_historico",
                    "source_label": "Historia clinica",
                    "limit": "No equivale a problema activo actual.",
                },
            },
        },
    )

    assert nursing_note.status_code == 201
    assert nursing_diagnosis.status_code == 403
    assert medical_note.status_code == 201
    assert convert_to_diagnosis.status_code == 403
    assert attach_historical_payload.status_code == 403
    assert allowed_diagnosis.status_code == 201


def test_nursing_cannot_write_curated_procedure_or_longitudinal_plan_events(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient_for_permissions(client, auth)
    nursing_auth = auth_headers(
        client,
        email="enfermeria@oneepis.local",
        password="enfermeria",
    )

    nursing_note = client.post(
        f"/api/v1/patients/{patient_id}/clinical-events",
        headers=nursing_auth,
        json={
            "event_type": "clinical_note",
            "occurred_at": "2026-06-20T12:00:00Z",
            "summary": "Nota contextual de enfermeria",
        },
    )
    nursing_procedure = client.post(
        f"/api/v1/patients/{patient_id}/clinical-events",
        headers=nursing_auth,
        json={
            "event_type": "procedure",
            "occurred_at": "2026-06-20T12:05:00Z",
            "summary": "Procedimiento curado no autorizado",
            "payload": {
                "antecedent": {
                    "category": "procedimiento",
                    "source_label": "Historia quirurgica",
                    "limit": "No equivale a indicacion ejecutable.",
                },
            },
        },
    )
    nursing_plan_payload = client.patch(
        f"/api/v1/patients/{patient_id}/clinical-events/{nursing_note.json()['id']}",
        headers=nursing_auth,
        json={
            "event_type": "care_plan",
            "payload": {
                "antecedent": {
                    "category": "plan_longitudinal",
                    "source_label": "Plan historico",
                    "limit": "Debe ser curado por rol medico.",
                },
            },
        },
    )
    allowed_procedure = client.post(
        f"/api/v1/patients/{patient_id}/clinical-events",
        headers=auth,
        json={
            "event_type": "procedure",
            "occurred_at": "2026-06-20T12:10:00Z",
            "summary": "Procedimiento curado por medico",
            "payload": {
                "antecedent": {
                    "category": "procedimiento",
                    "source_label": "Historia quirurgica",
                    "limit": "No equivale a indicacion ejecutable.",
                },
            },
        },
    )
    nursing_update_procedure = client.patch(
        f"/api/v1/patients/{patient_id}/clinical-events/{allowed_procedure.json()['id']}",
        headers=nursing_auth,
        json={"summary": "Intento de editar procedimiento"},
    )

    assert nursing_note.status_code == 201
    assert nursing_procedure.status_code == 403
    assert nursing_plan_payload.status_code == 403
    assert allowed_procedure.status_code == 201
    assert nursing_update_procedure.status_code == 403
