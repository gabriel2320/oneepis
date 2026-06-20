from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from oneepis_api.core.config import Settings, get_settings
from oneepis_api.db.base import Base
from oneepis_api.db.session import get_session
from oneepis_api.main import app
from oneepis_api.models import audit as _audit_models  # noqa: F401
from oneepis_api.models import clinical_record as _clinical_models  # noqa: F401
from oneepis_api.models import hospitalization as _hospitalization_models  # noqa: F401
from oneepis_api.models import patient as _patient_models  # noqa: F401


@pytest.fixture
def client() -> Iterator[TestClient]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    testing_session = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def override_session() -> Iterator[Session]:
        with testing_session() as session:
            yield session

    def override_settings() -> Settings:
        return Settings(ai_provider="local_rules")

    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[get_settings] = override_settings
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)


def auth_headers(
    client: TestClient,
    email: str = "medico@oneepis.local",
    password: str = "medico",
) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def create_patient_for_permissions(client: TestClient, headers: dict[str, str]) -> str:
    response = client.post(
        "/api/v1/patients",
        headers=headers,
        json={
            "first_name": "Permisos",
            "last_name": "Paciente",
            "birth_date": "1990-01-01",
            "sex_at_birth": "unknown",
        },
    )
    assert response.status_code == 201
    return str(response.json()["id"])


def test_patient_record_flow_writes_snapshot_and_audit(client: TestClient) -> None:
    auth = auth_headers(client)
    patient_response = client.post(
        "/api/v1/patients",
        headers=auth,
        json={
            "first_name": "Elena",
            "last_name": "Rojas",
            "birth_date": "1981-04-12",
            "sex_at_birth": "female",
            "clinical_identifier": "ONE-001",
        },
    )
    assert patient_response.status_code == 201
    patient_id = patient_response.json()["id"]

    encounter_response = client.post(
        f"/api/v1/patients/{patient_id}/encounters",
        headers=auth,
        json={
            "type": "ambulatory",
            "status": "in_progress",
            "reason": "Control clinico",
            "started_at": "2026-06-20T10:00:00Z",
            "location_label": "Consulta demo",
        },
    )
    assert encounter_response.status_code == 201
    assert encounter_response.json()["reason"] == "Control clinico"
    encounter_id = encounter_response.json()["id"]

    entry_response = client.post(
        f"/api/v1/patients/{patient_id}/clinical-entries",
        headers=auth,
        json={
            "encounter_id": encounter_id,
            "kind": "progress",
            "occurred_at": "2026-06-20T10:30:00Z",
            "title": "Evolucion SOAP",
            "subjective": "Refiere mejoria.",
            "objective": "Sin dificultad respiratoria.",
            "assessment": "Evolucion estable.",
            "plan": "Mantener observacion.",
            "tags": ["soap"],
        },
    )
    assert entry_response.status_code == 201
    assert entry_response.json()["created_by"] == "medico@oneepis.local"

    allergy_response = client.post(
        f"/api/v1/patients/{patient_id}/allergies",
        headers=auth,
        json={
            "substance": "Penicilina",
            "reaction": "Exantema",
            "severity": "moderate",
            "recorded_at": "2026-06-20T10:35:00Z",
        },
    )
    assert allergy_response.status_code == 201

    medication_response = client.post(
        f"/api/v1/patients/{patient_id}/medications",
        headers=auth,
        json={
            "name": "Paracetamol",
            "dose": "1 g",
            "route": "oral",
            "frequency": "cada 8 horas",
            "started_on": "2026-06-20",
        },
    )
    assert medication_response.status_code == 201

    problem_response = client.post(
        f"/api/v1/patients/{patient_id}/problems",
        headers=auth,
        json={
            "title": "Hipertension arterial",
            "code_system": "CIE-10",
            "code": "I10",
            "onset_date": "2024-01-10",
        },
    )
    assert problem_response.status_code == 201

    vital_response = client.post(
        f"/api/v1/patients/{patient_id}/vital-signs",
        headers=auth,
        json={
            "measured_at": "2026-06-20T10:40:00Z",
            "temperature_c": "36.8",
            "systolic_bp": 118,
            "diastolic_bp": 72,
            "heart_rate_bpm": 78,
            "oxygen_saturation_pct": "98.0",
        },
    )
    assert vital_response.status_code == 201

    snapshot_response = client.get(f"/api/v1/patients/{patient_id}/record", headers=auth)
    assert snapshot_response.status_code == 200
    snapshot = snapshot_response.json()
    assert snapshot["patient"]["clinical_identifier"] == "ONE-001"
    assert snapshot["patient"]["clinical_status"] == "active"
    assert snapshot["patient"]["current_care_context"] == "unknown"
    assert snapshot["active_problems"][0]["title"] == "Hipertension arterial"
    assert snapshot["active_problems"][0]["code"] == "I10"
    assert snapshot["latest_vitals"]["heart_rate_bpm"] == 78
    assert snapshot["active_allergies"][0]["substance"] == "Penicilina"
    assert snapshot["active_medications"][0]["name"] == "Paracetamol"
    assert snapshot["recent_entries"][0]["title"] == "Evolucion SOAP"
    assert snapshot["recent_entries"][0]["encounter_id"] == encounter_id

    audit_response = client.get(f"/api/v1/patients/{patient_id}/audit-events", headers=auth)
    assert audit_response.status_code == 200
    audit_events = audit_response.json()
    actions = {item["action"] for item in audit_events}
    assert {
        "patient.created",
        "encounter.created",
        "clinical_entry.created",
        "allergy.created",
        "medication.created",
        "problem.created",
        "vital_sign.created",
    }.issubset(actions)
    assert {item["actor_id"] for item in audit_events} == {"medico@oneepis.local"}


