from fastapi.testclient import TestClient

from oneepis_api.schemas.clinical_record import ClinicalIntentRouteRequest
from oneepis_api.services.clinical_intent import route_clinical_intent


def test_clinical_events_timeline_and_draft_are_audited(
    client: TestClient,
    auth_headers,
    audit_events_for_patient,
) -> None:
    auth = auth_headers(client)
    patient_response = client.post(
        "/api/v1/patients",
        headers=auth,
        json={
            "first_name": "AI",
            "last_name": "Chart",
            "birth_date": "1985-05-12",
            "sex_at_birth": "female",
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
            "reason": "Control AI-Chart",
            "started_at": "2026-06-22T10:00:00Z",
        },
    )
    assert encounter_response.status_code == 201
    encounter_id = encounter_response.json()["id"]

    event_response = client.post(
        f"/api/v1/patients/{patient_id}/clinical-events",
        headers=auth,
        json={
            "encounter_id": encounter_id,
            "event_type": "symptom",
            "occurred_at": "2026-06-22T10:05:00Z",
            "summary": "Dolor toracico resuelto",
            "source_type": "manual",
            "payload": {"details": "Sin dolor al momento de la evaluacion."},
        },
    )
    assert event_response.status_code == 201
    event = event_response.json()
    assert event["created_by"] == "medico@oneepis.local"

    timeline_response = client.get(f"/api/v1/patients/{patient_id}/timeline", headers=auth)
    assert timeline_response.status_code == 200
    timeline = timeline_response.json()
    assert timeline["events"][0]["summary"] == "Dolor toracico resuelto"
    assert timeline["entries"] == []

    draft_response = client.post(
        f"/api/v1/patients/{patient_id}/ai/draft-soap-from-events",
        headers=auth,
        json={"clinical_event_ids": [event["id"]], "encounter_id": encounter_id},
    )
    assert draft_response.status_code == 200
    draft = draft_response.json()
    assert draft["requires_human_confirmation"] is True
    assert draft["provider"] == "local_rules"
    assert draft["ai_available"] is True
    assert draft["sources"][0]["clinical_event_id"] == event["id"]
    assert {
        (source["section"], source["source_type"], source["source_id"])
        for source in draft["section_sources"]
    } >= {
        ("subjective", "clinical_event", event["id"]),
        ("objective", "clinical_event", event["id"]),
    }
    assert "Dolor toracico resuelto" in draft["subjective"]

    audit_events = audit_events_for_patient(patient_id)
    actions = {item["action"] for item in audit_events}
    assert {"clinical_event.created", "ai.soap_draft.created"}.issubset(actions)
    draft_audit = next(item for item in audit_events if item["action"] == "ai.soap_draft.created")
    assert draft_audit["extra_data"]["section_sources"][0]["section"] == "subjective"


