from fastapi.testclient import TestClient
from patient_ai_helpers import create_entry, create_event, create_patient, create_vitals

from oneepis_api.services.diagnostic_references import search_diagnostic_references


def test_diagnostic_reference_search_returns_curated_codes() -> None:
    pneumonia = search_diagnostic_references("neumonia")[0]
    diabetes = search_diagnostic_references("diabetes")[0]
    hypertension = search_diagnostic_references("hipertension")[0]

    assert {code.system for code in pneumonia.coding_references} == {
        "SNOMED-GPS",
        "CIE-10",
        "CIE-11",
    }
    assert pneumonia.reference_sources[0].chapter_id == "CL-0038"
    assert any(code.code == "5A11" for code in diabetes.coding_references)
    assert any(code.code == "BA00.Z" for code in hypertension.coding_references)


def test_diagnostic_candidates_are_review_only(
    client: TestClient,
    auth_headers,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient(client, auth, first_name="Dx", last_name="Candidato")
    create_event(client, auth, patient_id, summary="Tos y disnea en evaluacion clinica.")
    create_entry(
        client,
        auth,
        patient_id,
        title="Evolucion respiratoria",
        assessment="Crepitos y sospecha clinica respiratoria en revision.",
    )
    create_vitals(
        client,
        auth,
        patient_id,
        measured_at="2026-06-22T10:00:00Z",
        respiratory_rate_bpm=20,
        oxygen_saturation_pct="96.0",
    )

    response = client.post(
        f"/api/v1/patients/{patient_id}/ai/clinical-intent",
        headers=auth,
        json={"intent_type": "diagnostic_candidates"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["requires_human_confirmation"] is True
    assert payload["proposed_actions"][0]["action_type"] == "review_sources"
    assert all(action["action_type"] != "create_event" for action in payload["proposed_actions"])
    assert "No se crea problema activo" in " ".join(payload["warnings"])
    candidate = payload["diagnostic_candidates"][0]
    assert candidate["title"] == "Neumonia"
    assert candidate["certainty"] == "moderate"
    assert candidate["requires_human_confirmation"] is True
    assert {code["system"] for code in candidate["coding_references"]} == {
        "SNOMED-GPS",
        "CIE-10",
        "CIE-11",
    }
    assert "CL-0038" in candidate["reference_sources"][0]["chapter_id"]

    problems = client.get(f"/api/v1/patients/{patient_id}/problems", headers=auth)
    assert problems.status_code == 200
    assert problems.json() == []


def test_diagnostic_candidates_skip_existing_active_problem(
    client: TestClient,
    auth_headers,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient(client, auth, first_name="Dx", last_name="Existente")
    problem = client.post(
        f"/api/v1/patients/{patient_id}/problems",
        headers=auth,
        json={
            "title": "Diabetes mellitus tipo 2",
            "code_system": "SNOMED-GPS",
            "code": "44054006",
        },
    )
    assert problem.status_code == 201
    create_event(client, auth, patient_id, summary="Glicemia elevada en control.")

    response = client.post(
        f"/api/v1/patients/{patient_id}/ai/clinical-intent",
        headers=auth,
        json={"intent_type": "diagnostic_candidates"},
    )

    assert response.status_code == 200
    assert response.json()["diagnostic_candidates"] == []


def test_invalid_snomed_diagnostic_codes_return_422(
    client: TestClient,
    auth_headers,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient(client, auth, first_name="Dx", last_name="Codigo")

    problem = client.post(
        f"/api/v1/patients/{patient_id}/problems",
        headers=auth,
        json={"title": "Codigo invalido", "code_system": "SNOMED-GPS", "code": "ABC"},
    )
    event = client.post(
        f"/api/v1/patients/{patient_id}/clinical-events",
        headers=auth,
        json={
            "event_type": "diagnosis",
            "occurred_at": "2026-06-22T10:00:00Z",
            "summary": "Diagnostico con codigo invalido",
            "payload": {
                "diagnostic_codes": [
                    {
                        "system": "SNOMED-GPS",
                        "code": "ABC",
                        "label": "Codigo invalido",
                        "source_label": "Fixture sintetico",
                    }
                ]
            },
        },
    )

    assert problem.status_code == 422
    assert event.status_code == 422