def test_child_resources_return_404_for_wrong_patient(client: TestClient) -> None:
    auth = auth_headers(client)
    first = client.post(
        "/api/v1/patients",
        headers=auth,
        json={
            "first_name": "A",
            "last_name": "Paciente",
            "birth_date": "1990-01-01",
            "sex_at_birth": "unknown",
        },
    ).json()
    second = client.post(
        "/api/v1/patients",
        headers=auth,
        json={
            "first_name": "B",
            "last_name": "Paciente",
            "birth_date": "1991-01-01",
            "sex_at_birth": "unknown",
        },
    ).json()
    allergy = client.post(
        f"/api/v1/patients/{first['id']}/allergies",
        headers=auth,
        json={
            "substance": "Latex",
            "severity": "unknown",
            "recorded_at": "2026-06-20T11:00:00Z",
        },
    ).json()

    response = client.get(
        f"/api/v1/patients/{second['id']}/allergies/{allergy['id']}",
        headers=auth,
    )

    assert response.status_code == 404

    encounter = client.post(
        f"/api/v1/patients/{first['id']}/encounters",
        headers=auth,
        json={
            "type": "ambulatory",
            "reason": "Encuentro de otro paciente",
            "started_at": "2026-06-20T11:10:00Z",
        },
    ).json()

    cross_entry_response = client.post(
        f"/api/v1/patients/{second['id']}/clinical-entries",
        headers=auth,
        json={
            "encounter_id": encounter["id"],
            "kind": "progress",
            "occurred_at": "2026-06-20T11:20:00Z",
            "title": "SOAP cruzada",
        },
    )

    assert cross_entry_response.status_code == 404


def test_patient_ai_suggestions_use_snapshot_without_persisting(client: TestClient) -> None:
    auth = auth_headers(client)
    patient_response = client.post(
        "/api/v1/patients",
        headers=auth,
        json={
            "first_name": "C",
            "last_name": "Paciente",
            "birth_date": "1992-01-01",
            "sex_at_birth": "unknown",
        },
    )
    assert patient_response.status_code == 201
    patient_id = patient_response.json()["id"]

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


def test_patient_ai_suggestions_return_404_for_missing_patient(client: TestClient) -> None:
    auth = auth_headers(client)
    response = client.post(
        "/api/v1/patients/11111111-1111-4111-8111-111111111111/ai/suggestions",
        headers=auth,
        json={"focus": "summary"},
    )

    assert response.status_code == 404


def test_patient_routes_require_authentication(client: TestClient) -> None:
    response = client.get("/api/v1/patients")

    assert response.status_code == 401


def test_readonly_user_cannot_write_patient(client: TestClient) -> None:
    auth = auth_headers(client, email="lector@oneepis.local", password="lector")

    response = client.post(
        "/api/v1/patients",
        headers=auth,
        json={
            "first_name": "Solo",
            "last_name": "Lectura",
            "birth_date": "1990-01-01",
            "sex_at_birth": "unknown",
        },
    )

    assert response.status_code == 403


def test_readonly_user_can_read_patient_snapshot(client: TestClient) -> None:
    patient_id = create_patient_for_permissions(client, auth_headers(client))
    readonly_auth = auth_headers(client, email="lector@oneepis.local", password="lector")

    response = client.get(f"/api/v1/patients/{patient_id}/record", headers=readonly_auth)

    assert response.status_code == 200
    assert response.json()["patient"]["id"] == patient_id


