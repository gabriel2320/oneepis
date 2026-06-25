from fastapi.testclient import TestClient


def _create_patient(client: TestClient, auth: dict[str, str]) -> str:
    response = client.post(
        "/api/v1/patients",
        headers=auth,
        json={
            "first_name": "Audit",
            "last_name": "Patient",
            "birth_date": "1980-01-01",
            "sex_at_birth": "unknown",
        },
    )
    assert response.status_code == 201
    return str(response.json()["id"])


def test_vital_sign_delete_marks_entered_in_error_without_physical_delete(
    client: TestClient,
    auth_headers,
) -> None:
    auth = auth_headers(client)
    patient = client.post(
        "/api/v1/patients",
        headers=auth,
        json={
            "first_name": "Vital",
            "last_name": "Correction",
            "birth_date": "1980-01-01",
            "sex_at_birth": "unknown",
        },
    ).json()
    patient_id = patient["id"]
    vital = client.post(
        f"/api/v1/patients/{patient_id}/vital-signs",
        headers=auth,
        json={
            "measured_at": "2026-06-20T10:40:00Z",
            "heart_rate_bpm": 78,
            "notes": "Control ingresado por error.",
        },
    ).json()

    response = client.delete(
        f"/api/v1/patients/{patient_id}/vital-signs/{vital['id']}",
        headers=auth,
    )

    assert response.status_code == 204
    second_delete = client.delete(
        f"/api/v1/patients/{patient_id}/vital-signs/{vital['id']}",
        headers=auth,
    )
    assert second_delete.status_code == 204
    direct = client.get(
        f"/api/v1/patients/{patient_id}/vital-signs/{vital['id']}",
        headers=auth,
    )
    assert direct.status_code == 200
    assert direct.json()["status"] == "entered_in_error"
    assert client.get(f"/api/v1/patients/{patient_id}/vital-signs", headers=auth).json() == []
    record = client.get(f"/api/v1/patients/{patient_id}/record", headers=auth).json()
    assert record["latest_vitals"] is None
    timeline = client.get(
        f"/api/v1/patients/{patient_id}/assistant/timeline",
        headers=auth,
    ).json()
    assert all(item["item_type"] != "vital_sign" for item in timeline["items"])
    audit = client.get(f"/api/v1/patients/{patient_id}/audit-events", headers=auth).json()
    delete_events = [item for item in audit if item["action"] == "vital_sign.deleted"]
    assert len(delete_events) == 1
    delete_audit = delete_events[0]
    assert delete_audit["extra_data"]["before"] == {"status": "active"}
    assert delete_audit["extra_data"]["after"] == {"status": "entered_in_error"}


def test_vital_sign_entered_in_error_is_terminal_and_delete_only(
    client: TestClient,
    auth_headers,
) -> None:
    auth = auth_headers(client)
    patient_id = _create_patient(client, auth)

    create_invalid = client.post(
        f"/api/v1/patients/{patient_id}/vital-signs",
        headers=auth,
        json={
            "measured_at": "2026-06-20T10:40:00Z",
            "heart_rate_bpm": 78,
            "status": "entered_in_error",
        },
    )
    assert create_invalid.status_code == 422

    vital = client.post(
        f"/api/v1/patients/{patient_id}/vital-signs",
        headers=auth,
        json={
            "measured_at": "2026-06-20T10:40:00Z",
            "heart_rate_bpm": 78,
        },
    ).json()

    invalid_patch = client.patch(
        f"/api/v1/patients/{patient_id}/vital-signs/{vital['id']}",
        headers=auth,
        json={"status": "entered_in_error"},
    )
    assert invalid_patch.status_code == 422

    delete_response = client.delete(
        f"/api/v1/patients/{patient_id}/vital-signs/{vital['id']}",
        headers=auth,
    )
    assert delete_response.status_code == 204

    terminal_patch = client.patch(
        f"/api/v1/patients/{patient_id}/vital-signs/{vital['id']}",
        headers=auth,
        json={"notes": "Reactivate attempt"},
    )
    assert terminal_patch.status_code == 409


