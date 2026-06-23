from fastapi.testclient import TestClient
from patient_ai_helpers import (
    create_event,
    create_lab_panel,
    create_patient,
    create_problem,
    create_vitals,
)


def test_context_builder_explains_problem_evidence_links(
    client: TestClient,
    auth_headers,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient(client, auth, first_name="Contexto", last_name="Explicable")
    problem_id = create_problem(
        client,
        auth,
        patient_id,
        title="Dolor abdominal",
        notes="Controlar evolucion y tolerancia oral.",
    )
    linked_event_id = create_event(
        client,
        auth,
        patient_id,
        summary="Dolor abdominal en disminucion.",
    )
    unlinked_event_id = create_event(
        client,
        auth,
        patient_id,
        summary="Control telefonico pendiente.",
    )

    response = client.post(
        f"/api/v1/patients/{patient_id}/ai/clinical-intent",
        headers=auth,
        json={"intent_type": "summarize_patient"},
    )

    assert response.status_code == 200
    contexts = response.json()["problem_contexts"]
    structured = next(context for context in contexts if context["problem_id"] == problem_id)
    assert structured["title"] == "Dolor abdominal"
    assert structured["evidence"][0]["source_id"] == linked_event_id
    assert any("coincidencia textual" in item for item in structured["explanations"])
    assert any("nota de plan estructurada" in item for item in structured["explanations"])

    unlinked = next(context for context in contexts if context["status"] == "unlinked")
    assert unlinked["evidence"][0]["source_id"] == unlinked_event_id
    assert any("no coincidieron con reglas locales" in item for item in unlinked["explanations"])


def test_context_builder_links_problem_by_local_clinical_vocabulary(
    client: TestClient,
    auth_headers,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient(client, auth, first_name="Contexto", last_name="Vocabulario")
    problem_id = create_problem(
        client,
        auth,
        patient_id,
        title="Neumonia adquirida en comunidad",
    )
    event_id = create_event(
        client,
        auth,
        patient_id,
        summary="Disnea en disminucion con menor requerimiento de oxigeno.",
    )

    response = client.post(
        f"/api/v1/patients/{patient_id}/ai/clinical-intent",
        headers=auth,
        json={"intent_type": "summarize_patient"},
    )

    assert response.status_code == 200
    contexts = response.json()["problem_contexts"]
    structured = next(context for context in contexts if context["problem_id"] == problem_id)
    assert structured["evidence"][0]["source_id"] == event_id
    assert structured["evidence"][0]["detail"] == (
        "Evento asociado por vocabulario clinico local: respiratorio."
    )
    assert any("vocabulario clinico local" in item for item in structured["explanations"])
    assert not any(context["status"] == "unlinked" for context in contexts)


def test_context_builder_avoids_negated_local_vocabulary_false_positive(
    client: TestClient,
    auth_headers,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient(client, auth, first_name="Contexto", last_name="Negacion")
    problem_id = create_problem(
        client,
        auth,
        patient_id,
        title="Dolor lumbar",
    )
    event_id = create_event(
        client,
        auth,
        patient_id,
        summary="Niega dolor toracico en control.",
    )

    response = client.post(
        f"/api/v1/patients/{patient_id}/ai/clinical-intent",
        headers=auth,
        json={"intent_type": "summarize_patient"},
    )

    assert response.status_code == 200
    contexts = response.json()["problem_contexts"]
    structured = next(context for context in contexts if context["problem_id"] == problem_id)
    assert structured["evidence"] == []
    unlinked = next(context for context in contexts if context["status"] == "unlinked")
    assert unlinked["evidence"][0]["source_id"] == event_id


def test_context_builder_links_problem_by_snomed_repository_payload(
    client: TestClient,
    auth_headers,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient(client, auth, first_name="Contexto", last_name="Snomed")
    problem_id = create_problem(
        client,
        auth,
        patient_id,
        title="Neumonia adquirida en comunidad",
        code_system="SNOMED-CT",
        code="233604007",
    )
    event_id = create_event(
        client,
        auth,
        patient_id,
        summary="Disnea en disminucion.",
        payload={
            "snomed_concepts": [
                {
                    "concept_id": "267036007",
                    "term": "Dyspnea",
                    "ancestor_ids": ["233604007"],
                    "repository": "external-rf2-or-terminology-server",
                }
            ]
        },
    )

    response = client.post(
        f"/api/v1/patients/{patient_id}/ai/clinical-intent",
        headers=auth,
        json={"intent_type": "summarize_patient"},
    )

    assert response.status_code == 200
    contexts = response.json()["problem_contexts"]
    structured = next(context for context in contexts if context["problem_id"] == problem_id)
    assert structured["evidence"][0]["source_id"] == event_id
    assert structured["evidence"][0]["detail"] == (
        "Evento asociado por ancestro SNOMED CT desde repositorio terminologico."
    )
    assert not any(context["status"] == "unlinked" for context in contexts)


def test_context_builder_adds_domain_specific_problem_pending_data(
    client: TestClient,
    auth_headers,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient(client, auth, first_name="Contexto", last_name="Pendientes")
    respiratory_problem_id = create_problem(
        client,
        auth,
        patient_id,
        title="Neumonia adquirida en comunidad",
        notes="Controlar sintomas respiratorios.",
    )
    metabolic_problem_id = create_problem(
        client,
        auth,
        patient_id,
        title="Diabetes mellitus tipo 2",
        notes="Control metabolico pendiente.",
    )
    create_vitals(
        client,
        auth,
        patient_id,
        measured_at="2026-06-20T13:00:00Z",
        temperature_c="36.8",
        systolic_bp=128,
        heart_rate_bpm=82,
    )

    response = client.post(
        f"/api/v1/patients/{patient_id}/ai/clinical-intent",
        headers=auth,
        json={"intent_type": "summarize_patient"},
    )

    assert response.status_code == 200
    contexts = response.json()["problem_contexts"]
    respiratory_context = next(
        context for context in contexts if context["problem_id"] == respiratory_problem_id
    )
    metabolic_context = next(
        context for context in contexts if context["problem_id"] == metabolic_problem_id
    )
    assert any("saturacion O2 reciente" in item for item in respiratory_context["pending"])
    assert any(
        "frecuencia respiratoria reciente" in item for item in respiratory_context["pending"]
    )
    assert any("Dominio clinico probable" in item for item in respiratory_context["explanations"])
    assert any("glicemia" in item for item in metabolic_context["pending"])


def test_context_builder_handles_renal_domain_context(
    client: TestClient,
    auth_headers,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient(client, auth, first_name="Contexto", last_name="Renal")
    problem_id = create_problem(
        client,
        auth,
        patient_id,
        title="Enfermedad renal cronica",
        notes="Vigilar funcion renal.",
    )

    response = client.post(
        f"/api/v1/patients/{patient_id}/ai/clinical-intent",
        headers=auth,
        json={"intent_type": "summarize_patient"},
    )

    assert response.status_code == 200
    context = next(
        item for item in response.json()["problem_contexts"] if item["problem_id"] == problem_id
    )
    assert any("creatinina/eGFR o diuresis" in item for item in context["pending"])
    assert any("Dominio clinico probable" in item for item in context["explanations"])

    event_id = create_event(
        client,
        auth,
        patient_id,
        summary="Creatinina en control, funcion renal estable.",
    )
    linked_response = client.post(
        f"/api/v1/patients/{patient_id}/ai/clinical-intent",
        headers=auth,
        json={"intent_type": "summarize_patient"},
    )

    assert linked_response.status_code == 200
    linked_context = next(
        item
        for item in linked_response.json()["problem_contexts"]
        if item["problem_id"] == problem_id
    )
    assert linked_context["evidence"][0]["source_id"] == event_id
    assert linked_context["evidence"][0]["detail"] == (
        "Evento asociado por vocabulario clinico local: renal."
    )
    assert not any("creatinina/eGFR o diuresis" in item for item in linked_context["pending"])


def test_context_builder_uses_structured_lab_results_as_problem_evidence(
    client: TestClient,
    auth_headers,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient(client, auth, first_name="Contexto", last_name="Lab")
    problem_id = create_problem(
        client,
        auth,
        patient_id,
        title="Enfermedad renal cronica",
        notes="Vigilar funcion renal.",
    )
    panel = create_lab_panel(client, auth, patient_id)
    result_id = panel["results"][0]["id"]

    response = client.post(
        f"/api/v1/patients/{patient_id}/ai/clinical-intent",
        headers=auth,
        json={"intent_type": "summarize_patient"},
    )

    assert response.status_code == 200
    payload = response.json()
    context = next(
        item for item in payload["problem_contexts"] if item["problem_id"] == problem_id
    )
    assert context["evidence"][0]["source_id"] == result_id
    assert context["evidence"][0]["detail"] == (
        "Resultado estructurado asociado por dominio clinico local: renal."
    )
    assert not any("creatinina/eGFR o diuresis" in item for item in context["pending"])
    assert any(source["source_type"] == "lab_result" for source in payload["sources"])
    assert any(
        section["title"] == "Examenes estructurados" and section["items"]
        for section in payload["context_sections"]
    )


def test_context_builder_missing_data_depends_on_care_context(
    client: TestClient,
    auth_headers,
) -> None:
    auth = auth_headers(client)
    ambulatory_patient_id = create_patient(
        client,
        auth,
        first_name="Contexto",
        last_name="Ambulatorio",
        current_care_context="ambulatory",
    )
    hospitalized_patient_id = create_patient(
        client,
        auth,
        first_name="Contexto",
        last_name="Hospitalizado",
        current_care_context="hospitalized",
    )

    ambulatory_response = client.post(
        f"/api/v1/patients/{ambulatory_patient_id}/ai/clinical-intent",
        headers=auth,
        json={"intent_type": "summarize_patient"},
    )
    hospitalized_response = client.post(
        f"/api/v1/patients/{hospitalized_patient_id}/ai/clinical-intent",
        headers=auth,
        json={"intent_type": "summarize_patient"},
    )

    assert ambulatory_response.status_code == 200
    assert hospitalized_response.status_code == 200
    ambulatory_missing = ambulatory_response.json()["missing_data"]
    hospitalized_missing = hospitalized_response.json()["missing_data"]
    assert any("Evolucion ambulatoria reciente" in item for item in ambulatory_missing)
    assert any("contexto objetivo" in item for item in ambulatory_missing)
    assert any("Evolucion u hoja diaria reciente" in item for item in hospitalized_missing)
    assert any("contexto hospitalizado" in item for item in hospitalized_missing)