def test_nursing_can_record_vitals_but_not_medical_actions(client: TestClient) -> None:
    patient_id = create_patient_for_permissions(client, auth_headers(client))
    nursing_auth = auth_headers(client, email="enfermeria@oneepis.local", password="enfermeria")

    vitals_response = client.post(
        f"/api/v1/patients/{patient_id}/vital-signs",
        headers=nursing_auth,
        json={
            "measured_at": "2026-06-20T12:00:00Z",
            "systolic_bp": 120,
            "diastolic_bp": 70,
            "heart_rate_bpm": 80,
        },
    )
    assert vitals_response.status_code == 201
    assert vitals_response.json()["heart_rate_bpm"] == 80

    entry_response = client.post(
        f"/api/v1/patients/{patient_id}/clinical-entries",
        headers=nursing_auth,
        json={
            "kind": "progress",
            "occurred_at": "2026-06-20T12:05:00Z",
            "title": "Evolucion SOAP",
        },
    )
    assert entry_response.status_code == 403

    medication_response = client.post(
        f"/api/v1/patients/{patient_id}/medications",
        headers=nursing_auth,
        json={"name": "Ibuprofeno", "started_on": "2026-06-20"},
    )
    assert medication_response.status_code == 403

    problem_response = client.post(
        f"/api/v1/patients/{patient_id}/problems",
        headers=nursing_auth,
        json={"title": "Dolor toracico"},
    )
    assert problem_response.status_code == 403

    encounter_response = client.post(
        f"/api/v1/patients/{patient_id}/encounters",
        headers=nursing_auth,
        json={
            "type": "hospitalization",
            "reason": "Ingreso hospitalario",
            "started_at": "2026-06-20T12:10:00Z",
        },
    )
    assert encounter_response.status_code == 403

    ai_response = client.post(
        f"/api/v1/patients/{patient_id}/ai/suggestions",
        headers=nursing_auth,
        json={"focus": "summary"},
    )
    assert ai_response.status_code == 403


def test_audit_events_include_correlation_and_before_after(client: TestClient) -> None:
    auth = auth_headers(client)
    patient_id = create_patient_for_permissions(client, auth)
    headers = {**auth, "X-OneEpis-Correlation-ID": "corr-test-001"}

    update_response = client.patch(
        f"/api/v1/patients/{patient_id}",
        headers=headers,
        json={"last_name": "Auditado"},
    )
    assert update_response.status_code == 200
    assert update_response.headers["X-OneEpis-Correlation-ID"] == "corr-test-001"

    audit_response = client.get(f"/api/v1/patients/{patient_id}/audit-events", headers=auth)
    assert audit_response.status_code == 200
    patient_update = next(
        item for item in audit_response.json() if item["action"] == "patient.updated"
    )

    assert patient_update["correlation_id"] == "corr-test-001"
    assert patient_update["request_method"] == "PATCH"
    assert patient_update["request_path"] == f"/api/v1/patients/{patient_id}"
    assert patient_update["extra_data"]["before"] == {"last_name": "Paciente"}
    assert patient_update["extra_data"]["after"] == {"last_name": "Auditado"}