def test_clinical_entry_delete_marks_entered_in_error_without_physical_delete(
    client: TestClient,
    auth_headers,
) -> None:
    auth = auth_headers(client)
    patient = client.post(
        "/api/v1/patients",
        headers=auth,
        json={
            "first_name": "Entry",
            "last_name": "Correction",
            "birth_date": "1980-01-01",
            "sex_at_birth": "unknown",
        },
    ).json()
    patient_id = patient["id"]
    entry = client.post(
        f"/api/v1/patients/{patient_id}/clinical-entries",
        headers=auth,
        json={
            "kind": "progress",
            "occurred_at": "2026-06-20T10:30:00Z",
            "title": "Borrador ingresado por error",
            "assessment": "No debe aparecer en vistas operativas.",
        },
    ).json()

    response = client.delete(
        f"/api/v1/patients/{patient_id}/clinical-entries/{entry['id']}",
        headers=auth,
    )

    assert response.status_code == 204
    second_delete = client.delete(
        f"/api/v1/patients/{patient_id}/clinical-entries/{entry['id']}",
        headers=auth,
    )
    assert second_delete.status_code == 204
    direct = client.get(
        f"/api/v1/patients/{patient_id}/clinical-entries/{entry['id']}",
        headers=auth,
    )
    assert direct.status_code == 200
    assert direct.json()["status"] == "entered_in_error"
    assert client.get(f"/api/v1/patients/{patient_id}/clinical-entries", headers=auth).json() == []
    timeline = client.get(f"/api/v1/patients/{patient_id}/timeline", headers=auth).json()
    assert timeline["entries"] == []
    assistant_timeline = client.get(
        f"/api/v1/patients/{patient_id}/assistant/timeline",
        headers=auth,
    ).json()
    assert all(item["item_type"] != "clinical_entry" for item in assistant_timeline["items"])
    audit = client.get(f"/api/v1/patients/{patient_id}/audit-events", headers=auth).json()
    delete_events = [item for item in audit if item["action"] == "clinical_entry.deleted"]
    assert len(delete_events) == 1
    delete_audit = delete_events[0]
    assert delete_audit["extra_data"]["before"] == {"status": "draft"}
    assert delete_audit["extra_data"]["after"] == {"status": "entered_in_error"}


def test_clinical_entry_entered_in_error_is_terminal_and_delete_only(
    client: TestClient,
    auth_headers,
) -> None:
    auth = auth_headers(client)
    patient_id = _create_patient(client, auth)

    create_invalid = client.post(
        f"/api/v1/patients/{patient_id}/clinical-entries",
        headers=auth,
        json={
            "kind": "progress",
            "status": "entered_in_error",
            "occurred_at": "2026-06-20T10:30:00Z",
            "title": "Invalid entered in error create",
        },
    )
    assert create_invalid.status_code == 422

    entry = client.post(
        f"/api/v1/patients/{patient_id}/clinical-entries",
        headers=auth,
        json={
            "kind": "progress",
            "occurred_at": "2026-06-20T10:30:00Z",
            "title": "Draft to correct",
        },
    ).json()

    invalid_patch = client.patch(
        f"/api/v1/patients/{patient_id}/clinical-entries/{entry['id']}",
        headers=auth,
        json={"status": "entered_in_error"},
    )
    assert invalid_patch.status_code == 422

    signed = client.post(
        f"/api/v1/patients/{patient_id}/clinical-entries",
        headers=auth,
        json={
            "kind": "progress",
            "status": "signed",
            "occurred_at": "2026-06-20T11:30:00Z",
            "title": "Signed internal entry",
        },
    ).json()
    signed_delete = client.delete(
        f"/api/v1/patients/{patient_id}/clinical-entries/{signed['id']}",
        headers=auth,
    )
    assert signed_delete.status_code == 409

    delete_response = client.delete(
        f"/api/v1/patients/{patient_id}/clinical-entries/{entry['id']}",
        headers=auth,
    )
    assert delete_response.status_code == 204

    terminal_patch = client.patch(
        f"/api/v1/patients/{patient_id}/clinical-entries/{entry['id']}",
        headers=auth,
        json={"title": "Reactivate attempt"},
    )
    assert terminal_patch.status_code == 409


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
    assert snapshot["active_problems"][0]["title"] == "Hipertension arterial"
    assert snapshot["active_problems"][0]["code"] == "I10"
    assert snapshot["latest_vitals"]["heart_rate_bpm"] == 78
    assert snapshot["active_allergies"][0]["substance"] == "Penicilina"
    assert snapshot["active_medications"][0]["name"] == "Paracetamol"
    assert snapshot["recent_entries"][0]["title"] == "Evolucion SOAP"
    assert snapshot["recent_entries"][0]["encounter_id"] == encounter_id

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
