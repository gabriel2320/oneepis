from fastapi.testclient import TestClient


def test_patient_record_flow_writes_snapshot_and_audit(
    client: TestClient,
    auth_headers,
) -> None:
    auth = auth_headers(client)
    patient_response = client.post(
        "/api/v1/patients",
        headers=auth,
        json={
            "first_name": "Elena",
            "last_name": "Rojas",
            "birth_date": "1981-04-12",
            "sex_at_birth": "female",
            "clinical_identifier": "ONE-001",
        },
    )
    assert patient_response.status_code == 201
    patient_id = patient_response.json()["id"]

    encounter_response = client.post(
        f"/api/v1/patients/{patient_id}/encounters",
        headers=auth,
        json={
            "type": "ambulatory",
            "status": "in_progress",
            "reason": "Control clinico",
            "started_at": "2026-06-20T10:00:00Z",
            "location_label": "Consulta demo",
        },
    )
    assert encounter_response.status_code == 201
    assert encounter_response.json()["reason"] == "Control clinico"
    encounter_id = encounter_response.json()["id"]

    entry_response = client.post(
        f"/api/v1/patients/{patient_id}/clinical-entries",
        headers=auth,
        json={
            "encounter_id": encounter_id,
            "kind": "progress",
            "occurred_at": "2026-06-20T10:30:00Z",
            "title": "Evolucion SOAP",
            "subjective": "Refiere mejoria.",
            "objective": "Sin dificultad respiratoria.",
            "assessment": "Evolucion estable.",
            "plan": "Mantener observacion.",
            "tags": ["soap"],
        },
    )
    assert entry_response.status_code == 201
    assert entry_response.json()["created_by"] == "medico@oneepis.local"

    allergy_response = client.post(
        f"/api/v1/patients/{patient_id}/allergies",
        headers=auth,
        json={
            "substance": "Penicilina",
            "reaction": "Exantema",
            "severity": "moderate",
            "recorded_at": "2026-06-20T10:35:00Z",
        },
    )
    assert allergy_response.status_code == 201

    medication_response = client.post(
        f"/api/v1/patients/{patient_id}/medications",
        headers=auth,
        json={
            "name": "Paracetamol",
            "dose": "1 g",
            "route": "oral",
            "frequency": "cada 8 horas",
            "started_on": "2026-06-20",
        },
    )
    assert medication_response.status_code == 201

    problem_response = client.post(
        f"/api/v1/patients/{patient_id}/problems",
        headers=auth,
        json={
            "title": "Hipertension arterial",
            "code_system": "CIE-10",
            "code": "I10",
            "onset_date": "2024-01-10",
        },
    )
    assert problem_response.status_code == 201

    diagnosis_event_response = client.post(
        f"/api/v1/patients/{patient_id}/clinical-events",
        headers=auth,
        json={
            "event_type": "diagnosis",
            "occurred_at": "2023-04-10T09:00:00Z",
            "summary": "Neumonia resuelta en control previo",
            "payload": {
                "code_system": "CIE-10",
                "code": "J18.9",
                "antecedent": {
                    "category": "diagnostico_historico",
                    "source_label": "Historia clinica previa",
                    "limit": "No equivale a problema activo actual.",
                },
            },
        },
    )
    assert diagnosis_event_response.status_code == 201
    diagnosis_event = diagnosis_event_response.json()

    procedure_event_response = client.post(
        f"/api/v1/patients/{patient_id}/clinical-events",
        headers=auth,
        json={
            "event_type": "procedure",
            "occurred_at": "2022-01-10T09:00:00Z",
            "summary": "Procedimiento previo curado",
            "payload": {
                "antecedent": {
                    "category": "procedimiento",
                    "source_label": "Historia clinica previa",
                    "limit": "No equivale a diagnostico historico.",
                },
            },
        },
    )
    assert procedure_event_response.status_code == 201

    vital_response = client.post(
        f"/api/v1/patients/{patient_id}/vital-signs",
        headers=auth,
        json={
            "measured_at": "2026-06-20T10:40:00Z",
            "temperature_c": "36.8",
            "systolic_bp": 118,
            "diastolic_bp": 72,
            "heart_rate_bpm": 78,
            "oxygen_saturation_pct": "98.0",
        },
    )
    assert vital_response.status_code == 201

    snapshot_response = client.get(f"/api/v1/patients/{patient_id}/record", headers=auth)
    assert snapshot_response.status_code == 200
    snapshot = snapshot_response.json()
    assert snapshot["patient"]["clinical_identifier"] == "ONE-001"
    assert snapshot["patient"]["clinical_status"] == "active"
    assert snapshot["patient"]["current_care_context"] == "unknown"
    assert len(snapshot["active_problems"]) == 1
    assert snapshot["active_problems"][0]["title"] == "Hipertension arterial"
    assert snapshot["active_problems"][0]["code"] == "I10"
    assert snapshot["historical_diagnoses"][0]["source_event_id"] == diagnosis_event["id"]
    assert snapshot["historical_diagnoses"][0]["title"] == "Neumonia resuelta en control previo"
    assert snapshot["historical_diagnoses"][0]["code"] == "J18.9"
    assert snapshot["historical_diagnoses"][0]["source_label"] == "Historia clinica previa"
    assert snapshot["historical_diagnoses"][0]["limit"] == "No equivale a problema activo actual."
    assert len(snapshot["historical_diagnoses"]) == 1
    assert snapshot["latest_vitals"]["heart_rate_bpm"] == 78
    assert snapshot["active_allergies"][0]["substance"] == "Penicilina"
    assert snapshot["active_medications"][0]["name"] == "Paracetamol"
    assert snapshot["active_medications"][0]["source"] is None
    assert snapshot["active_medications"][0]["missing_fields"] == ["source"]
    assert snapshot["recent_entries"][0]["title"] == "Evolucion SOAP"
    assert snapshot["recent_entries"][0]["encounter_id"] == encounter_id

    active_problems_ai_response = client.post(
        f"/api/v1/patients/{patient_id}/ai/clinical-intent",
        headers=auth,
        json={"intent_type": "active_problems"},
    )
    assert active_problems_ai_response.status_code == 200
    active_problems_ai = active_problems_ai_response.json()
    assert "Hipertension arterial" in active_problems_ai["clinical_answer"]
    assert "Neumonia resuelta en control previo" not in active_problems_ai["clinical_answer"]

    audit_response = client.get(f"/api/v1/patients/{patient_id}/audit-events", headers=auth)
    assert audit_response.status_code == 200
    audit_events = audit_response.json()
    actions = {item["action"] for item in audit_events}
    assert {
        "patient.created",
        "encounter.created",
        "clinical_entry.created",
        "allergy.created",
        "medication.created",
        "problem.created",
        "vital_sign.created",
    }.issubset(actions)
    assert {item["actor_id"] for item in audit_events} == {"medico@oneepis.local"}