def test_clinical_event_audit_snapshots_use_allowlist(
    client: TestClient,
    auth_headers,
    audit_events_for_patient,
) -> None:
    auth = auth_headers(client)
    patient_response = client.post(
        "/api/v1/patients",
        headers=auth,
        json={
            "first_name": "Evento",
            "last_name": "Auditado",
            "birth_date": "1985-05-12",
            "sex_at_birth": "female",
        },
    )
    assert patient_response.status_code == 201
    patient_id = patient_response.json()["id"]

    event_response = client.post(
        f"/api/v1/patients/{patient_id}/clinical-events",
        headers=auth,
        json={
            "event_type": "clinical_note",
            "occurred_at": "2026-06-22T10:05:00Z",
            "summary": "Texto clinico libre no debe quedar en auditoria.",
            "payload": {"details": "Detalle narrativo sensible de prueba."},
        },
    )
    assert event_response.status_code == 201
    event_id = event_response.json()["id"]

    update_response = client.patch(
        f"/api/v1/patients/{patient_id}/clinical-events/{event_id}",
        headers=auth,
        json={
            "summary": "Texto clinico actualizado tampoco se copia.",
            "payload": {"details": "Nuevo detalle narrativo sensible."},
        },
    )
    assert update_response.status_code == 200

    audit_events = audit_events_for_patient(patient_id)
    created_audit = next(
        item
        for item in audit_events
        if item["action"] == "clinical_event.created" and item["entity_id"] == event_id
    )
    updated_audit = next(
        item
        for item in audit_events
        if item["action"] == "clinical_event.updated" and item["entity_id"] == event_id
    )
    created_after = created_audit["extra_data"]["after"]
    assert created_after["event_type"] == "clinical_note"
    assert created_after["patient_id"] == patient_id
    assert "summary" not in created_after
    assert "payload" not in created_after
    assert updated_audit["extra_data"]["fields"] == ["payload", "summary"]
    assert updated_audit["extra_data"]["before"] == {}
    assert updated_audit["extra_data"]["after"] == {}
    audit_payload = str([created_audit["extra_data"], updated_audit["extra_data"]])
    assert "Texto clinico" not in audit_payload
    assert "Detalle narrativo" not in audit_payload
    assert "Nuevo detalle" not in audit_payload


