from fastapi.testclient import TestClient
from patient_ai_helpers import (
    audit_events,
    create_entry,
    create_patient,
    first_event_proposal_from_entry,
)


def test_accepting_entry_event_proposal_creates_sourced_event(
    client: TestClient,
    auth_headers,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient(client, auth, first_name="Evento", last_name="Aceptado")
    entry_id = create_entry(
        client,
        auth,
        patient_id,
        title="Evolucion con evento",
        plan="Control telefonico en 48 horas.",
    )
    proposal = first_event_proposal_from_entry(client, auth, patient_id, entry_id)

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
    patient_audit_events = audit_events(client, auth, patient_id)
    assert any(
        audit["action"] == "ai.clinical_patch.accepted"
        and audit["extra_data"]["patch_id"] == proposal["patch"]["patch_id"]
        and audit["extra_data"]["applies_changes"] is True
        for audit in patient_audit_events
    )


def test_rejecting_entry_event_patch_audits_without_creating_event(
    client: TestClient,
    auth_headers,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient(client, auth, first_name="Evento", last_name="Rechazado")
    entry_id = create_entry(
        client,
        auth,
        patient_id,
        title="Evolucion sin evento final",
        plan="Control telefonico en 48 horas.",
    )
    proposal = first_event_proposal_from_entry(client, auth, patient_id, entry_id)

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
    patient_audit_events = audit_events(client, auth, patient_id)
    assert any(
        audit["action"] == "ai.clinical_patch.rejected"
        and audit["extra_data"]["patch_id"] == proposal["patch"]["patch_id"]
        and audit["extra_data"]["applies_changes"] is False
        for audit in patient_audit_events
    )


def test_accepting_patch_without_human_confirmation_is_blocked(
    client: TestClient,
    auth_headers,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient(client, auth, first_name="Patch", last_name="SinConfirmacion")
    entry_id = create_entry(
        client,
        auth,
        patient_id,
        title="Evolucion con evento inseguro",
        plan="Control telefonico en 48 horas.",
    )
    proposal = first_event_proposal_from_entry(client, auth, patient_id, entry_id)
    proposal["patch"]["requires_human_confirmation"] = False

    response = client.post(
        f"/api/v1/patients/{patient_id}/ai/confirm-clinical-patch",
        headers=auth,
        json={
            "decision": "accepted",
            "patch": proposal["patch"],
        },
    )

    assert response.status_code == 422
    events_response = client.get(
        f"/api/v1/patients/{patient_id}/clinical-events",
        headers=auth,
    )
    assert events_response.status_code == 200
    assert events_response.json() == []
    patient_audit_events = audit_events(client, auth, patient_id)
    assert any(
        audit["action"] == "ai.clinical_patch.blocked"
        and audit["extra_data"]["patch_id"] == proposal["patch"]["patch_id"]
        and audit["extra_data"]["requires_human_confirmation"] is False
        and audit["extra_data"]["applies_changes"] is False
        for audit in patient_audit_events
    )


def test_accepting_evolution_patch_creates_reviewed_draft_entry(
    client: TestClient,
    auth_headers,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient(client, auth, first_name="Soap", last_name="Patch")

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
    patient_audit_events = audit_events(client, auth, patient_id)
    assert any(
        audit["action"] == "ai.clinical_patch.accepted"
        and audit["entity_type"] == "clinical_entry"
        and audit["extra_data"]["target"] == "evolution"
        for audit in patient_audit_events
    )


def test_accepting_evolution_patch_must_remain_draft(
    client: TestClient,
    auth_headers,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient(client, auth, first_name="Soap", last_name="Firmado")

    response = client.post(
        f"/api/v1/patients/{patient_id}/ai/confirm-clinical-patch",
        headers=auth,
        json={
            "decision": "accepted",
            "patch": {
                "patch_id": "soap-signed-test",
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
                        "value": "signed",
                        "reason": "Estado no permitido desde AI-Chart.",
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
                        "value": "Evolucion SOAP firmada por patch",
                        "reason": "Titulo editado por humano.",
                    },
                ],
                "sources": [],
                "warnings": [],
                "requires_human_confirmation": True,
            },
        },
    )

    assert response.status_code == 422
    entries_response = client.get(
        f"/api/v1/patients/{patient_id}/clinical-entries",
        headers=auth,
    )
    assert entries_response.status_code == 200
    assert entries_response.json() == []
    patient_audit_events = audit_events(client, auth, patient_id)
    assert any(
        audit["action"] == "ai.clinical_patch.blocked"
        and audit["extra_data"]["patch_id"] == "soap-signed-test"
        and audit["extra_data"]["target"] == "evolution"
        and audit["extra_data"]["applies_changes"] is False
        for audit in patient_audit_events
    )


def test_accepting_unsupported_patch_target_does_not_write_or_audit_acceptance(
    client: TestClient,
    auth_headers,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient(client, auth, first_name="Patch", last_name="Unsupported")

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
    patient_audit_events = audit_events(client, auth, patient_id)
    assert not any(
        audit["action"] == "ai.clinical_patch.accepted"
        and audit["extra_data"].get("patch_id") == "unsupported-medication-patch"
        for audit in patient_audit_events
    )
    assert any(
        audit["action"] == "ai.clinical_patch.unsupported"
        and audit["extra_data"].get("patch_id") == "unsupported-medication-patch"
        and audit["extra_data"]["target"] == "medication"
        and audit["extra_data"]["applies_changes"] is False
        for audit in patient_audit_events
    )
