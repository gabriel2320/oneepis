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
from oneepis_api.models.access_boundary import AccessBoundaryStatus
from oneepis_api.models.patient import Patient


def test_hospitalization_active_abac_filters_to_active_relationship(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
) -> None:
    auth = auth_headers(client)
    visible_patient_id = create_patient_for_permissions(client, auth)
    inactive_patient_id = create_patient_for_permissions(client, auth)
    unscoped_patient_id = create_patient_for_permissions(client, auth)
    _create_hospitalization(client, auth, visible_patient_id, "2026-06-20T10:00:00Z")
    _create_hospitalization(client, auth, inactive_patient_id, "2026-06-20T09:00:00Z")
    _create_hospitalization(client, auth, unscoped_patient_id, "2026-06-20T08:00:00Z")
    _assign_patient_scope(
        patient_id=visible_patient_id,
        actor_id="medico@oneepis.local",
    )
    _assign_patient_scope(
        patient_id=inactive_patient_id,
        actor_id="medico@oneepis.local",
        care_team_status=AccessBoundaryStatus.RETIRED,
    )
    _enable_development_abac_enforcement()

    response = client.get("/api/v1/hospitalization/active?limit=50", headers=auth)

    assert response.status_code == 200
    patient_ids = [item["patient"]["id"] for item in response.json()]
    assert patient_ids == [visible_patient_id]
    assert inactive_patient_id not in patient_ids
    assert unscoped_patient_id not in patient_ids


def test_hospitalization_active_abac_keeps_admin_global_index(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
) -> None:
    auth = auth_headers(client)
    first_patient_id = create_patient_for_permissions(client, auth)
    second_patient_id = create_patient_for_permissions(client, auth)
    _create_hospitalization(client, auth, first_patient_id, "2026-06-20T10:00:00Z")
    _create_hospitalization(client, auth, second_patient_id, "2026-06-20T09:00:00Z")
    admin_auth = auth_headers(client, email="admin@oneepis.local", password="admin")
    _enable_development_abac_enforcement()

    response = client.get("/api/v1/hospitalization/active?limit=50", headers=admin_auth)

    assert response.status_code == 200
    patient_ids = {item["patient"]["id"] for item in response.json()}
    assert {first_patient_id, second_patient_id}.issubset(patient_ids)


def _create_hospitalization(
    client: TestClient,
    auth: dict[str, str],
    patient_id: str,
    started_at: str,
) -> str:
    response = client.post(
        f"/api/v1/patients/{patient_id}/encounters",
        headers=auth,
        json={
            "type": "hospitalization",
            "status": "in_progress",
            "reason": "Ingreso ABAC hospitalario",
            "started_at": started_at,
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def _enable_development_abac_enforcement() -> None:
    app.dependency_overrides[get_settings] = lambda: Settings(
        ai_provider="local_rules",
        abac_enforcement_enabled=True,
    )


def _assign_patient_scope(
    *,
    patient_id: str,
    actor_id: str,
    care_team_status: AccessBoundaryStatus = AccessBoundaryStatus.ACTIVE,
) -> None:
    with _test_session() as session:
        patient = session.get(Patient, uuid.UUID(patient_id))
        assert patient is not None
        care_team = create_care_team(session, care_team_status=care_team_status)
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
