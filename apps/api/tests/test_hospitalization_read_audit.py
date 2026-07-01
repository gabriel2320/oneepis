from fastapi.testclient import TestClient
from sqlalchemy import select

from oneepis_api.db.session import get_session
from oneepis_api.main import app
from oneepis_api.models.audit import AuditEvent


def test_hospitalization_indexes_emit_minimized_read_audit(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient_for_permissions(client, auth)

    encounter_response = client.post(
        f"/api/v1/patients/{patient_id}/encounters",
        headers=auth,
        json={
            "type": "hospitalization",
            "status": "in_progress",
            "reason": "Ingreso activo auditado",
            "started_at": "2026-06-20T07:00:00Z",
            "location_label": "Sala sensible",
        },
    )
    assert encounter_response.status_code == 201

    bed_response = client.post(
        "/api/v1/hospitalization/beds",
        headers=auth,
        json={
            "ward": "Medicina",
            "room": "301",
            "bed_label": "A",
            "status": "available",
            "notes": "Nota libre sensible de cama",
        },
    )
    assert bed_response.status_code == 201

    beds_response = client.get(
        "/api/v1/hospitalization/beds?limit=10",
        headers={**auth, "X-OneEpis-Correlation-ID": "hospital-beds-read-001"},
    )
    board_response = client.get(
        "/api/v1/hospitalization/active?limit=10",
        headers={**auth, "X-OneEpis-Correlation-ID": "hospital-board-read-001"},
    )

    assert beds_response.status_code == 200
    assert board_response.status_code == 200

    beds_audit = _audit_event("hospital_beds.read", "hospital-beds-read-001")
    assert beds_audit.entity_type == "hospital_bed_index"
    assert beds_audit.entity_id is None
    assert beds_audit.actor_id == "medico@oneepis.local"
    assert beds_audit.request_method == "GET"
    assert beds_audit.request_path == "/api/v1/hospitalization/beds"
    assert beds_audit.extra_data == {"limit": 10, "result_count": 1}

    board_audit = _audit_event("hospitalization_board.read", "hospital-board-read-001")
    assert board_audit.entity_type == "hospitalization_board"
    assert board_audit.entity_id is None
    assert board_audit.actor_id == "medico@oneepis.local"
    assert board_audit.request_method == "GET"
    assert board_audit.request_path == "/api/v1/hospitalization/active"
    assert board_audit.extra_data == {"limit": 10, "result_count": 1}

    audit_payload = str([beds_audit.extra_data, board_audit.extra_data])
    assert "Nota libre sensible" not in audit_payload
    assert "Sala sensible" not in audit_payload
    assert patient_id not in audit_payload


def _audit_event(action: str, correlation_id: str) -> AuditEvent:
    session_provider = app.dependency_overrides[get_session]
    session_iterator = session_provider()
    session = next(session_iterator)
    try:
        event = session.scalar(
            select(AuditEvent).where(
                AuditEvent.action == action,
                AuditEvent.correlation_id == correlation_id,
            )
        )
        assert event is not None
        return event
    finally:
        session_iterator.close()
