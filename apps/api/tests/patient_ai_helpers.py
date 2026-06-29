import uuid

from fastapi.testclient import TestClient
from sqlalchemy import or_, select

from oneepis_api.db.session import get_session
from oneepis_api.main import app
from oneepis_api.models.audit import AuditEvent


def create_patient(
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


def create_entry(
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


def create_problem(
    client: TestClient,
    auth: dict[str, str],
    patient_id: str,
    *,
    title: str,
    notes: str | None = None,
    code_system: str | None = None,
    code: str | None = None,
) -> str:
    response = client.post(
        f"/api/v1/patients/{patient_id}/problems",
        headers=auth,
        json={
            "title": title,
            "onset_date": "2026-06-01",
            "notes": notes,
            "code_system": code_system,
            "code": code,
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def create_event(
    client: TestClient,
    auth: dict[str, str],
    patient_id: str,
    *,
    summary: str,
    occurred_at: str = "2026-06-20T12:00:00Z",
    payload: dict | None = None,
) -> str:
    response = client.post(
        f"/api/v1/patients/{patient_id}/clinical-events",
        headers=auth,
        json={
            "event_type": "clinical_note",
            "occurred_at": occurred_at,
            "summary": summary,
            "source_type": "manual",
            "payload": payload or {},
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def create_vitals(
    client: TestClient,
    auth: dict[str, str],
    patient_id: str,
    *,
    measured_at: str,
    temperature_c: str | None = None,
    systolic_bp: int | None = None,
    heart_rate_bpm: int | None = None,
    respiratory_rate_bpm: int | None = None,
    oxygen_saturation_pct: str | None = None,
) -> str:
    response = client.post(
        f"/api/v1/patients/{patient_id}/vital-signs",
        headers=auth,
        json={
            "measured_at": measured_at,
            "temperature_c": temperature_c,
            "systolic_bp": systolic_bp,
            "heart_rate_bpm": heart_rate_bpm,
            "respiratory_rate_bpm": respiratory_rate_bpm,
            "oxygen_saturation_pct": oxygen_saturation_pct,
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def create_lab_panel(
    client: TestClient,
    auth: dict[str, str],
    patient_id: str,
    *,
    panel_name: str = "Perfil renal",
    result_name: str = "Creatinina",
    code: str = "creatinina",
    value: str = "1.10",
    unit: str = "mg/dL",
    status: str = "active",
) -> dict:
    response = client.post(
        f"/api/v1/patients/{patient_id}/lab-panels",
        headers=auth,
        json={
            "occurred_at": "2026-06-20T09:00:00Z",
            "panel_name": panel_name,
            "results": [
                {
                    "code": code,
                    "name": result_name,
                    "value": value,
                    "numeric_value": value,
                    "unit": unit,
                    "status": status,
                }
            ],
        },
    )
    assert response.status_code == 201
    return response.json()


def audit_events(client: TestClient, auth: dict[str, str], patient_id: str) -> list[dict]:
    override_session = app.dependency_overrides[get_session]
    session_iterator = override_session()
    session = next(session_iterator)
    try:
        patient_uuid = uuid.UUID(patient_id)
        statement = (
            select(AuditEvent)
            .where(
                or_(
                    AuditEvent.entity_id == patient_uuid,
                    AuditEvent.extra_data["patient_id"].as_string() == patient_id,
                )
            )
            .order_by(AuditEvent.created_at.desc())
        )
        return [
            {
                "id": str(event.id),
                "action": event.action,
                "entity_type": event.entity_type,
                "entity_id": str(event.entity_id) if event.entity_id else None,
                "actor_id": event.actor_id,
                "correlation_id": event.correlation_id,
                "request_method": event.request_method,
                "request_path": event.request_path,
                "extra_data": event.extra_data,
                "created_at": event.created_at.isoformat(),
            }
            for event in session.scalars(statement).all()
        ]
    finally:
        session_iterator.close()


def first_event_proposal_from_entry(
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
