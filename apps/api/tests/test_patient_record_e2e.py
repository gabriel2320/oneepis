from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from oneepis_api.db.base import Base
from oneepis_api.db.session import get_session
from oneepis_api.main import app
from oneepis_api.models import audit as _audit_models  # noqa: F401
from oneepis_api.models import clinical_record as _clinical_models  # noqa: F401
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

    app.dependency_overrides[get_session] = override_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)


def test_patient_record_flow_writes_snapshot_and_audit(client: TestClient) -> None:
    actor = {"X-OneEpis-Actor": "dev.doctor"}
    patient_response = client.post(
        "/api/v1/patients",
        headers=actor,
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

    entry_response = client.post(
        f"/api/v1/patients/{patient_id}/clinical-entries",
        headers=actor,
        json={
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
    assert entry_response.json()["created_by"] == "dev.doctor"

    allergy_response = client.post(
        f"/api/v1/patients/{patient_id}/allergies",
        headers=actor,
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
        headers=actor,
        json={
            "name": "Paracetamol",
            "dose": "1 g",
            "route": "oral",
            "frequency": "cada 8 horas",
            "started_on": "2026-06-20",
        },
    )
    assert medication_response.status_code == 201

    vital_response = client.post(
        f"/api/v1/patients/{patient_id}/vital-signs",
        headers=actor,
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

    snapshot_response = client.get(f"/api/v1/patients/{patient_id}/record")
    assert snapshot_response.status_code == 200
    snapshot = snapshot_response.json()
    assert snapshot["patient"]["clinical_identifier"] == "ONE-001"
    assert snapshot["latest_vitals"]["heart_rate_bpm"] == 78
    assert snapshot["active_allergies"][0]["substance"] == "Penicilina"
    assert snapshot["active_medications"][0]["name"] == "Paracetamol"
    assert snapshot["recent_entries"][0]["title"] == "Evolucion SOAP"

    audit_response = client.get(f"/api/v1/patients/{patient_id}/audit-events")
    assert audit_response.status_code == 200
    audit_events = audit_response.json()
    actions = {item["action"] for item in audit_events}
    assert {
        "patient.created",
        "clinical_entry.created",
        "allergy.created",
        "medication.created",
        "vital_sign.created",
    }.issubset(actions)
    assert {item["actor_id"] for item in audit_events} == {"dev.doctor"}


def test_child_resources_return_404_for_wrong_patient(client: TestClient) -> None:
    first = client.post(
        "/api/v1/patients",
        json={
            "first_name": "A",
            "last_name": "Paciente",
            "birth_date": "1990-01-01",
            "sex_at_birth": "unknown",
        },
    ).json()
    second = client.post(
        "/api/v1/patients",
        json={
            "first_name": "B",
            "last_name": "Paciente",
            "birth_date": "1991-01-01",
            "sex_at_birth": "unknown",
        },
    ).json()
    allergy = client.post(
        f"/api/v1/patients/{first['id']}/allergies",
        json={
            "substance": "Latex",
            "severity": "unknown",
            "recorded_at": "2026-06-20T11:00:00Z",
        },
    ).json()

    response = client.get(f"/api/v1/patients/{second['id']}/allergies/{allergy['id']}")

    assert response.status_code == 404