def test_patient_status_and_problem_update_are_audited(client: TestClient) -> None:
    auth = auth_headers(client)
    patient_id = create_patient_for_permissions(client, auth)

    status_response = client.patch(
        f"/api/v1/patients/{patient_id}",
        headers=auth,
        json={"clinical_status": "closed", "current_care_context": "ambulatory"},
    )
    assert status_response.status_code == 200
    assert status_response.json()["clinical_status"] == "closed"
    assert status_response.json()["current_care_context"] == "ambulatory"

    problem_response = client.post(
        f"/api/v1/patients/{patient_id}/problems",
        headers=auth,
        json={"title": "Diabetes tipo 2", "status": "active"},
    )
    assert problem_response.status_code == 201
    problem_id = problem_response.json()["id"]

    update_response = client.patch(
        f"/api/v1/patients/{patient_id}/problems/{problem_id}",
        headers=auth,
        json={"status": "resolved", "resolved_on": "2026-06-20"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["status"] == "resolved"

    snapshot_response = client.get(f"/api/v1/patients/{patient_id}/record", headers=auth)
    assert snapshot_response.status_code == 200
    assert snapshot_response.json()["active_problems"] == []

    list_response = client.get(f"/api/v1/patients/{patient_id}/problems", headers=auth)
    assert list_response.status_code == 200
    assert list_response.json() == []

    audit_response = client.get(f"/api/v1/patients/{patient_id}/audit-events", headers=auth)
    assert audit_response.status_code == 200
    problem_update = next(
        item for item in audit_response.json() if item["action"] == "problem.updated"
    )
    assert problem_update["extra_data"]["before"] == {
        "status": "active",
        "resolved_on": None,
    }
    assert problem_update["extra_data"]["after"] == {
        "status": "resolved",
        "resolved_on": "2026-06-20",
    }


def test_encounter_update_and_cancel_are_audited(client: TestClient) -> None:
    auth = auth_headers(client)
    patient_id = create_patient_for_permissions(client, auth)

    create_response = client.post(
        f"/api/v1/patients/{patient_id}/encounters",
        headers=auth,
        json={
            "type": "hospitalization",
            "status": "in_progress",
            "reason": "Ingreso hospitalario",
            "started_at": "2026-06-20T08:00:00Z",
            "location_label": "Sala 2",
        },
    )
    assert create_response.status_code == 201
    encounter_id = create_response.json()["id"]

    list_response = client.get(f"/api/v1/patients/{patient_id}/encounters", headers=auth)
    assert list_response.status_code == 200
    assert list_response.json()[0]["id"] == encounter_id

    update_response = client.patch(
        f"/api/v1/patients/{patient_id}/encounters/{encounter_id}",
        headers=auth,
        json={
            "status": "completed",
            "ended_at": "2026-06-20T18:00:00Z",
            "notes": "Cierre administrativo de desarrollo",
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["status"] == "completed"

    cancel_response = client.delete(
        f"/api/v1/patients/{patient_id}/encounters/{encounter_id}",
        headers=auth,
    )
    assert cancel_response.status_code == 204

    get_response = client.get(
        f"/api/v1/patients/{patient_id}/encounters/{encounter_id}",
        headers=auth,
    )
    assert get_response.status_code == 200
    assert get_response.json()["status"] == "cancelled"

    audit_response = client.get(f"/api/v1/patients/{patient_id}/audit-events", headers=auth)
    assert audit_response.status_code == 200
    events = audit_response.json()
    encounter_update = next(item for item in events if item["action"] == "encounter.updated")
    assert encounter_update["extra_data"]["before"] == {
        "status": "in_progress",
        "ended_at": None,
        "notes": None,
    }
    assert encounter_update["extra_data"]["after"] == {
        "status": "completed",
        "ended_at": "2026-06-20T18:00:00+00:00",
        "notes": "Cierre administrativo de desarrollo",
    }
    encounter_cancel = next(item for item in events if item["action"] == "encounter.cancelled")
    assert encounter_cancel["extra_data"]["after"] == {"status": "cancelled"}


def test_hospitalization_board_lists_active_hospitalizations_only(
    client: TestClient,
) -> None:
    auth = auth_headers(client)
    active_patient_id = create_patient_for_permissions(client, auth)
    completed_patient_id = create_patient_for_permissions(client, auth)

    active_response = client.post(
        f"/api/v1/patients/{active_patient_id}/encounters",
        headers=auth,
        json={
            "type": "hospitalization",
            "status": "in_progress",
            "reason": "Ingreso activo",
            "started_at": "2026-06-20T07:00:00Z",
            "location_label": "Sala A / Cama 1",
        },
    )
    assert active_response.status_code == 201
    active_encounter_id = active_response.json()["id"]

    completed_response = client.post(
        f"/api/v1/patients/{completed_patient_id}/encounters",
        headers=auth,
        json={
            "type": "hospitalization",
            "status": "completed",
            "reason": "Ingreso cerrado",
            "started_at": "2026-06-19T07:00:00Z",
            "ended_at": "2026-06-20T07:00:00Z",
        },
    )
    assert completed_response.status_code == 201

    ambulatory_response = client.post(
        f"/api/v1/patients/{active_patient_id}/encounters",
        headers=auth,
        json={
            "type": "ambulatory",
            "status": "in_progress",
            "reason": "Consulta activa",
            "started_at": "2026-06-20T08:00:00Z",
        },
    )
    assert ambulatory_response.status_code == 201

    board_response = client.get("/api/v1/hospitalization/active", headers=auth)
    assert board_response.status_code == 200
    payload = board_response.json()
    assert len(payload) == 1
    assert payload[0]["patient"]["id"] == active_patient_id
    assert payload[0]["encounter"]["id"] == active_encounter_id
    assert payload[0]["encounter"]["location_label"] == "Sala A / Cama 1"


def test_hospital_bed_assignment_enriches_board_and_audit(client: TestClient) -> None:
    auth = auth_headers(client)
    patient_id = create_patient_for_permissions(client, auth)

    encounter_response = client.post(
        f"/api/v1/patients/{patient_id}/encounters",
        headers=auth,
        json={
            "type": "hospitalization",
            "status": "in_progress",
            "reason": "Ingreso con cama",
            "started_at": "2026-06-20T09:00:00Z",
            "location_label": "Ubicacion libre",
        },
    )
    assert encounter_response.status_code == 201
    encounter_id = encounter_response.json()["id"]

    bed_response = client.post(
        "/api/v1/hospitalization/beds",
        headers=auth,
        json={
            "ward": "Medicina",
            "room": "301",
            "bed_label": "A",
            "status": "occupied",
            "encounter_id": encounter_id,
        },
    )
    assert bed_response.status_code == 201
    bed_payload = bed_response.json()
    assert bed_payload["encounter_id"] == encounter_id

    beds_response = client.get("/api/v1/hospitalization/beds", headers=auth)
    assert beds_response.status_code == 200
    assert beds_response.json()[0]["ward"] == "Medicina"

    board_response = client.get("/api/v1/hospitalization/active", headers=auth)
    assert board_response.status_code == 200
    board_payload = board_response.json()
    assert board_payload[0]["bed"]["id"] == bed_payload["id"]
    assert board_payload[0]["bed"]["room"] == "301"

    audit_response = client.get(f"/api/v1/patients/{patient_id}/audit-events", headers=auth)
    assert audit_response.status_code == 200
    assert any(
        event["action"] == "hospital_bed.created"
        and event["extra_data"]["encounter_id"] == encounter_id
        for event in audit_response.json()
    )


def test_hospital_bed_assignment_requires_active_hospitalization(client: TestClient) -> None:
    auth = auth_headers(client)
    patient_id = create_patient_for_permissions(client, auth)

    missing_encounter_response = client.post(
        "/api/v1/hospitalization/beds",
        headers=auth,
        json={
            "ward": "Medicina",
            "room": "302",
            "bed_label": "A",
            "status": "occupied",
        },
    )
    assert missing_encounter_response.status_code == 409

    ambulatory_response = client.post(
        f"/api/v1/patients/{patient_id}/encounters",
        headers=auth,
        json={
            "type": "ambulatory",
            "status": "in_progress",
            "reason": "Consulta activa",
            "started_at": "2026-06-20T10:00:00Z",
        },
    )
    assert ambulatory_response.status_code == 201

    invalid_assignment_response = client.post(
        "/api/v1/hospitalization/beds",
        headers=auth,
        json={
            "ward": "Medicina",
            "room": "302",
            "bed_label": "B",
            "status": "occupied",
            "encounter_id": ambulatory_response.json()["id"],
        },
    )
    assert invalid_assignment_response.status_code == 409


def test_hospitalization_board_requires_authentication(client: TestClient) -> None:
    response = client.get("/api/v1/hospitalization/active")

    assert response.status_code == 401


def test_clinical_entry_can_be_linked_and_unlinked_from_encounter(
    client: TestClient,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient_for_permissions(client, auth)
    encounter_response = client.post(
        f"/api/v1/patients/{patient_id}/encounters",
        headers=auth,
        json={
            "type": "ambulatory",
            "reason": "Control longitudinal",
            "started_at": "2026-06-20T09:00:00Z",
        },
    )
    assert encounter_response.status_code == 201
    encounter_id = encounter_response.json()["id"]

    entry_response = client.post(
        f"/api/v1/patients/{patient_id}/clinical-entries",
        headers=auth,
        json={
            "kind": "progress",
            "occurred_at": "2026-06-20T09:30:00Z",
            "title": "SOAP sin encuentro",
        },
    )
    assert entry_response.status_code == 201
    entry_id = entry_response.json()["id"]
    assert entry_response.json()["encounter_id"] is None

    link_response = client.patch(
        f"/api/v1/patients/{patient_id}/clinical-entries/{entry_id}",
        headers=auth,
        json={"encounter_id": encounter_id},
    )
    assert link_response.status_code == 200
    assert link_response.json()["encounter_id"] == encounter_id

    unlink_response = client.patch(
        f"/api/v1/patients/{patient_id}/clinical-entries/{entry_id}",
        headers=auth,
        json={"encounter_id": None},
    )
    assert unlink_response.status_code == 200
    assert unlink_response.json()["encounter_id"] is None

    audit_response = client.get(f"/api/v1/patients/{patient_id}/audit-events", headers=auth)
    assert audit_response.status_code == 200
    updates = [
        item
        for item in audit_response.json()
        if item["action"] == "clinical_entry.updated"
    ]
    assert any(item["extra_data"]["after"] == {"encounter_id": encounter_id} for item in updates)
    assert any(item["extra_data"]["after"] == {"encounter_id": None} for item in updates)
