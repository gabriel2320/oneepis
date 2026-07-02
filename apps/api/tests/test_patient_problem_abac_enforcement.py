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


def test_patient_problems_abac_enforcement_denies_without_active_relationship(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
    audit_events_for_patient,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient_for_permissions(client, auth)
    problem = _create_problem(client, auth, patient_id)
    _enable_development_abac_enforcement()

    list_response = client.get(f"/api/v1/patients/{patient_id}/problems", headers=auth)
    detail_response = client.get(
        f"/api/v1/patients/{patient_id}/problems/{problem['id']}",
        headers=auth,
    )

    assert list_response.status_code == 403
    assert detail_response.status_code == 403
    actions = [event["action"] for event in audit_events_for_patient(patient_id)]
    assert actions.count("access_context.denied") == 2
    assert "problems.read" not in actions
    assert "problem.read" not in actions


def test_patient_problems_abac_enforcement_allows_active_relationship(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient_for_permissions(client, auth)
    problem = _create_problem(client, auth, patient_id)
    _assign_patient_scope(
        patient_id=patient_id,
        actor_id="medico@oneepis.local",
    )
    _enable_development_abac_enforcement()

    list_response = client.get(f"/api/v1/patients/{patient_id}/problems", headers=auth)
    detail_response = client.get(
        f"/api/v1/patients/{patient_id}/problems/{problem['id']}",
        headers=auth,
    )

    assert list_response.status_code == 200
    assert [item["id"] for item in list_response.json()] == [problem["id"]]
    assert detail_response.status_code == 200
    assert detail_response.json()["id"] == problem["id"]


def test_patient_problems_write_abac_denies_without_active_relationship(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
    audit_events_for_patient,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient_for_permissions(client, auth)
    problem = _create_problem(client, auth, patient_id)
    unknown_problem_id = uuid.uuid4()
    _enable_development_abac_enforcement()

    create_response = client.post(
        f"/api/v1/patients/{patient_id}/problems",
        headers=auth,
        json=_problem_payload(title="Problema sin relacion activa", code="E10"),
    )
    update_response = client.patch(
        f"/api/v1/patients/{patient_id}/problems/{problem['id']}",
        headers=auth,
        json={"code": "E10"},
    )
    missing_update_response = client.patch(
        f"/api/v1/patients/{patient_id}/problems/{unknown_problem_id}",
        headers=auth,
        json={"code": "E10"},
    )
    delete_response = client.delete(
        f"/api/v1/patients/{patient_id}/problems/{problem['id']}",
        headers=auth,
    )

    assert create_response.status_code == 403
    assert update_response.status_code == 403
    assert missing_update_response.status_code == 403
    assert delete_response.status_code == 403
    actions = [event["action"] for event in audit_events_for_patient(patient_id)]
    assert actions.count("access_context.denied") == 4
    assert actions.count("problem.created") == 1
    assert "problem.updated" not in actions
    assert "problem.entered_in_error" not in actions


def test_patient_problems_write_abac_allows_active_relationship(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient_for_permissions(client, auth)
    _assign_patient_scope(
        patient_id=patient_id,
        actor_id="medico@oneepis.local",
    )
    _enable_development_abac_enforcement()

    create_response = client.post(
        f"/api/v1/patients/{patient_id}/problems",
        headers=auth,
        json=_problem_payload(title="Problema permitido por relacion activa", code="E11"),
    )
    problem_id = create_response.json()["id"]
    update_response = client.patch(
        f"/api/v1/patients/{patient_id}/problems/{problem_id}",
        headers=auth,
        json={"code": "E10"},
    )
    delete_response = client.delete(
        f"/api/v1/patients/{patient_id}/problems/{problem_id}",
        headers=auth,
    )

    assert create_response.status_code == 201
    assert update_response.status_code == 200
    assert update_response.json()["code"] == "E10"
    assert delete_response.status_code == 204


def test_patient_problems_write_abac_allows_admin_breakout(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
) -> None:
    auth = auth_headers(client)
    admin_auth = auth_headers(client, email="admin@oneepis.local", password="admin")
    patient_id = create_patient_for_permissions(client, auth)
    _enable_development_abac_enforcement()

    response = client.post(
        f"/api/v1/patients/{patient_id}/problems",
        headers=admin_auth,
        json=_problem_payload(title="Problema creado por breakout admin", code="E11"),
    )

    assert response.status_code == 201


def _create_problem(client: TestClient, auth: dict[str, str], patient_id: str) -> dict:
    response = client.post(
        f"/api/v1/patients/{patient_id}/problems",
        headers=auth,
        json=_problem_payload(title="Problema ABAC activo", code="E11"),
    )
    assert response.status_code == 201
    return response.json()


def _problem_payload(*, title: str, code: str) -> dict[str, str]:
    return {
        "title": title,
        "status": "active",
        "code_system": "ICD-10",
        "code": code,
        "onset_date": "2026-06-01",
        "notes": "Nota ABAC problema activo",
    }


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
