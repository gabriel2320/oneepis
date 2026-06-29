from datetime import UTC, date, datetime

from fastapi.testclient import TestClient
from patient_ai_helpers import (
    audit_events,
    create_entry,
    create_event,
    create_lab_panel,
    create_patient,
    create_problem,
    create_vitals,
)

from oneepis_api.api.v1.routes.patient_assistant import _date_or_created_at


def test_assistant_timeline_date_items_preserve_timezone() -> None:
    fallback = datetime(2026, 6, 20, 12, tzinfo=UTC)

    occurred_at = _date_or_created_at(date(2026, 6, 18), fallback)

    assert occurred_at == datetime(2026, 6, 18, tzinfo=UTC)


def test_assistant_timeline_reads_longitudinal_sources_without_writing(
    client: TestClient,
    auth_headers,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient(client, auth, first_name="Assistant", last_name="Timeline")
    encounter_response = client.post(
        f"/api/v1/patients/{patient_id}/encounters",
        headers=auth,
        json={
            "type": "ambulatory",
            "reason": "Control longitudinal",
            "started_at": "2026-06-20T10:00:00Z",
            "location_label": "Consulta",
        },
    )
    assert encounter_response.status_code == 201
    create_entry(
        client,
        auth,
        patient_id,
        title="Evolucion timeline",
        assessment="Paciente estable para lectura longitudinal.",
    )
    create_event(
        client,
        auth,
        patient_id,
        summary="Evento longitudinal relevante",
        occurred_at="2026-06-20T10:45:00Z",
    )
    create_vitals(
        client,
        auth,
        patient_id,
        measured_at="2026-06-20T10:50:00Z",
        systolic_bp=118,
        heart_rate_bpm=76,
        oxygen_saturation_pct="98.0",
    )
    create_lab_panel(
        client,
        auth,
        patient_id,
        panel_name="Perfil renal timeline",
        result_name="Creatinina",
        code="creatinina",
        value="1.20",
        unit="mg/dL",
    )
    create_problem(client, auth, patient_id, title="Hipertension arterial", code="I10")
    medication_response = client.post(
        f"/api/v1/patients/{patient_id}/medications",
        headers=auth,
        json={
            "name": "Losartan",
            "dose": "50 mg",
            "frequency": "cada 24 horas",
            "started_on": "2026-06-18",
        },
    )
    assert medication_response.status_code == 201
    allergy_response = client.post(
        f"/api/v1/patients/{patient_id}/allergies",
        headers=auth,
        json={
            "substance": "Penicilina",
            "reaction": "Exantema",
            "recorded_at": "2026-06-19T09:00:00Z",
        },
    )
    assert allergy_response.status_code == 201
    before_audit = audit_events(client, auth, patient_id)

    response = client.get(
        f"/api/v1/patients/{patient_id}/assistant/timeline?limit=10",
        headers=auth,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["patient_id"] == patient_id
    assert payload["applies_changes"] is False
    assert payload["missing_data"] == []
    assert payload["has_more"] is False
    item_types = [item["item_type"] for item in payload["items"]]
    assert {
        "encounter",
        "clinical_entry",
        "clinical_event",
        "vital_sign",
        "medication",
        "problem",
        "allergy",
        "lab_result",
    }.issubset(set(item_types))
    occurred_values = [item["occurred_at"] for item in payload["items"]]
    assert occurred_values == sorted(occurred_values, reverse=True)
    vital_item = next(item for item in payload["items"] if item["item_type"] == "vital_sign")
    assert vital_item["source_path"].endswith("/vital-signs/" + vital_item["item_id"])
    event_item = next(item for item in payload["items"] if item["item_type"] == "clinical_event")
    assert event_item["summary"] == "Evento longitudinal relevante"
    assert event_item["source_path"].endswith("/clinical-events/" + event_item["item_id"])
    lab_item = next(item for item in payload["items"] if item["item_type"] == "lab_result")
    assert lab_item["label"] == "Creatinina"
    assert "Perfil renal timeline" in lab_item["summary"]
    assert "/lab-panels/" in lab_item["source_path"]
    assert lab_item["source_path"].endswith("/results/" + lab_item["item_id"])
    after_audit = audit_events(client, auth, patient_id)
    assert after_audit == before_audit


def test_assistant_timeline_reads_historical_diagnoses_as_context_without_writing(
    client: TestClient,
    auth_headers,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient(client, auth, first_name="Assistant", last_name="Historico")
    encounter_response = client.post(
        f"/api/v1/patients/{patient_id}/encounters",
        headers=auth,
        json={
            "type": "hospitalization",
            "status": "in_progress",
            "reason": "Ingreso con antecedente historico",
            "started_at": "2026-06-20T08:00:00Z",
        },
    )
    assert encounter_response.status_code == 201
    encounter_id = encounter_response.json()["id"]
    diagnosis_response = client.post(
        f"/api/v1/patients/{patient_id}/clinical-events",
        headers=auth,
        json={
            "encounter_id": encounter_id,
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
    assert diagnosis_response.status_code == 201
    event_id = diagnosis_response.json()["id"]
    before_audit = audit_events(client, auth, patient_id)

    response = client.get(
        f"/api/v1/patients/{patient_id}/assistant/timeline?limit=10",
        headers=auth,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["applies_changes"] is False
    historical_item = next(
        item for item in payload["items"] if item["source_label"] == "Historia clinica previa"
    )
    assert historical_item["item_type"] == "clinical_event"
    assert historical_item["item_id"] == event_id
    assert historical_item["label"] == "Neumonia resuelta en control previo"
    assert historical_item["summary"] == (
        "Historia clinica previa: No equivale a problema activo actual. (CIE-10: J18.9)"
    )
    assert historical_item["source_path"].endswith("/clinical-events/" + event_id)
    assert historical_item["encounter_id"] == encounter_id
    assert historical_item["encounter_type"] == "hospitalization"
    assert historical_item["encounter_status"] == "in_progress"
    assert historical_item["scope"] == "hospitalization"
    assert all(item["source_label"] != "historical_diagnoses" for item in payload["items"])
    assert [item["item_id"] for item in payload["items"]].count(event_id) == 1
    after_audit = audit_events(client, auth, patient_id)
    assert after_audit == before_audit


def test_assistant_timeline_exposes_encounter_metadata(
    client: TestClient,
    auth_headers,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient(client, auth, first_name="Timeline", last_name="Encounter")
    encounter_response = client.post(
        f"/api/v1/patients/{patient_id}/encounters",
        headers=auth,
        json={
            "type": "ambulatory",
            "status": "in_progress",
            "reason": "Control con contexto",
            "started_at": "2026-06-20T10:00:00Z",
        },
    )
    assert encounter_response.status_code == 201
    encounter_id = encounter_response.json()["id"]
    entry_response = client.post(
        f"/api/v1/patients/{patient_id}/clinical-entries",
        headers=auth,
        json={
            "encounter_id": encounter_id,
            "kind": "progress",
            "occurred_at": "2026-06-20T10:30:00Z",
            "title": "Evolucion con episodio",
            "assessment": "Seguimiento ambulatorio estructurado.",
        },
    )
    assert entry_response.status_code == 201
    lab_response = client.post(
        f"/api/v1/patients/{patient_id}/lab-panels",
        headers=auth,
        json={
            "encounter_id": encounter_id,
            "occurred_at": "2026-06-20T10:45:00Z",
            "panel_name": "Perfil con episodio",
            "results": [{"name": "Creatinina", "value": "1.0"}],
        },
    )
    assert lab_response.status_code == 201

    response = client.get(
        f"/api/v1/patients/{patient_id}/assistant/timeline?limit=10",
        headers=auth,
    )

    assert response.status_code == 200
    items = response.json()["items"]
    encounter_item = next(item for item in items if item["item_type"] == "encounter")
    entry_item = next(item for item in items if item["item_type"] == "clinical_entry")
    lab_item = next(item for item in items if item["item_type"] == "lab_result")
    assert encounter_item["encounter_id"] == encounter_id
    assert encounter_item["encounter_type"] == "ambulatory"
    assert encounter_item["encounter_status"] == "in_progress"
    assert encounter_item["scope"] == "ambulatory"
    assert entry_item["encounter_id"] == encounter_id
    assert entry_item["encounter_type"] == "ambulatory"
    assert lab_item["encounter_id"] == encounter_id
    assert lab_item["encounter_type"] == "ambulatory"


def test_assistant_timeline_allows_readonly_user(
    client: TestClient,
    auth_headers,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient(client, auth, first_name="Timeline", last_name="Lector")
    create_event(client, auth, patient_id, summary="Lectura longitudinal")
    readonly_auth = auth_headers(client, email="lector@oneepis.local", password="lector")

    response = client.get(
        f"/api/v1/patients/{patient_id}/assistant/timeline",
        headers=readonly_auth,
    )

    assert response.status_code == 200
    assert response.json()["items"][0]["summary"] == "Lectura longitudinal"


def test_assistant_timeline_reports_missing_data_and_limit(
    client: TestClient,
    auth_headers,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient(client, auth, first_name="Timeline", last_name="Limit")
    create_event(
        client,
        auth,
        patient_id,
        summary="Primer evento",
        occurred_at="2026-06-20T10:00:00Z",
    )
    create_event(
        client,
        auth,
        patient_id,
        summary="Segundo evento",
        occurred_at="2026-06-20T11:00:00Z",
    )

    response = client.get(
        f"/api/v1/patients/{patient_id}/assistant/timeline?limit=1",
        headers=auth,
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["items"]) == 1
    assert payload["items"][0]["summary"] == "Segundo evento"
    assert payload["has_more"] is True
    expected_warning = "Timeline limitado a 1 items; aumenta limit o consulta dominios fuente."
    assert payload["warnings"] == [expected_warning]
    assert "No hay signos vitales estructurados." in payload["missing_data"]


def test_assistant_timeline_unknown_patient_returns_404(
    client: TestClient,
    auth_headers,
) -> None:
    auth = auth_headers(client)

    response = client.get(
        "/api/v1/patients/11111111-1111-4111-8111-111111111111/assistant/timeline",
        headers=auth,
    )

    assert response.status_code == 404


def test_assistant_search_reads_sources_without_writing(
    client: TestClient,
    auth_headers,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient(client, auth, first_name="Assistant", last_name="Search")
    encounter_response = client.post(
        f"/api/v1/patients/{patient_id}/encounters",
        headers=auth,
        json={
            "type": "ambulatory",
            "reason": "Control diabetes",
            "started_at": "2026-06-20T08:00:00Z",
        },
    )
    assert encounter_response.status_code == 201
    create_entry(
        client,
        auth,
        patient_id,
        title="Evolucion metabolica",
        assessment="Diabetes mellitus en seguimiento longitudinal.",
    )
    create_event(
        client,
        auth,
        patient_id,
        summary="Diabetes con ajuste educativo",
        occurred_at="2026-06-20T10:45:00Z",
    )
    create_problem(client, auth, patient_id, title="Diabetes mellitus", code="E11")
    medication_response = client.post(
        f"/api/v1/patients/{patient_id}/medications",
        headers=auth,
        json={"name": "Metformina", "dose": "850 mg", "started_on": "2026-06-18"},
    )
    assert medication_response.status_code == 201
    allergy_response = client.post(
        f"/api/v1/patients/{patient_id}/allergies",
        headers=auth,
        json={
            "substance": "Penicilina",
            "reaction": "Exantema",
            "recorded_at": "2026-06-19T09:00:00Z",
        },
    )
    assert allergy_response.status_code == 201
    vital_response = client.post(
        f"/api/v1/patients/{patient_id}/vital-signs",
        headers=auth,
        json={
            "measured_at": "2026-06-20T11:00:00Z",
            "heart_rate_bpm": 76,
            "notes": "Control diabetes sin signos de alarma.",
        },
    )
    assert vital_response.status_code == 201
    panel = create_lab_panel(
        client,
        auth,
        patient_id,
        panel_name="Control diabetes",
        result_name="Glicemia",
        code="glucosa",
        value="142",
        unit="mg/dL",
    )
    before_audit = audit_events(client, auth, patient_id)

    response = client.get(
        f"/api/v1/patients/{patient_id}/assistant/search?q= diabetes &limit=10",
        headers=auth,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["patient_id"] == patient_id
    assert payload["query"] == "diabetes"
    assert payload["applies_changes"] is False
    assert payload["missing_data"] == []
    assert payload["has_more"] is False
    item_types = [item["item_type"] for item in payload["results"]]
    assert {
        "encounter",
        "clinical_entry",
        "clinical_event",
        "problem",
        "vital_sign",
        "lab_result",
    }.issubset(set(item_types))
    occurred_values = [item["occurred_at"] for item in payload["results"]]
    assert occurred_values == sorted(occurred_values, reverse=True)
    entry_item = next(item for item in payload["results"] if item["item_type"] == "clinical_entry")
    assert entry_item["matched_fields"] == ["assessment"]
    assert "Diabetes mellitus" in entry_item["snippet"]
    assert entry_item["source_path"].endswith("/clinical-entries/" + entry_item["item_id"])
    event_item = next(item for item in payload["results"] if item["item_type"] == "clinical_event")
    assert event_item["source_path"].endswith("/clinical-events/" + event_item["item_id"])
    problem_item = next(item for item in payload["results"] if item["item_type"] == "problem")
    assert problem_item["source_path"].endswith("/problems/" + problem_item["item_id"])
    lab_item = next(item for item in payload["results"] if item["item_type"] == "lab_result")
    assert lab_item["item_id"] == panel["results"][0]["id"]
    assert lab_item["matched_fields"] == ["panel_name"]
    assert "/lab-panels/" in lab_item["source_path"]
    assert lab_item["source_path"].endswith("/results/" + lab_item["item_id"])
    after_audit = audit_events(client, auth, patient_id)
    assert after_audit == before_audit


def test_assistant_search_allows_readonly_user(
    client: TestClient,
    auth_headers,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient(client, auth, first_name="Search", last_name="Lector")
    create_event(client, auth, patient_id, summary="Antecedente familiar relevante")
    readonly_auth = auth_headers(client, email="lector@oneepis.local", password="lector")

    response = client.get(
        f"/api/v1/patients/{patient_id}/assistant/search?q=familiar",
        headers=readonly_auth,
    )

    assert response.status_code == 200
    assert response.json()["results"][0]["snippet"] == "Antecedente familiar relevante"


def test_assistant_search_reports_limit_and_empty_results(
    client: TestClient,
    auth_headers,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient(client, auth, first_name="Search", last_name="Limit")
    create_event(
        client,
        auth,
        patient_id,
        summary="Dolor toracico inicial",
        occurred_at="2026-06-20T10:00:00Z",
    )
    create_event(
        client,
        auth,
        patient_id,
        summary="Dolor toracico en reevaluacion",
        occurred_at="2026-06-20T11:00:00Z",
    )

    limited_response = client.get(
        f"/api/v1/patients/{patient_id}/assistant/search?q=dolor&limit=1",
        headers=auth,
    )
    empty_response = client.get(
        f"/api/v1/patients/{patient_id}/assistant/search?q=asma",
        headers=auth,
    )

    assert limited_response.status_code == 200
    limited_payload = limited_response.json()
    assert len(limited_payload["results"]) == 1
    assert limited_payload["results"][0]["snippet"] == "Dolor toracico en reevaluacion"
    assert limited_payload["has_more"] is True
    expected_warning = "Busqueda limitada a 1 resultados; afina la consulta o abre dominios fuente."
    assert limited_payload["warnings"] == [expected_warning]
    assert empty_response.status_code == 200
    assert empty_response.json()["results"] == []
    expected_missing = "No se encontraron coincidencias clinicas estructuradas para la busqueda."
    assert empty_response.json()["missing_data"] == [expected_missing]


def test_assistant_search_unknown_patient_returns_404(
    client: TestClient,
    auth_headers,
) -> None:
    auth = auth_headers(client)

    response = client.get(
        "/api/v1/patients/11111111-1111-4111-8111-111111111111/assistant/search?q=dolor",
        headers=auth,
    )

    assert response.status_code == 404


def test_assistant_chart_returns_vitals_and_exam_series_without_writing(
    client: TestClient,
    auth_headers,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient(client, auth, first_name="Assistant", last_name="Chart")
    create_vitals(
        client,
        auth,
        patient_id,
        measured_at="2026-06-20T10:00:00Z",
        heart_rate_bpm=72,
        oxygen_saturation_pct="96.0",
    )
    create_vitals(
        client,
        auth,
        patient_id,
        measured_at="2026-06-20T11:00:00Z",
        heart_rate_bpm=80,
        oxygen_saturation_pct="98.0",
    )
    first_exam = client.post(
        f"/api/v1/patients/{patient_id}/clinical-events",
        headers=auth,
        json={
            "event_type": "exam_result",
            "occurred_at": "2026-06-20T09:00:00Z",
            "summary": "Creatinina basal",
            "source_type": "manual",
            "payload": {"code": "creatinina", "value": "1.1", "unit": "mg/dL"},
        },
    )
    second_exam = client.post(
        f"/api/v1/patients/{patient_id}/clinical-events",
        headers=auth,
        json={
            "event_type": "exam_result",
            "occurred_at": "2026-06-20T12:00:00Z",
            "summary": "Creatinina control",
            "source_type": "manual",
            "payload": {"results": [{"code": "creatinina", "value": "1.6", "unit": "mg/dL"}]},
        },
    )
    assert first_exam.status_code == 201
    assert second_exam.status_code == 201
    lab_panel = client.post(
        f"/api/v1/patients/{patient_id}/lab-panels",
        headers=auth,
        json={
            "occurred_at": "2026-06-20T08:00:00Z",
            "panel_name": "Perfil renal estructurado",
            "results": [
                {
                    "code": "creatinina",
                    "name": "Creatinina",
                    "value": "0.9",
                    "numeric_value": "0.9",
                    "unit": "mg/dL",
                },
                {
                    "code": "creatinina",
                    "name": "Creatinina corregida",
                    "value": "9.9",
                    "numeric_value": "9.9",
                    "unit": "mg/dL",
                    "status": "entered_in_error",
                },
            ],
        },
    )
    assert lab_panel.status_code == 201
    before_audit = audit_events(client, auth, patient_id)

    response = client.post(
        f"/api/v1/patients/{patient_id}/assistant/chart",
        headers=auth,
        json={"series": ["heart_rate_bpm", "exam:creatinina"], "limit": 10},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["patient_id"] == patient_id
    assert payload["applies_changes"] is False
    assert payload["missing_data"] == []
    assert payload["has_more"] is False
    series_by_key = {series["key"]: series for series in payload["series"]}
    assert set(series_by_key) == {"heart_rate_bpm", "exam:creatinina"}
    heart_points = series_by_key["heart_rate_bpm"]["points"]
    assert [point["value"] for point in heart_points] == [72.0, 80.0]
    assert heart_points[0]["source_path"].endswith("/vital-signs/" + heart_points[0]["source_id"])
    exam_series = series_by_key["exam:creatinina"]
    assert exam_series["unit"] == "mg/dL"
    assert [point["value"] for point in exam_series["points"]] == [0.9, 1.1, 1.6]
    assert {point["source_type"] for point in exam_series["points"]} == {
        "clinical_event",
        "lab_result",
    }
    lab_point = exam_series["points"][0]
    assert lab_point["source_type"] == "lab_result"
    assert "/lab-panels/" in lab_point["source_path"]
    legacy_point = exam_series["points"][1]
    assert legacy_point["source_path"].endswith(
        "/clinical-events/" + legacy_point["source_id"]
    )
    after_audit = audit_events(client, auth, patient_id)
    assert after_audit == before_audit


def test_assistant_chart_allows_readonly_user(
    client: TestClient,
    auth_headers,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient(client, auth, first_name="Chart", last_name="Lector")
    create_vitals(
        client,
        auth,
        patient_id,
        measured_at="2026-06-20T10:00:00Z",
        heart_rate_bpm=72,
    )
    readonly_auth = auth_headers(client, email="lector@oneepis.local", password="lector")

    response = client.post(
        f"/api/v1/patients/{patient_id}/assistant/chart",
        headers=readonly_auth,
        json={"series": ["heart_rate_bpm"]},
    )

    assert response.status_code == 200
    assert response.json()["series"][0]["points"][0]["value"] == 72.0


def test_assistant_chart_reports_missing_data_limit_and_unsupported_series(
    client: TestClient,
    auth_headers,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient(client, auth, first_name="Chart", last_name="Limit")
    create_vitals(
        client,
        auth,
        patient_id,
        measured_at="2026-06-20T10:00:00Z",
        heart_rate_bpm=72,
    )
    create_vitals(
        client,
        auth,
        patient_id,
        measured_at="2026-06-20T11:00:00Z",
        heart_rate_bpm=80,
    )

    limited_response = client.post(
        f"/api/v1/patients/{patient_id}/assistant/chart",
        headers=auth,
        json={"series": ["heart_rate_bpm", "no_soportada"], "limit": 1},
    )
    empty_patient_id = create_patient(client, auth, first_name="Chart", last_name="Empty")
    empty_response = client.post(
        f"/api/v1/patients/{empty_patient_id}/assistant/chart",
        headers=auth,
        json={},
    )

    assert limited_response.status_code == 200
    limited_payload = limited_response.json()
    assert limited_payload["has_more"] is True
    assert "Series no soportadas: no_soportada." in limited_payload["warnings"]
    assert "Datos graficables limitados a 1 registros por dominio." in limited_payload["warnings"]
    assert empty_response.status_code == 200
    empty_missing = empty_response.json()["missing_data"]
    assert "No hay signos vitales estructurados para graficar." in empty_missing
    assert "No hay examenes estructurados ni eventos exam_result para graficar." in empty_missing
    assert "No hay datos numericos graficables para las series solicitadas." in empty_missing


def test_assistant_chart_unknown_patient_returns_404(
    client: TestClient,
    auth_headers,
) -> None:
    auth = auth_headers(client)

    response = client.post(
        "/api/v1/patients/11111111-1111-4111-8111-111111111111/assistant/chart",
        headers=auth,
        json={},
    )

    assert response.status_code == 404


def test_assistant_correlate_returns_explainable_sources_without_writing(
    client: TestClient,
    auth_headers,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient(client, auth, first_name="Assistant", last_name="Correlate")
    create_vitals(
        client,
        auth,
        patient_id,
        measured_at="2026-06-20T10:00:00Z",
        temperature_c="38.5",
    )
    event_response = client.post(
        f"/api/v1/patients/{patient_id}/clinical-events",
        headers=auth,
        json={
            "event_type": "exam_result",
            "occurred_at": "2026-06-20T11:00:00Z",
            "summary": "PCR elevada por sospecha infeccion",
            "source_type": "manual",
            "payload": {"code": "pcr", "value": "180", "unit": "mg/L"},
        },
    )
    assert event_response.status_code == 201
    before_audit = audit_events(client, auth, patient_id)

    response = client.post(
        f"/api/v1/patients/{patient_id}/assistant/correlate",
        headers=auth,
        json={"presets": ["fever_infection"], "limit": 10},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["patient_id"] == patient_id
    assert payload["applies_changes"] is False
    assert payload["missing_data"] == ["No hay medicacion activa estructurada para correlacionar."]
    assert payload["has_more"] is False
    correlation = payload["correlations"][0]
    assert correlation["preset"] == "fever_infection"
    assert correlation["missing_data"] == []
    assert "interpretacion humana" in correlation["summary"]
    labels = {item["label"] for item in correlation["evidence"]}
    assert labels == {"Fiebre", "Marcador infeccioso textual"}
    assert {item["source_type"] for item in correlation["evidence"]} == {
        "vital_sign",
        "clinical_event",
    }
    event_evidence = next(
        item for item in correlation["evidence"] if item["source_type"] == "clinical_event"
    )
    assert event_evidence["source_path"].endswith("/clinical-events/" + event_evidence["source_id"])
    after_audit = audit_events(client, auth, patient_id)
    assert after_audit == before_audit


def test_assistant_correlate_allows_readonly_user(
    client: TestClient,
    auth_headers,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient(client, auth, first_name="Correlate", last_name="Lector")
    create_vitals(
        client,
        auth,
        patient_id,
        measured_at="2026-06-20T10:00:00Z",
        oxygen_saturation_pct="89.0",
    )
    create_event(client, auth, patient_id, summary="Paciente con disnea")
    readonly_auth = auth_headers(client, email="lector@oneepis.local", password="lector")

    response = client.post(
        f"/api/v1/patients/{patient_id}/assistant/correlate",
        headers=readonly_auth,
        json={"presets": ["respiratory_oxygen"]},
    )

    assert response.status_code == 200
    assert response.json()["correlations"][0]["missing_data"] == []


def test_assistant_correlate_reads_structured_labs_without_legacy_event(
    client: TestClient,
    auth_headers,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient(client, auth, first_name="Correlate", last_name="Lab")
    create_vitals(
        client,
        auth,
        patient_id,
        measured_at="2026-06-20T10:00:00Z",
        temperature_c="38.4",
    )
    lab_panel = client.post(
        f"/api/v1/patients/{patient_id}/lab-panels",
        headers=auth,
        json={
            "occurred_at": "2026-06-20T11:00:00Z",
            "panel_name": "Panel inflamatorio",
            "results": [
                {
                    "code": "pcr",
                    "name": "Proteina C reactiva",
                    "value": "180",
                    "numeric_value": "180",
                    "unit": "mg/L",
                    "flag": "high",
                }
            ],
        },
    )
    assert lab_panel.status_code == 201
    before_audit = audit_events(client, auth, patient_id)

    response = client.post(
        f"/api/v1/patients/{patient_id}/assistant/correlate",
        headers=auth,
        json={"presets": ["fever_infection"], "limit": 10},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["applies_changes"] is False
    assert payload["missing_data"] == ["No hay medicacion activa estructurada para correlacionar."]
    correlation = payload["correlations"][0]
    assert correlation["missing_data"] == []
    assert {item["source_type"] for item in correlation["evidence"]} == {
        "vital_sign",
        "lab_result",
    }
    lab_evidence = next(
        item for item in correlation["evidence"] if item["source_type"] == "lab_result"
    )
    assert "/lab-panels/" in lab_evidence["source_path"]
    after_audit = audit_events(client, auth, patient_id)
    assert after_audit == before_audit


def test_assistant_correlate_reports_limit_and_missing_evidence(
    client: TestClient,
    auth_headers,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient(client, auth, first_name="Correlate", last_name="Limit")
    create_event(
        client,
        auth,
        patient_id,
        summary="Primer evento sin correlacion",
        occurred_at="2026-06-20T10:00:00Z",
    )
    create_event(
        client,
        auth,
        patient_id,
        summary="Segundo evento sin correlacion",
        occurred_at="2026-06-20T11:00:00Z",
    )

    response = client.post(
        f"/api/v1/patients/{patient_id}/assistant/correlate",
        headers=auth,
        json={"presets": ["renal_medications"], "limit": 1},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["has_more"] is True
    assert payload["warnings"] == ["Correlacion limitada a 1 registros por dominio."]
    assert "No hay signos vitales estructurados para correlacionar." in payload["missing_data"]
    assert "No hay medicacion activa estructurada para correlacionar." in payload["missing_data"]
    correlation = payload["correlations"][0]
    assert correlation["preset"] == "renal_medications"
    assert correlation["evidence"] == []
    assert correlation["missing_data"] != []


def test_assistant_correlate_unknown_patient_returns_404(
    client: TestClient,
    auth_headers,
) -> None:
    auth = auth_headers(client)

    response = client.post(
        "/api/v1/patients/11111111-1111-4111-8111-111111111111/assistant/correlate",
        headers=auth,
        json={},
    )

    assert response.status_code == 404
