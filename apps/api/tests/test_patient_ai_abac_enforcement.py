from __future__ import annotations

import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

import pytest
from access_boundary_helpers import (
    assign_actor_to_care_team,
    assign_patient_to_care_team,
    create_care_team,
)
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from oneepis_api.core.config import Settings, get_settings
from oneepis_api.db.session import get_session
from oneepis_api.main import app
from oneepis_api.models.patient import Patient

PATIENT_AI_DENIED_CASES: tuple[tuple[str, dict[str, Any], str], ...] = (
    (
        "/ai/draft-soap-from-events",
        {"clinical_event_ids": ["11111111-1111-4111-8111-111111111111"]},
        "ai.soap_draft.created",
    ),
    (
        "/ai/event-proposals-from-entry",
        {"entry_id": "22222222-2222-4222-8222-222222222222"},
        "ai.entry_event_proposals.created",
    ),
    (
        "/ai/confirm-clinical-patch",
        {
            "decision": "rejected",
            "patch": {
                "patch_id": "abac-denied-patch",
                "target": "clinical_event",
                "mode": "suggestion",
                "operations": [
                    {
                        "op": "add",
                        "path": "/summary",
                        "value": "No se aplica",
                        "reason": "Prueba ABAC sin relacion activa.",
                    }
                ],
                "sources": [],
                "warnings": [],
                "requires_human_confirmation": True,
            },
        },
        "ai.clinical_patch.rejected",
    ),
    (
        "/ai/clinical-intent",
        {"intent_type": "summarize_patient", "mode": "read"},
        "ai.clinical_intent.created",
    ),
    (
        "/ai/clinical-intent-route",
        {"text": "resumir paciente"},
        "ai.clinical_intent.routed",
    ),
    (
        "/ai/action-decision",
        {
            "decision": "reviewed",
            "action_type": "none",
            "label": "Sin accion",
            "requires_confirmation": False,
        },
        "ai.clinical_action.decided",
    ),
    (
        "/ai/review-item-decision",
        {
            "decision": "rejected",
            "item_type": "missing_medication_dose",
            "label": "Dosis pendiente",
            "detail": "Falta dosis estructurada.",
            "source_type": "medication",
        },
        "ai.review_item.decided",
    ),
)


@pytest.mark.parametrize(("path_suffix", "payload", "route_action"), PATIENT_AI_DENIED_CASES)
def test_patient_ai_abac_enforcement_denies_without_active_relationship(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
    audit_events_for_patient,
    path_suffix: str,
    payload: dict[str, Any],
    route_action: str,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient_for_permissions(client, auth)
    _enable_development_abac_enforcement()

    response = client.post(
        f"/api/v1/patients/{patient_id}{path_suffix}",
        headers=auth,
        json=payload,
    )

    assert response.status_code == 403
    actions = [event["action"] for event in audit_events_for_patient(patient_id)]
    assert actions.count("access_context.denied") == 1
    assert route_action not in actions


def test_patient_ai_abac_enforcement_allows_active_relationship(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
    audit_events_for_patient,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient_for_permissions(client, auth)
    _assign_patient_scope(
        patient_id=patient_id,
        actor_id="medico@oneepis.local",
    )
    _enable_development_abac_enforcement()

    response = client.post(
        f"/api/v1/patients/{patient_id}/ai/clinical-intent",
        headers=auth,
        json={"intent_type": "summarize_patient", "mode": "read"},
    )

    assert response.status_code == 200
    assert response.json()["intent_type"] == "summarize_patient"
    actions = [event["action"] for event in audit_events_for_patient(patient_id)]
    assert "ai.clinical_intent.created" in actions
    assert "access_context.denied" not in actions


def _enable_development_abac_enforcement() -> None:
    app.dependency_overrides[get_settings] = lambda: Settings(
        ai_provider="local_rules",
        abac_enforcement_enabled=True,
    )


def _assign_patient_scope(*, patient_id: str, actor_id: str) -> None:
    with _test_session() as session:
        patient = session.get(Patient, uuid.UUID(patient_id))
        assert patient is not None
        care_team = create_care_team(session)
        assign_actor_to_care_team(
            session,
            actor_id=actor_id,
            care_team=care_team,
        )
        assign_patient_to_care_team(
            session,
            patient=patient,
            care_team=care_team,
        )


@contextmanager
def _test_session() -> Iterator[Session]:
    session_provider = app.dependency_overrides[get_session]
    session_iterator = session_provider()
    session = next(session_iterator)
    try:
        yield session
    finally:
        session_iterator.close()