def test_clinical_event_detail_is_readable_without_audit_write(
    client: TestClient,
    auth_headers,
) -> None:
    auth = auth_headers(client)
    patient = client.post(
        "/api/v1/patients",
        headers=auth,
        json={
            "first_name": "Evento",
            "last_name": "Lectura",
            "birth_date": "1985-05-12",
            "sex_at_birth": "female",
        },
    ).json()
    event = client.post(
        f"/api/v1/patients/{patient['id']}/clinical-events",
        headers=auth,
        json={
            "event_type": "clinical_note",
            "occurred_at": "2026-06-22T10:05:00Z",
            "summary": "Evento puntual para fuente inspeccionable",
        },
    ).json()
    before_audit = client.get(
        f"/api/v1/patients/{patient['id']}/audit-events",
        headers=auth_headers(client, email="admin@oneepis.local", password="admin"),
    ).json()
    readonly_auth = auth_headers(client, email="lector@oneepis.local", password="lector")

    response = client.get(
        f"/api/v1/patients/{patient['id']}/clinical-events/{event['id']}",
        headers=readonly_auth,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == event["id"]
    assert payload["summary"] == "Evento puntual para fuente inspeccionable"
    after_audit = client.get(
        f"/api/v1/patients/{patient['id']}/audit-events",
        headers=auth_headers(client, email="admin@oneepis.local", password="admin"),
    ).json()
    assert after_audit == before_audit


def test_clinical_event_detail_requires_patient_ownership(
    client: TestClient,
    auth_headers,
) -> None:
    auth = auth_headers(client)
    first = client.post(
        "/api/v1/patients",
        headers=auth,
        json={
            "first_name": "Primer",
            "last_name": "Evento",
            "birth_date": "1980-01-01",
            "sex_at_birth": "unknown",
        },
    ).json()
    second = client.post(
        "/api/v1/patients",
        headers=auth,
        json={
            "first_name": "Segundo",
            "last_name": "Evento",
            "birth_date": "1981-01-01",
            "sex_at_birth": "unknown",
        },
    ).json()
    event = client.post(
        f"/api/v1/patients/{first['id']}/clinical-events",
        headers=auth,
        json={
            "event_type": "clinical_note",
            "occurred_at": "2026-06-22T10:05:00Z",
            "summary": "Evento de otro paciente",
        },
    ).json()

    response = client.get(
        f"/api/v1/patients/{second['id']}/clinical-events/{event['id']}",
        headers=auth,
    )
    missing_response = client.get(
        f"/api/v1/patients/{first['id']}/clinical-events/"
        "11111111-1111-4111-8111-111111111111",
        headers=auth,
    )

    assert response.status_code == 404
    assert missing_response.status_code == 404


def test_derived_clinical_event_requires_source_ref(
    client: TestClient,
    auth_headers,
) -> None:
    auth = auth_headers(client)
    patient = client.post(
        "/api/v1/patients",
        headers=auth,
        json={
            "first_name": "Fuente",
            "last_name": "Derivada",
            "birth_date": "1984-02-01",
            "sex_at_birth": "unknown",
        },
    ).json()

    response = client.post(
        f"/api/v1/patients/{patient['id']}/clinical-events",
        headers=auth,
        json={
            "event_type": "clinical_note",
            "occurred_at": "2026-06-22T10:05:00Z",
            "summary": "Evento derivado sin referencia",
            "source_type": "clinical_entry",
        },
    )

    assert response.status_code == 422
    assert "source_ref is required" in response.json()["detail"]


def test_curated_antecedent_event_is_validated_and_audited(
    client: TestClient,
    auth_headers,
    audit_events_for_patient,
) -> None:
    auth = auth_headers(client)
    auth["X-OneEpis-Correlation-ID"] = "dev-132-antecedent-validation"
    patient = client.post(
        "/api/v1/patients",
        headers=auth,
        json={
            "first_name": "Antecedente",
            "last_name": "Curado",
            "birth_date": "1984-02-01",
            "sex_at_birth": "unknown",
        },
    ).json()

    response = client.post(
        f"/api/v1/patients/{patient['id']}/clinical-events",
        headers=auth,
        json={
            "event_type": "diagnosis",
            "occurred_at": "2026-06-22T10:05:00Z",
            "summary": "Diagnostico historico confirmado por ficha previa",
            "payload": {
                "antecedent": {
                    "category": "diagnostico_historico",
                    "source_label": "Historia clinica",
                    "limit": "Fecha exacta pendiente de confirmacion humana.",
                },
            },
        },
    )

    assert response.status_code == 201
    event = response.json()
    assert event["payload"]["antecedent"]["category"] == "diagnostico_historico"
    audit_events = audit_events_for_patient(patient["id"])
    event_audit = next(item for item in audit_events if item["entity_id"] == event["id"])
    assert event_audit["action"] == "clinical_event.created"
    assert event_audit["actor_id"] == "medico@oneepis.local"
    assert event_audit["correlation_id"] == "dev-132-antecedent-validation"
    assert event_audit["extra_data"]["patient_id"] == patient["id"]


def test_curated_antecedent_event_rejects_invalid_payload(
    client: TestClient,
    auth_headers,
) -> None:
    auth = auth_headers(client)
    patient = client.post(
        "/api/v1/patients",
        headers=auth,
        json={
            "first_name": "Antecedente",
            "last_name": "Invalido",
            "birth_date": "1984-02-01",
            "sex_at_birth": "unknown",
        },
    ).json()

    invalid_category = client.post(
        f"/api/v1/patients/{patient['id']}/clinical-events",
        headers=auth,
        json={
            "event_type": "diagnosis",
            "occurred_at": "2026-06-22T10:05:00Z",
            "summary": "Antecedente con categoria invalida",
            "payload": {
                "antecedent": {
                    "category": "riesgo_clinico",
                    "source_label": "Historia clinica",
                    "limit": "No usar como riesgo estructurado.",
                },
            },
        },
    )
    missing_limit = client.post(
        f"/api/v1/patients/{patient['id']}/clinical-events",
        headers=auth,
        json={
            "event_type": "diagnosis",
            "occurred_at": "2026-06-22T10:05:00Z",
            "summary": "Antecedente sin limite",
            "payload": {
                "antecedent": {
                    "category": "diagnostico_historico",
                    "source_label": "Historia clinica",
                },
            },
        },
    )

    assert invalid_category.status_code == 422
    assert "category is not allowed" in invalid_category.json()["detail"]
    assert missing_limit.status_code == 422
    assert "requires category, source_label and limit" in missing_limit.json()["detail"]


def test_curated_antecedent_category_must_match_event_type(
    client: TestClient,
    auth_headers,
) -> None:
    auth = auth_headers(client)
    patient = client.post(
        "/api/v1/patients",
        headers=auth,
        json={
            "first_name": "Antecedente",
            "last_name": "Tipo",
            "birth_date": "1984-02-01",
            "sex_at_birth": "unknown",
        },
    ).json()

    valid_diagnosis = client.post(
        f"/api/v1/patients/{patient['id']}/clinical-events",
        headers=auth,
        json={
            "event_type": "diagnosis",
            "occurred_at": "2026-06-22T10:05:00Z",
            "summary": "Diagnostico historico curado",
            "payload": {
                "antecedent": {
                    "category": "diagnostico_historico",
                    "source_label": "Historia clinica",
                    "limit": "No equivale a problema activo actual.",
                },
            },
        },
    )
    invalid_diagnosis_type = client.post(
        f"/api/v1/patients/{patient['id']}/clinical-events",
        headers=auth,
        json={
            "event_type": "symptom",
            "occurred_at": "2026-06-22T10:10:00Z",
            "summary": "Diagnostico historico con tipo incorrecto",
            "payload": {
                "antecedent": {
                    "category": "diagnostico_historico",
                    "source_label": "Historia clinica",
                    "limit": "Debe registrarse como diagnostico.",
                },
            },
        },
    )
    valid_procedure = client.post(
        f"/api/v1/patients/{patient['id']}/clinical-events",
        headers=auth,
        json={
            "event_type": "procedure",
            "occurred_at": "2026-06-22T10:15:00Z",
            "summary": "Procedimiento previo curado",
            "payload": {
                "antecedent": {
                    "category": "procedimiento",
                    "source_label": "Historia quirurgica",
                    "limit": "No equivale a indicacion ejecutable.",
                },
            },
        },
    )
    invalid_procedure_type = client.post(
        f"/api/v1/patients/{patient['id']}/clinical-events",
        headers=auth,
        json={
            "event_type": "clinical_note",
            "occurred_at": "2026-06-22T10:20:00Z",
            "summary": "Procedimiento con tipo incorrecto",
            "payload": {
                "antecedent": {
                    "category": "procedimiento",
                    "source_label": "Historia quirurgica",
                    "limit": "Debe registrarse como procedimiento.",
                },
            },
        },
    )

    assert valid_diagnosis.status_code == 201
    assert invalid_diagnosis_type.status_code == 422
    assert "requires event_type diagnosis" in invalid_diagnosis_type.json()["detail"]
    assert valid_procedure.status_code == 201
    assert invalid_procedure_type.status_code == 422
    assert "requires event_type procedure" in invalid_procedure_type.json()["detail"]

    incompatible_update = client.patch(
        f"/api/v1/patients/{patient['id']}/clinical-events/{valid_diagnosis.json()['id']}",
        headers=auth,
        json={"event_type": "symptom"},
    )

    assert incompatible_update.status_code == 422
    assert "requires event_type diagnosis" in incompatible_update.json()["detail"]


def test_curated_antecedent_update_rejects_invalid_payload(
    client: TestClient,
    auth_headers,
) -> None:
    auth = auth_headers(client)
    patient = client.post(
        "/api/v1/patients",
        headers=auth,
        json={
            "first_name": "Antecedente",
            "last_name": "Actualizado",
            "birth_date": "1984-02-01",
            "sex_at_birth": "unknown",
        },
    ).json()
    event = client.post(
        f"/api/v1/patients/{patient['id']}/clinical-events",
        headers=auth,
        json={
            "event_type": "clinical_note",
            "occurred_at": "2026-06-22T10:05:00Z",
            "summary": "Evento por curar",
        },
    ).json()

    response = client.patch(
        f"/api/v1/patients/{patient['id']}/clinical-events/{event['id']}",
        headers=auth,
        json={"payload": {"antecedent": "diagnostico_historico"}},
    )

    assert response.status_code == 422
    assert "payload.antecedent must be an object" in response.json()["detail"]


def test_derived_clinical_event_cannot_clear_source_ref(
    client: TestClient,
    auth_headers,
) -> None:
    auth = auth_headers(client)
    patient = client.post(
        "/api/v1/patients",
        headers=auth,
        json={
            "first_name": "Fuente",
            "last_name": "Persistente",
            "birth_date": "1984-02-01",
            "sex_at_birth": "unknown",
        },
    ).json()
    entry = client.post(
        f"/api/v1/patients/{patient['id']}/clinical-entries",
        headers=auth,
        json={
            "kind": "progress",
            "status": "signed",
            "occurred_at": "2026-06-22T09:00:00Z",
            "title": "Evolucion fuente",
            "subjective": "Control.",
        },
    ).json()
    event = client.post(
        f"/api/v1/patients/{patient['id']}/clinical-events",
        headers=auth,
        json={
            "event_type": "clinical_note",
            "occurred_at": "2026-06-22T10:05:00Z",
            "summary": "Evento derivado con referencia",
            "source_type": "clinical_entry",
            "source_ref": entry["id"],
        },
    ).json()

    response = client.patch(
        f"/api/v1/patients/{patient['id']}/clinical-events/{event['id']}",
        headers=auth,
        json={"source_ref": None},
    )

    assert response.status_code == 422
    assert "source_ref is required" in response.json()["detail"]


def test_draft_rejects_events_from_other_patient(
    client: TestClient,
    auth_headers,
) -> None:
    auth = auth_headers(client)
    first = client.post(
        "/api/v1/patients",
        headers=auth,
        json={
            "first_name": "Primer",
            "last_name": "Paciente",
            "birth_date": "1980-01-01",
            "sex_at_birth": "unknown",
        },
    ).json()
    second = client.post(
        "/api/v1/patients",
        headers=auth,
        json={
            "first_name": "Segundo",
            "last_name": "Paciente",
            "birth_date": "1981-01-01",
            "sex_at_birth": "unknown",
        },
    ).json()
    event = client.post(
        f"/api/v1/patients/{first['id']}/clinical-events",
        headers=auth,
        json={
            "event_type": "clinical_note",
            "occurred_at": "2026-06-22T10:05:00Z",
            "summary": "Evento de otro paciente",
        },
    ).json()

    response = client.post(
        f"/api/v1/patients/{second['id']}/ai/draft-soap-from-events",
        headers=auth,
        json={"clinical_event_ids": [event["id"]]},
    )

    assert response.status_code == 404


def test_clinical_intent_returns_sources_and_audit(
    client: TestClient,
    auth_headers,
    audit_events_for_patient,
) -> None:
    auth = auth_headers(client)
    patient = client.post(
        "/api/v1/patients",
        headers=auth,
        json={
            "first_name": "Intent",
            "last_name": "Clinico",
            "birth_date": "1979-03-01",
            "sex_at_birth": "male",
        },
    ).json()
    event = client.post(
        f"/api/v1/patients/{patient['id']}/clinical-events",
        headers=auth,
        json={
            "event_type": "clinical_note",
            "occurred_at": "2026-06-22T12:00:00Z",
            "summary": "Neumonia adquirida en la comunidad: paciente afebril y sin dolor",
        },
    ).json()
    previous_exam_response = client.post(
        f"/api/v1/patients/{patient['id']}/clinical-events",
        headers=auth,
        json={
            "event_type": "exam_result",
            "occurred_at": "2026-06-21T11:00:00Z",
            "summary": "Creatinina 1.1 mg/dL",
            "payload": {"code": "creatinina", "value": "1.1", "unit": "mg/dL"},
        },
    )
    assert previous_exam_response.status_code == 201
    exam_event = client.post(
        f"/api/v1/patients/{patient['id']}/clinical-events",
        headers=auth,
        json={
            "event_type": "exam_result",
            "occurred_at": "2026-06-22T13:00:00Z",
            "summary": "Creatinina subio a 1.6 mg/dL",
            "payload": {"code": "creatinina", "value": "1.6", "unit": "mg/dL"},
        },
    ).json()
    previous_panel_response = client.post(
        f"/api/v1/patients/{patient['id']}/clinical-events",
        headers=auth,
        json={
            "event_type": "exam_result",
            "occurred_at": "2026-06-21T13:30:00Z",
            "summary": "Panel inflamatorio previo",
            "payload": {"results": [{"code": "pcr", "value": "180", "unit": "mg/L"}]},
        },
    )
    assert previous_panel_response.status_code == 201
    current_panel_response = client.post(
        f"/api/v1/patients/{patient['id']}/clinical-events",
        headers=auth,
        json={
            "event_type": "exam_result",
            "occurred_at": "2026-06-22T13:30:00Z",
            "summary": "Panel inflamatorio actual",
            "payload": {"results": [{"code": "pcr", "value": "92", "unit": "mg/L"}]},
        },
    )
    assert current_panel_response.status_code == 201
    medication_event = client.post(
        f"/api/v1/patients/{patient['id']}/clinical-events",
        headers=auth,
        json={
            "event_type": "medication",
            "occurred_at": "2026-06-22T14:00:00Z",
            "summary": "Se ajusta dosis de enoxaparina",
            "payload": {
                "action": "dose_changed",
                "name": "Enoxaparina",
                "previous_dose": "40 mg cada 24 h",
                "dose": "20 mg cada 24 h",
            },
        },
    ).json()
    active_medication_response = client.post(
        f"/api/v1/patients/{patient['id']}/medications",
        headers=auth,
        json={
            "name": "Losartan",
            "route": "oral",
        },
    )
    assert active_medication_response.status_code == 201
    problem = client.post(
        f"/api/v1/patients/{patient['id']}/problems",
        headers=auth,
        json={
            "title": "Neumonia adquirida en la comunidad",
            "notes": "Completar duracion antibiotica.",
        },
    ).json()
    entry_response = client.post(
        f"/api/v1/patients/{patient['id']}/clinical-entries",
        headers=auth,
        json={
            "kind": "progress",
            "status": "signed",
            "occurred_at": "2026-06-21T12:00:00Z",
            "title": "Evolucion previa",
            "subjective": "Sin fiebre.",
            "objective": "Estable.",
            "assessment": "Neumonia en tratamiento.",
            "plan": "Mantener antibioticos.",
        },
    )
    assert entry_response.status_code == 201
    entry = entry_response.json()
    previous_vitals_response = client.post(
        f"/api/v1/patients/{patient['id']}/vital-signs",
        headers=auth,
        json={
            "measured_at": "2026-06-21T12:00:00Z",
            "temperature_c": "38.2",
            "systolic_bp": 130,
            "heart_rate_bpm": 104,
            "oxygen_saturation_pct": "92.0",
        },
    )
    assert previous_vitals_response.status_code == 201
    current_vitals_response = client.post(
        f"/api/v1/patients/{patient['id']}/vital-signs",
        headers=auth,
        json={
            "measured_at": "2026-06-22T12:00:00Z",
            "temperature_c": "36.8",
            "systolic_bp": 118,
            "heart_rate_bpm": 82,
            "oxygen_saturation_pct": "96.0",
        },
    )
    assert current_vitals_response.status_code == 201

    response = client.post(
        f"/api/v1/patients/{patient['id']}/ai/clinical-intent",
        headers=auth,
        json={"intent_type": "summarize_patient", "mode": "read"},
    )

    assert response.status_code == 200
    intent = response.json()
    assert intent["intent_type"] == "summarize_patient"
    assert "Intent Clinico" in intent["clinical_answer"]
    assert any(source["source_id"] == event["id"] for source in intent["sources"])
    assert any(section["title"] == "Eventos recientes" for section in intent["context_sections"])
    assert any(mark["status"] == "confirmed" for mark in intent["evidence_marks"])
    assert intent["change_set"]["baseline"] == entry["title"]
    assert event["summary"] in intent["change_set"]["new_items"]
    assert "Temperatura bajo de 38.2 a 36.8 C." in intent["change_set"]["rule_findings"]
    assert "Saturacion O2 subio de 92 a 96 %." in intent["change_set"]["rule_findings"]
    assert (
        f"Nuevo examen registrado: {exam_event['summary']}."
        in intent["change_set"]["rule_findings"]
    )
    assert "Creatinina subio de 1.1 a 1.6 mg/dL." in intent["change_set"]["rule_findings"]
    assert "PCR bajo de 180 a 92 mg/L." in intent["change_set"]["rule_findings"]
    assert (
        f"Nuevo evento de medicacion registrado: {medication_event['summary']}."
        in intent["change_set"]["rule_findings"]
    )
    assert (
        "Dosis modificada: Enoxaparina de 40 mg cada 24 h a 20 mg cada 24 h."
        in intent["change_set"]["rule_findings"]
    )
    assert (
        "Revisar medicamento activo sin dosis: Losartan."
        in intent["change_set"]["rule_findings"]
    )
    assert (
        "Revisar medicamento activo sin frecuencia: Losartan."
        in intent["change_set"]["rule_findings"]
    )
    assert (
        f"Revisar evento de medicacion sin problema activo asociado: "
        f"{medication_event['summary']}."
        in intent["change_set"]["rule_findings"]
    )
    review_item_types = {item["item_type"] for item in intent["review_items"]}
    assert {
        "missing_medication_dose",
        "missing_medication_frequency",
        "unlinked_medication_event",
    }.issubset(review_item_types)
    assert any(
        item["source_id"] == medication_event["id"]
        and item["suggested_action"] == "Vincular a un problema activo o crear uno si corresponde."
        for item in intent["review_items"]
    )
    review_item = next(
        item for item in intent["review_items"] if item["item_type"] == "unlinked_medication_event"
    )
    decision_response = client.post(
        f"/api/v1/patients/{patient['id']}/ai/review-item-decision",
        headers=auth,
        json={
            "decision": "accepted",
            "item_type": review_item["item_type"],
            "label": review_item["label"],
            "detail": review_item["detail"],
            "source_type": review_item["source_type"],
            "source_id": review_item["source_id"],
            "note": "Revisado en test.",
        },
    )
    assert decision_response.status_code == 200
    decision = decision_response.json()
    assert decision["audited"] is True
    assert decision["decision"] == "accepted"
    assert any(
        finding.endswith("evento(s) recientes sin problema activo asociado.")
        for finding in intent["change_set"]["rule_findings"]
    )
    assert any(
        context["problem_id"] == problem["id"]
        and context["evidence"][0]["source_id"] == event["id"]
        for context in intent["problem_contexts"]
    )
    assert intent["requires_human_confirmation"] is False

    audit_events = audit_events_for_patient(patient["id"])
    actions = {item["action"] for item in audit_events}
    assert "ai.clinical_intent.created" in actions
    review_decision = next(
        item for item in audit_events if item["action"] == "ai.review_item.decided"
    )
    assert review_decision["extra_data"]["decision"] == "accepted"
    assert review_decision["extra_data"]["applies_changes"] is False

    repeated_response = client.post(
        f"/api/v1/patients/{patient['id']}/ai/clinical-intent",
        headers=auth,
        json={"intent_type": "summarize_patient", "mode": "read"},
    )
    assert repeated_response.status_code == 200
    repeated_intent = repeated_response.json()
    repeated_item = next(
        item
        for item in repeated_intent["review_items"]
        if item["item_type"] == "unlinked_medication_event"
    )
    assert repeated_item["decision_status"] == "accepted"
    assert repeated_item["decision_actor_id"] == "medico@oneepis.local"
    assert repeated_item["decision_at"] is not None
    assert repeated_item["decision_audit_event_id"] == review_decision["id"]
    soap_action = next(
        action
        for action in repeated_intent["proposed_actions"]
        if action["action_type"] == "create_soap_draft"
    )
    assert soap_action["action_id"] == "create_soap_draft:preparar_evolucion_soap"
    assert soap_action["description"]
    assert soap_action["confirmation_label"] == "Revisar y confirmar"

    action_decision_response = client.post(
        f"/api/v1/patients/{patient['id']}/ai/action-decision",
        headers=auth,
        json={
            "decision": "accepted",
            "action_type": soap_action["action_type"],
            "action_id": soap_action["action_id"],
            "label": soap_action["label"],
            "description": soap_action["description"],
            "requires_confirmation": soap_action["requires_confirmation"],
            "note": "Accion revisada en test.",
        },
    )
    assert action_decision_response.status_code == 200
    action_decision = action_decision_response.json()
    assert action_decision["audited"] is True
    assert action_decision["applies_changes"] is False
    assert action_decision["decision"] == "accepted"

    action_audit_events = audit_events_for_patient(patient["id"])
    action_audit = next(
        item
        for item in action_audit_events
        if item["action"] == "ai.clinical_action.decided"
    )
    assert action_audit["extra_data"]["action_id"] == soap_action["action_id"]
    assert action_audit["extra_data"]["applies_changes"] is False


def test_clinical_intent_router_is_directed_and_audited(
    client: TestClient,
    auth_headers,
) -> None:
    auth = auth_headers(client)
    patient = client.post(
        "/api/v1/patients",
        headers=auth,
        json={
            "first_name": "Router",
            "last_name": "Clinico",
            "birth_date": "1982-02-02",
            "sex_at_birth": "unknown",
        },
    ).json()

    response = client.post(
        f"/api/v1/patients/{patient['id']}/ai/clinical-intent-route",
        headers=auth,
        json={"text": "Prepara evolucion medica de hoy"},
    )

    assert response.status_code == 200
    routed = response.json()
    assert routed["recognized"] is True
    assert routed["intent_type"] == "draft_soap"
    assert routed["mode"] == "draft"
    assert routed["suggested_actions"][0]["requires_confirmation"] is True
    assert routed["suggested_actions"][0]["action_id"]
    assert routed["suggested_actions"][0]["description"]

    fallback_response = client.post(
        f"/api/v1/patients/{patient['id']}/ai/clinical-intent-route",
        headers=auth,
        json={"text": "haz magia rara"},
    )

    assert fallback_response.status_code == 200
    fallback = fallback_response.json()
    assert fallback["recognized"] is False
    assert fallback["intent_type"] is None
    assert fallback["fallback_options"]

    audit_response = client.get(
        f"/api/v1/patients/{patient['id']}/audit-events",
        headers=auth_headers(client, email="admin@oneepis.local", password="admin"),
    )
    actions = [item["action"] for item in audit_response.json()]
    assert actions.count("ai.clinical_intent.routed") == 2


def test_clinical_intent_route_returns_direct_form_action():
    routed = route_clinical_intent(
        ClinicalIntentRouteRequest(text="Registrar medicamento losartan 50 mg")
    )

    assert routed.recognized is True
    assert routed.intent_type is None
    assert routed.mode == "structured_proposal"
    assert routed.suggested_actions[0].action_type == "create_event"
    assert routed.suggested_actions[0].label == "Registrar medicacion"
    assert routed.suggested_actions[0].requires_confirmation is True
    description = routed.suggested_actions[0].description
    assert "Texto original: Registrar medicamento losartan 50 mg" in description
