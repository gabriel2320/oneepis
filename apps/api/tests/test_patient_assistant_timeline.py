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
