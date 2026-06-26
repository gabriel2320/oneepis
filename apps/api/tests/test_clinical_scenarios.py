from fastapi.testclient import TestClient
from patient_ai_helpers import audit_events, create_patient


def test_patient_unifies_ambulatory_hospital_and_longitudinal_context(
    client: TestClient,
    auth_headers,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient(
        client,
        auth,
        first_name="Escenario",
        last_name="Canonico",
    )

    appointment = _create_appointment(client, auth, patient_id)
    ambulatory_encounter = _create_ambulatory_encounter(client, auth, patient_id)
    ambulatory_entry = _create_progress_entry(
        client,
        auth,
        patient_id,
        encounter_id=ambulatory_encounter["id"],
        occurred_at="2026-06-24T09:25:00Z",
        title="Control ambulatorio",
    )
    hospitalization_encounter = _create_hospitalization_encounter(client, auth, patient_id)
    bed = _create_hospital_bed(client, auth, encounter_id=hospitalization_encounter["id"])
    indication = _create_hospital_indication(client, auth, patient_id)
    allergy = _create_allergy(client, auth, patient_id)
    medication = _create_medication(client, auth, patient_id)
    risk = _create_risk(client, auth, patient_id, encounter_id=hospitalization_encounter["id"])

    context_response = client.get(f"/api/v1/patients/{patient_id}/context", headers=auth)
    record_response = client.get(f"/api/v1/patients/{patient_id}/record", headers=auth)

    assert context_response.status_code == 200
    context = context_response.json()
    assert context["patient_id"] == patient_id
    assert context["derived_care_context"] == "hospitalization"
    assert context["active_hospitalization"]["id"] == hospitalization_encounter["id"]
    assert context["active_encounter"]["id"] == hospitalization_encounter["id"]
    assert context["recent_ambulatory_encounters"][0]["id"] == ambulatory_encounter["id"]
    assert context["allergies"][0]["id"] == allergy["id"]
    assert context["active_medications"][0]["id"] == medication["id"]
    assert context["active_risks"][0]["id"] == risk["id"]
    assert context["active_risks"][0]["encounter_id"] == hospitalization_encounter["id"]
    assert context["active_risks"][0]["encounter_type"] == "hospitalization"
    assert context["timeline"][0]["item_id"] == ambulatory_entry["id"]
    assert context["timeline"][0]["encounter_id"] == ambulatory_encounter["id"]
    assert context["applies_changes"] is False
    assert "Contexto limitado" in context["limits"][0]

    assert record_response.status_code == 200
    record = record_response.json()
    assert record["patient"]["id"] == patient_id
    assert record["active_allergies"][0]["id"] == allergy["id"]
    assert record["active_medications"][0]["id"] == medication["id"]
    assert record["recent_entries"][0]["encounter_id"] == ambulatory_encounter["id"]

    events = audit_events(client, auth, patient_id)
    actions = {event["action"] for event in events}
    assert {
        "appointment.created",
        "encounter.created",
        "clinical_entry.created",
        "hospital_bed.created",
        "hospital_indication.created",
        "allergy.created",
        "medication.created",
        "clinical_risk.created",
    }.issubset(actions)
    assert indication["status"] == "draft"
    assert indication["encounter_id"] == hospitalization_encounter["id"]
    assert bed["encounter_id"] == hospitalization_encounter["id"]
    assert appointment["patient_id"] == patient_id


def test_nursing_and_readonly_stay_inside_scenario_permissions(
    client: TestClient,
    auth_headers,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient(client, auth, first_name="Escenario", last_name="Permisos")
    _create_hospitalization_encounter(client, auth, patient_id)
    nursing_auth = auth_headers(client, email="enfermeria@oneepis.local", password="enfermeria")
    readonly_auth = auth_headers(client, email="lector@oneepis.local", password="lector")

    nursing_preconsult = client.post(
        f"/api/v1/patients/{patient_id}/encounters",
        headers=nursing_auth,
        json={
            "type": "ambulatory",
            "status": "in_progress",
            "workflow_kind": "ambulatory_preconsult",
            "reason": "Preconsulta ambulatoria",
            "started_at": "2026-06-24T08:30:00Z",
            "notes": "Preconsulta vinculada a cita ambulatoria.",
        },
    )
    nursing_indication = client.post(
        f"/api/v1/hospitalization/patients/{patient_id}/indications",
        headers=nursing_auth,
        json={
            "indicated_at": "2026-06-25T10:00:00Z",
            "title": "Indicacion no permitida",
            "indication_text": "Enfermeria no crea indicaciones medicas.",
        },
    )
    readonly_context = client.get(f"/api/v1/patients/{patient_id}/context", headers=readonly_auth)
    readonly_medication = client.post(
        f"/api/v1/patients/{patient_id}/medications",
        headers=readonly_auth,
        json={"name": "No permitido"},
    )

    assert nursing_preconsult.status_code == 201
    assert nursing_preconsult.json()["workflow_kind"] == "ambulatory_preconsult"
    assert nursing_indication.status_code == 403
    assert readonly_context.status_code == 200
    assert readonly_context.json()["applies_changes"] is False
    assert readonly_medication.status_code == 403


def _create_appointment(client: TestClient, auth: dict[str, str], patient_id: str) -> dict:
    response = client.post(
        f"/api/v1/patients/{patient_id}/appointments",
        headers=auth,
        json={
            "starts_at": "2026-06-24T09:00:00Z",
            "ends_at": "2026-06-24T09:30:00Z",
            "reason": "Control ambulatorio",
            "location_label": "Box 1",
        },
    )
    assert response.status_code == 201
    return response.json()


def _create_ambulatory_encounter(
    client: TestClient,
    auth: dict[str, str],
    patient_id: str,
) -> dict:
    response = client.post(
        f"/api/v1/patients/{patient_id}/encounters",
        headers=auth,
        json={
            "type": "ambulatory",
            "status": "completed",
            "reason": "Control ambulatorio",
            "started_at": "2026-06-24T09:00:00Z",
            "ended_at": "2026-06-24T09:30:00Z",
            "location_label": "Consultas ambulatorias",
        },
    )
    assert response.status_code == 201
    return response.json()


def _create_hospitalization_encounter(
    client: TestClient,
    auth: dict[str, str],
    patient_id: str,
) -> dict:
    response = client.post(
        f"/api/v1/patients/{patient_id}/encounters",
        headers=auth,
        json={
            "type": "hospitalization",
            "status": "in_progress",
            "reason": "Ingreso hospitalario",
            "started_at": "2026-06-25T08:00:00Z",
            "location_label": "Medicina interna",
        },
    )
    assert response.status_code == 201
    return response.json()


def _create_progress_entry(
    client: TestClient,
    auth: dict[str, str],
    patient_id: str,
    *,
    encounter_id: str,
    occurred_at: str,
    title: str,
) -> dict:
    response = client.post(
        f"/api/v1/patients/{patient_id}/clinical-entries",
        headers=auth,
        json={
            "encounter_id": encounter_id,
            "kind": "progress",
            "status": "draft",
            "occurred_at": occurred_at,
            "title": title,
            "subjective": "Refiere control clinico.",
            "objective": "Sin hallazgos criticos.",
            "assessment": "Evolucion estable.",
            "plan": "Mantener seguimiento.",
        },
    )
    assert response.status_code == 201
    return response.json()


def _create_hospital_bed(client: TestClient, auth: dict[str, str], *, encounter_id: str) -> dict:
    response = client.post(
        "/api/v1/hospitalization/beds",
        headers=auth,
        json={
            "ward": "Medicina",
            "room": "301",
            "bed_label": "A",
            "status": "occupied",
            "encounter_id": encounter_id,
        },
    )
    assert response.status_code == 201
    return response.json()


def _create_hospital_indication(client: TestClient, auth: dict[str, str], patient_id: str) -> dict:
    response = client.post(
        f"/api/v1/hospitalization/patients/{patient_id}/indications",
        headers=auth,
        json={
            "indicated_at": "2026-06-25T10:00:00Z",
            "title": "Indicacion de observacion",
            "indication_text": "Mantener observacion clinica y reevaluar.",
            "safety_notes": "No equivale a orden firmada.",
        },
    )
    assert response.status_code == 201
    return response.json()


def _create_allergy(client: TestClient, auth: dict[str, str], patient_id: str) -> dict:
    response = client.post(
        f"/api/v1/patients/{patient_id}/allergies",
        headers=auth,
        json={
            "substance": "Penicilina",
            "reaction": "Exantema",
            "severity": "moderate",
            "recorded_at": "2026-06-24T09:35:00Z",
        },
    )
    assert response.status_code == 201
    return response.json()


def _create_medication(client: TestClient, auth: dict[str, str], patient_id: str) -> dict:
    response = client.post(
        f"/api/v1/patients/{patient_id}/medications",
        headers=auth,
        json={
            "name": "Paracetamol",
            "dose": "500 mg",
            "route": "oral",
            "frequency": "cada 8 horas",
            "started_on": "2026-06-24",
        },
    )
    assert response.status_code == 201
    return response.json()


def _create_risk(
    client: TestClient,
    auth: dict[str, str],
    patient_id: str,
    *,
    encounter_id: str,
) -> dict:
    response = client.post(
        f"/api/v1/patients/{patient_id}/clinical-risks",
        headers=auth,
        json={
            "risk_type": "fall",
            "severity": "moderate",
            "source_kind": "manual",
            "encounter_id": encounter_id,
            "reason": "Riesgo de caida observado durante hospitalizacion.",
            "human_action": "Mantener medidas preventivas.",
        },
    )
    assert response.status_code == 201
    return response.json()
