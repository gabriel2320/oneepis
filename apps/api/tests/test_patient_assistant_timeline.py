from datetime import UTC, date, datetime

from fastapi.testclient import TestClient
from patient_ai_helpers import (
    audit_events,
    create_entry,
    create_event,
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
    }.issubset(set(item_types))
    occurred_values = [item["occurred_at"] for item in payload["items"]]
    assert occurred_values == sorted(occurred_values, reverse=True)
    vital_item = next(item for item in payload["items"] if item["item_type"] == "vital_sign")
    assert vital_item["source_path"].endswith("/vital-signs/" + vital_item["item_id"])
    event_item = next(item for item in payload["items"] if item["item_type"] == "clinical_event")
    assert event_item["summary"] == "Evento longitudinal relevante"
    assert event_item["source_path"].endswith("/clinical-events")
    after_audit = audit_events(client, auth, patient_id)
    assert after_audit == before_audit


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
    }.issubset(set(item_types))
    occurred_values = [item["occurred_at"] for item in payload["results"]]
    assert occurred_values == sorted(occurred_values, reverse=True)
    entry_item = next(item for item in payload["results"] if item["item_type"] == "clinical_entry")
    assert entry_item["matched_fields"] == ["assessment"]
    assert "Diabetes mellitus" in entry_item["snippet"]
    assert entry_item["source_path"].endswith("/clinical-entries/" + entry_item["item_id"])
    problem_item = next(item for item in payload["results"] if item["item_type"] == "problem")
    assert problem_item["source_path"].endswith("/problems/" + problem_item["item_id"])
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
