from fastapi.testclient import TestClient
from patient_ai_helpers import create_entry, create_event, create_patient, create_vitals


def test_context_builder_flags_clinical_course_from_recent_events(
    client: TestClient,
    auth_headers,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient(client, auth, first_name="Curso", last_name="Clinico")
    create_entry(
        client,
        auth,
        patient_id,
        title="Baseline clinico",
        assessment="Control previo.",
    )
    create_event(
        client,
        auth,
        patient_id,
        summary="Dolor abdominal en mejoria.",
        occurred_at="2026-06-20T13:00:00Z",
    )
    create_event(
        client,
        auth,
        patient_id,
        summary="Disnea empeora durante la tarde.",
        occurred_at="2026-06-20T14:00:00Z",
    )
    create_event(
        client,
        auth,
        patient_id,
        summary="Sin empeoramiento respiratorio en reevaluacion.",
        occurred_at="2026-06-20T15:00:00Z",
    )
    create_vitals(
        client,
        auth,
        patient_id,
        measured_at="2026-06-20T12:30:00Z",
        temperature_c="37.0",
        systolic_bp=120,
        heart_rate_bpm=86,
        respiratory_rate_bpm=18,
        oxygen_saturation_pct="96.0",
    )
    create_vitals(
        client,
        auth,
        patient_id,
        measured_at="2026-06-20T14:30:00Z",
        temperature_c="37.2",
        systolic_bp=122,
        heart_rate_bpm=92,
        respiratory_rate_bpm=24,
        oxygen_saturation_pct="92.0",
    )

    response = client.post(
        f"/api/v1/patients/{patient_id}/ai/clinical-intent",
        headers=auth,
        json={"intent_type": "daily_changes"},
    )

    assert response.status_code == 200
    rule_findings = response.json()["change_set"]["rule_findings"]
    assert any("Mejoria clinica sugerida" in finding for finding in rule_findings)
    assert any("Empeoramiento clinico sugerido" in finding for finding in rule_findings)
    assert any("dominio dolor" in finding for finding in rule_findings)
    assert any("dominio respiratorio" in finding for finding in rule_findings)
    assert any("Corroborado por signos vitales" in finding for finding in rule_findings)
    assert any("saturacion O2 bajo de 96 a 92 %" in finding for finding in rule_findings)
    assert not any("Sin empeoramiento respiratorio" in finding for finding in rule_findings)