def test_child_resources_return_404_for_wrong_patient(
    client: TestClient,
    auth_headers,
) -> None:
    auth = auth_headers(client)
    first = client.post(
        "/api/v1/patients",
        headers=auth,
        json={
            "first_name": "A",
            "last_name": "Paciente",
            "birth_date": "1990-01-01",
            "sex_at_birth": "unknown",
        },
    ).json()
    second = client.post(
        "/api/v1/patients",
        headers=auth,
        json={
            "first_name": "B",
            "last_name": "Paciente",
            "birth_date": "1991-01-01",
            "sex_at_birth": "unknown",
        },
    ).json()
    allergy = client.post(
        f"/api/v1/patients/{first['id']}/allergies",
        headers=auth,
        json={
            "substance": "Latex",
            "severity": "unknown",
            "recorded_at": "2026-06-20T11:00:00Z",
        },
    ).json()

    response = client.get(
        f"/api/v1/patients/{second['id']}/allergies/{allergy['id']}",
        headers=auth,
    )

    assert response.status_code == 404

    encounter = client.post(
        f"/api/v1/patients/{first['id']}/encounters",
        headers=auth,
        json={
            "type": "ambulatory",
            "reason": "Encuentro de otro paciente",
            "started_at": "2026-06-20T11:10:00Z",
        },
    ).json()

    cross_entry_response = client.post(
        f"/api/v1/patients/{second['id']}/clinical-entries",
        headers=auth,
        json={
            "encounter_id": encounter["id"],
            "kind": "progress",
            "occurred_at": "2026-06-20T11:20:00Z",
            "title": "SOAP cruzada",
        },
    )

    assert cross_entry_response.status_code == 404
