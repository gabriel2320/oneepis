from __future__ import annotations

import uuid
from collections.abc import Iterator
from contextlib import contextmanager

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


def test_assistant_timeline_abac_denies_without_active_relationship(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
    audit_events_for_patient,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient_for_permissions(client, auth)
    _enable_development_abac_enforcement()

    response = client.get(
        f"/api/v1/patients/{patient_id}/assistant/timeline",
        headers=auth,
    )

    assert response.status_code == 403
    actions = [event["action"] for event in audit_events_for_patient(patient_id)]
    assert actions.count("access_context.denied") == 1
    assert "assistant_timeline.read" not in actions
    assert "access_context.passive_decision" not in actions


def test_assistant_timeline_abac_allows_active_relationship(
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

    response = client.get(
        f"/api/v1/patients/{patient_id}/assistant/timeline",
        headers=auth,
    )

    assert response.status_code == 200
    assert response.json()["patient_id"] == patient_id
    actions = [event["action"] for event in audit_events_for_patient(patient_id)]
    assert "assistant_timeline.read" in actions
    assert "access_context.passive_decision" in actions


def test_assistant_search_abac_denies_without_active_relationship(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
    audit_events_for_patient,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient_for_permissions(client, auth)
    _enable_development_abac_enforcement()

    response = client.get(
        f"/api/v1/patients/{patient_id}/assistant/search?q=ficha",
        headers=auth,
    )

    assert response.status_code == 403
    actions = [event["action"] for event in audit_events_for_patient(patient_id)]
    assert actions.count("access_context.denied") == 1
    assert "assistant_search.read" not in actions
    assert "access_context.passive_decision" not in actions


def test_assistant_search_abac_allows_active_relationship(
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

    response = client.get(
        f"/api/v1/patients/{patient_id}/assistant/search?q=ficha",
        headers=auth,
    )

    assert response.status_code == 200
    assert response.json()["patient_id"] == patient_id
    actions = [event["action"] for event in audit_events_for_patient(patient_id)]
    assert "assistant_search.read" in actions
    assert "access_context.passive_decision" in actions


def test_assistant_chart_abac_denies_without_active_relationship(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
    audit_events_for_patient,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient_for_permissions(client, auth)
    _enable_development_abac_enforcement()

    response = client.post(
        f"/api/v1/patients/{patient_id}/assistant/chart",
        headers=auth,
        json={"series": ["heart_rate"], "limit": 10},
    )

    assert response.status_code == 403
    actions = [event["action"] for event in audit_events_for_patient(patient_id)]
    assert actions.count("access_context.denied") == 1
    assert "assistant_chart.read" not in actions
    assert "access_context.passive_decision" not in actions


def test_assistant_chart_abac_allows_active_relationship(
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
        f"/api/v1/patients/{patient_id}/assistant/chart",
        headers=auth,
        json={"series": ["heart_rate"], "limit": 10},
    )

    assert response.status_code == 200
    assert response.json()["patient_id"] == patient_id
    actions = [event["action"] for event in audit_events_for_patient(patient_id)]
    assert "assistant_chart.read" in actions
    assert "access_context.passive_decision" in actions


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
