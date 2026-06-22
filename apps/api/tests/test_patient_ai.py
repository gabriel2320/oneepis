from fastapi.testclient import TestClient


def _create_patient(
    client: TestClient,
    auth: dict[str, str],
    *,
    first_name: str = "Paciente",
    last_name: str = "IA",
    current_care_context: str = "unknown",
) -> str:
    response = client.post(
        "/api/v1/patients",
        headers=auth,
        json={
            "first_name": first_name,
            "last_name": last_name,
            "birth_date": "1988-01-01",
            "sex_at_birth": "unknown",
            "current_care_context": current_care_context,
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def _create_entry(
    client: TestClient,
    auth: dict[str, str],
    patient_id: str,
    *,
    title: str,
    subjective: str | None = None,
    objective: str | None = None,
    assessment: str | None = None,
    plan: str | None = None,
) -> str:
    response = client.post(
        f"/api/v1/patients/{patient_id}/clinical-entries",
        headers=auth,
        json={
            "kind": "progress",
            "status": "draft",
            "occurred_at": "2026-06-20T12:00:00Z",
            "title": title,
            "subjective": subjective,
            "objective": objective,
            "assessment": assessment,
            "plan": plan,
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def _create_problem(
    client: TestClient,
    auth: dict[str, str],
    patient_id: str,
    *,
    title: str,
    notes: str | None = None,
) -> str:
    response = client.post(
        f"/api/v1/patients/{patient_id}/problems",
        headers=auth,
        json={
            "title": title,
            "onset_date": "2026-06-01",
            "notes": notes,
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def _create_event(
    client: TestClient,
    auth: dict[str, str],
    patient_id: str,
    *,
    summary: str,
) -> str:
    response = client.post(
        f"/api/v1/patients/{patient_id}/clinical-events",
        headers=auth,
        json={
            "event_type": "clinical_note",
            "occurred_at": "2026-06-20T12:00:00Z",
            "summary": summary,
            "source_type": "manual",
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def _audit_events(client: TestClient, auth: dict[str, str], patient_id: str) -> list[dict]:
    response = client.get(
        f"/api/v1/patients/{patient_id}/audit-events",
        headers=auth,
    )
    assert response.status_code == 200
    return response.json()


def _first_event_proposal_from_entry(
    client: TestClient,
    auth: dict[str, str],
    patient_id: str,
    entry_id: str,
) -> dict:
    response = client.post(
        f"/api/v1/patients/{patient_id}/ai/event-proposals-from-entry",
        headers=auth,
        json={"entry_id": entry_id},
    )
    assert response.status_code == 200
    return response.json()["proposals"][0]


def test_patient_ai_suggestions_use_snapshot_without_persisting(
    client: TestClient,
    auth_headers,
) -> None:
    auth = auth_headers(client)
    patient_id = _create_patient(client, auth, first_name="C", last_name="Paciente")

    response = client.post(
        f"/api/v1/patients/{patient_id}/ai/suggestions",
        headers=auth,
        json={"focus": "documentation"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["provider"] == "local_rules"
    assert payload["status"] == "draft"
    assert payload["patient_id"] == patient_id
    assert payload["suggestions"][0]["title"] == "Faltan signos vitales recientes"


def test_patient_ai_suggestions_return_404_for_missing_patient(
    client: TestClient,
    auth_headers,
) -> None:
    auth = auth_headers(client)
    response = client.post(
        "/api/v1/patients/11111111-1111-4111-8111-111111111111/ai/suggestions",
        headers=auth,
        json={"focus": "summary"},
    )

    assert response.status_code == 404


def test_context_builder_explains_problem_evidence_links(
    client: TestClient,
    auth_headers,
) -> None:
    auth = auth_headers(client)
    patient_id = _create_patient(client, auth, first_name="Contexto", last_name="Explicable")
    problem_id = _create_problem(
        client,
        auth,
        patient_id,
        title="Dolor abdominal",
        notes="Controlar evolucion y tolerancia oral.",
    )
    linked_event_id = _create_event(
        client,
        auth,
        patient_id,
        summary="Dolor abdominal en disminucion.",
    )
    unlinked_event_id = _create_event(
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
    assert any("no coincidieron textualmente" in item for item in unlinked["explanations"])


def test_context_builder_missing_data_depends_on_care_context(
    client: TestClient,
    auth_headers,
) -> None:
    auth = auth_headers(client)
    ambulatory_patient_id = _create_patient(
        client,
        auth,
        first_name="Contexto",
        last_name="Ambulatorio",
        current_care_context="ambulatory",
    )
    hospitalized_patient_id = _create_patient(
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


def test_event_proposals_from_entry_are_reviewable_and_do_not_persist(
    client: TestClient,
    auth_headers,
) -> None:
    auth = auth_headers(client)
    patient_id = _create_patient(client, auth, first_name="Propuesta", last_name="Evento")
    entry_id = _create_entry(
        client,
        auth,
        patient_id,
        title="Evolucion con plan",
        assessment="Dolor controlado y sin fiebre.",
        plan="Mantener hidratacion. Controlar signos vitales.",
    )

    response = client.post(
        f"/api/v1/patients/{patient_id}/ai/event-proposals-from-entry",
        headers=auth,
        json={"entry_id": entry_id},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["applies_changes"] is False
    assert payload["requires_human_confirmation"] is True
    assert [proposal["summary"] for proposal in payload["proposals"]] == [
        "Dolor controlado y sin fiebre",
        "Mantener hidratacion",
        "Controlar signos vitales",
    ]
    assert payload["proposals"][1]["event_type"] == "care_plan"
    assert payload["proposals"][1]["source_type"] == "clinical_entry"
    assert payload["proposals"][1]["patch"]["target"] == "clinical_event"
    assert payload["proposals"][1]["patch"]["requires_human_confirmation"] is True
    assert {
        operation["path"] for operation in payload["proposals"][1]["patch"]["operations"]
    } >= {"/event_type", "/occurred_at", "/summary", "/source_type", "/source_ref", "/payload"}
    events_response = client.get(
        f"/api/v1/patients/{patient_id}/clinical-events",
        headers=auth,
    )
    assert events_response.status_code == 200
    assert events_response.json() == []

    audit_events = _audit_events(client, auth, patient_id)
    assert any(
        event["action"] == "ai.entry_event_proposals.created"
        and event["extra_data"]["proposal_count"] == 3
        for event in audit_events
    )


def test_accepting_entry_event_proposal_creates_sourced_event(
    client: TestClient,
    auth_headers,
) -> None:
    auth = auth_headers(client)
    patient_id = _create_patient(client, auth, first_name="Evento", last_name="Aceptado")
    entry_id = _create_entry(
        client,
        auth,
        patient_id,
        title="Evolucion con evento",
        plan="Control telefonico en 48 horas.",
    )
    proposal = _first_event_proposal_from_entry(client, auth, patient_id, entry_id)

    create_response = client.post(
        f"/api/v1/patients/{patient_id}/ai/confirm-clinical-patch",
        headers=auth,
        json={
            "decision": "accepted",
            "patch": proposal["patch"],
        },
    )

    assert create_response.status_code == 200
    payload = create_response.json()
    assert payload["applies_changes"] is True
    event = payload["clinical_event"]
    assert event["summary"] == "Control telefonico en 48 horas"
    assert event["source_type"] == "clinical_entry"
    assert event["source_ref"] == entry_id
    assert event["payload"]["human_reviewed"] is True
    assert event["payload"]["confirmed_from_patch"] is True
    assert event["payload"]["clinical_patch_id"] == proposal["patch"]["patch_id"]
    audit_events = _audit_events(client, auth, patient_id)
    assert any(
        audit["action"] == "ai.clinical_patch.accepted"
        and audit["extra_data"]["patch_id"] == proposal["patch"]["patch_id"]
        and audit["extra_data"]["applies_changes"] is True
        for audit in audit_events
    )


def test_rejecting_entry_event_patch_audits_without_creating_event(
    client: TestClient,
    auth_headers,
) -> None:
    auth = auth_headers(client)
    patient_id = _create_patient(client, auth, first_name="Evento", last_name="Rechazado")
    entry_id = _create_entry(
        client,
        auth,
        patient_id,
        title="Evolucion sin evento final",
        plan="Control telefonico en 48 horas.",
    )
    proposal = _first_event_proposal_from_entry(client, auth, patient_id, entry_id)

    reject_response = client.post(
        f"/api/v1/patients/{patient_id}/ai/confirm-clinical-patch",
        headers=auth,
        json={
            "decision": "rejected",
            "patch": proposal["patch"],
            "note": "No corresponde a evento longitudinal.",
        },
    )

    assert reject_response.status_code == 200
    payload = reject_response.json()
    assert payload["applies_changes"] is False
    assert payload["clinical_event"] is None
    events_response = client.get(
        f"/api/v1/patients/{patient_id}/clinical-events",
        headers=auth,
    )
    assert events_response.status_code == 200
    assert events_response.json() == []
    audit_events = _audit_events(client, auth, patient_id)
    assert any(
        audit["action"] == "ai.clinical_patch.rejected"
        and audit["extra_data"]["patch_id"] == proposal["patch"]["patch_id"]
        and audit["extra_data"]["applies_changes"] is False
        for audit in audit_events
    )


def test_accepting_evolution_patch_creates_reviewed_draft_entry(
    client: TestClient,
    auth_headers,
) -> None:
    auth = auth_headers(client)
    patient_id = _create_patient(client, auth, first_name="Soap", last_name="Patch")

    response = client.post(
        f"/api/v1/patients/{patient_id}/ai/confirm-clinical-patch",
        headers=auth,
        json={
            "decision": "accepted",
            "patch": {
                "patch_id": "soap-draft-test",
                "target": "evolution",
                "mode": "draft",
                "operations": [
                    {
                        "op": "add",
                        "path": "/kind",
                        "value": "progress",
                        "reason": "Borrador SOAP generado desde AI-Chart.",
                    },
                    {
                        "op": "add",
                        "path": "/status",
                        "value": "draft",
                        "reason": "Las propuestas IA se guardan como borrador no firmado.",
                    },
                    {
                        "op": "add",
                        "path": "/occurred_at",
                        "value": "2026-06-20T12:00:00Z",
                        "reason": "Fecha de confirmacion humana.",
                    },
                    {
                        "op": "add",
                        "path": "/title",
                        "value": "Evolucion SOAP desde patch",
                        "reason": "Titulo editado por humano.",
                    },
                    {
                        "op": "add",
                        "path": "/subjective",
                        "value": "Paciente refiere estabilidad.",
                        "reason": "Seccion S revisada.",
                    },
                    {
                        "op": "add",
                        "path": "/objective",
                        "value": "Sin hallazgos objetivos nuevos.",
                        "reason": "Seccion O revisada.",
                    },
                    {
                        "op": "add",
                        "path": "/assessment",
                        "value": "Seguimiento clinico.",
                        "reason": "Seccion A revisada.",
                    },
                    {
                        "op": "add",
                        "path": "/plan",
                        "value": "Mantener control.",
                        "reason": "Seccion P revisada.",
                    },
                    {
                        "op": "add",
                        "path": "/tags",
                        "value": ["soap", "ai-chart"],
                        "reason": "Trazabilidad del origen.",
                    },
                    {
                        "op": "add",
                        "path": "/extra_data",
                        "value": {"requires_human_confirmation": True},
                        "reason": "Metadata de revision.",
                    },
                ],
                "sources": [],
                "warnings": [],
                "requires_human_confirmation": True,
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["applies_changes"] is True
    entry = payload["clinical_entry"]
    assert entry["title"] == "Evolucion SOAP desde patch"
    assert entry["status"] == "draft"
    assert entry["subjective"] == "Paciente refiere estabilidad."
    assert entry["extra_data"]["clinical_patch_id"] == "soap-draft-test"
    assert entry["extra_data"]["confirmed_from_patch"] is True
    assert entry["extra_data"]["human_reviewed"] is True
    audit_events = _audit_events(client, auth, patient_id)
    assert any(
        audit["action"] == "ai.clinical_patch.accepted"
        and audit["entity_type"] == "clinical_entry"
        and audit["extra_data"]["target"] == "evolution"
        for audit in audit_events
    )


def test_accepting_unsupported_patch_target_does_not_write_or_audit_acceptance(
    client: TestClient,
    auth_headers,
) -> None:
    auth = auth_headers(client)
    patient_id = _create_patient(client, auth, first_name="Patch", last_name="Unsupported")

    response = client.post(
        f"/api/v1/patients/{patient_id}/ai/confirm-clinical-patch",
        headers=auth,
        json={
            "decision": "accepted",
            "patch": {
                "patch_id": "unsupported-medication-patch",
                "target": "medication",
                "mode": "suggestion",
                "operations": [
                    {
                        "op": "add",
                        "path": "/name",
                        "value": "Medicamento no aplicado",
                        "reason": "Target no soportado en ClinicalPatch v0.",
                    }
                ],
                "sources": [],
                "warnings": [],
                "requires_human_confirmation": True,
            },
        },
    )

    assert response.status_code == 422
    events_response = client.get(
        f"/api/v1/patients/{patient_id}/clinical-events",
        headers=auth,
    )
    assert events_response.status_code == 200
    assert events_response.json() == []
    audit_events = _audit_events(client, auth, patient_id)
    assert not any(
        audit["action"] == "ai.clinical_patch.accepted"
        and audit["extra_data"].get("patch_id") == "unsupported-medication-patch"
        for audit in audit_events
    )
    assert any(
        audit["action"] == "ai.clinical_patch.unsupported"
        and audit["extra_data"].get("patch_id") == "unsupported-medication-patch"
        and audit["extra_data"]["target"] == "medication"
        and audit["extra_data"]["applies_changes"] is False
        for audit in audit_events
    )
