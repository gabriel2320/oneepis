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


def test_hospital_draft_reads_abac_denies_without_active_relationship(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
    audit_events_for_patient,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient_for_permissions(client, auth)
    daily_sheet, indication = _create_hospital_drafts(client, auth, patient_id)
    _enable_development_abac_enforcement()

    daily_response = client.get(
        f"/api/v1/hospitalization/patients/{patient_id}/daily-sheets",
        headers=auth,
    )
    indication_response = client.get(
        f"/api/v1/hospitalization/patients/{patient_id}/indications",
        headers=auth,
    )

    assert daily_sheet["patient_id"] == patient_id
    assert indication["patient_id"] == patient_id
    assert daily_response.status_code == 403
    assert indication_response.status_code == 403
    actions = [event["action"] for event in audit_events_for_patient(patient_id)]
    assert actions.count("access_context.denied") == 2
    assert "hospital_daily_sheets.read" not in actions
    assert "hospital_indications.read" not in actions


def test_hospital_draft_reads_abac_allows_active_relationship(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient_for_permissions(client, auth)
    daily_sheet, indication = _create_hospital_drafts(client, auth, patient_id)
    _assign_patient_scope(
        patient_id=patient_id,
        actor_id="medico@oneepis.local",
    )
    _enable_development_abac_enforcement()

    daily_response = client.get(
        f"/api/v1/hospitalization/patients/{patient_id}/daily-sheets",
        headers=auth,
    )
    indication_response = client.get(
        f"/api/v1/hospitalization/patients/{patient_id}/indications",
        headers=auth,
    )

    assert daily_response.status_code == 200
    assert [item["id"] for item in daily_response.json()] == [daily_sheet["id"]]
    assert indication_response.status_code == 200
    assert [item["id"] for item in indication_response.json()] == [indication["id"]]


def _create_hospital_drafts(
    client: TestClient,
    auth: dict[str, str],
    patient_id: str,
) -> tuple[dict, dict]:
    encounter_response = client.post(
        f"/api/v1/patients/{patient_id}/encounters",
        headers=auth,
        json={
            "type": "hospitalization",
            "status": "in_progress",
            "reason": "Ingreso ABAC hospitalario",
            "started_at": "2026-06-20T07:00:00Z",
        },
    )
    assert encounter_response.status_code == 201
    daily_response = client.post(
        f"/api/v1/hospitalization/patients/{patient_id}/daily-sheets",
        headers=auth,
        json={
            "sheet_date": "2026-06-20",
            "clinical_summary": "Hoja diaria ABAC.",
        },
    )
    assert daily_response.status_code == 201
    indication_response = client.post(
        f"/api/v1/hospitalization/patients/{patient_id}/indications",
        headers=auth,
        json={
            "indicated_at": "2026-06-20T10:00:00Z",
            "title": "Indicacion ABAC",
            "indication_text": "Mantener observacion en borrador.",
        },
    )
    assert indication_response.status_code == 201
    return daily_response.json(), indication_response.json()


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
