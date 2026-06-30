from fastapi.testclient import TestClient
from sqlalchemy import select

from oneepis_api.db.session import get_session
from oneepis_api.main import app
from oneepis_api.models.audit import AuditEvent


def test_break_glass_header_is_rejected_on_clinical_routes(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient_for_permissions(client, auth)

    response = client.get(
        f"/api/v1/patients/{patient_id}/record",
        headers={**auth, "X-OneEpis-Break-Glass": "true"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Contextual access override is not enabled."


def test_contextual_access_headers_are_rejected_until_abac_exists(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient_for_permissions(client, auth)

    for header in [
        "X-OneEpis-Access-Reason",
        "X-OneEpis-Institution",
        "X-OneEpis-Tenant",
        "X-OneEpis-Care-Team",
    ]:
        response = client.get(
            f"/api/v1/patients/{patient_id}/record",
            headers={**auth, header: "demo"},
        )

        assert response.status_code == 403
        assert response.json()["detail"] == "Contextual access override is not enabled."


def test_empty_contextual_access_header_is_rejected_on_clinical_routes(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient_for_permissions(client, auth)

    response = client.get(
        f"/api/v1/patients/{patient_id}/record",
        headers={**auth, "X-OneEpis-Tenant": ""},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Contextual access override is not enabled."


def test_empty_contextual_access_header_does_not_block_non_clinical_routes(
    client: TestClient,
    auth_headers,
) -> None:
    auth = auth_headers(client)

    response = client.get("/api/v1/health", headers={**auth, "X-OneEpis-Tenant": ""})

    assert response.status_code == 200


def test_contextual_access_header_rejection_emits_minimized_security_audit(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient_for_permissions(client, auth)

    response = client.get(
        f"/api/v1/patients/{patient_id}/record",
        headers={
            **auth,
            "X-OneEpis-Correlation-ID": "blocked-contextual-access-001",
            "X-OneEpis-Tenant": "tenant-libre-no-auditable",
            "X-OneEpis-Access-Reason": "motivo-libre-no-auditable",
        },
    )

    assert response.status_code == 403
    audit_event = _latest_contextual_access_block_event()
    assert audit_event.actor_id == "system"
    assert audit_event.entity_type == "security"
    assert audit_event.entity_id is None
    assert audit_event.correlation_id == "blocked-contextual-access-001"
    assert audit_event.request_method == "GET"
    assert audit_event.request_path == f"/api/v1/patients/{patient_id}/record"
    assert audit_event.extra_data == {
        "blocked_headers": ["X-OneEpis-Access-Reason", "X-OneEpis-Tenant"],
        "header_count": 2,
    }


def test_contextual_access_header_audit_truncates_long_request_path(
    client: TestClient,
    auth_headers,
) -> None:
    auth = auth_headers(client)
    long_path = "/api/v1/patients/" + ("a" * 280)

    response = client.get(
        long_path,
        headers={
            **auth,
            "X-OneEpis-Correlation-ID": "blocked-contextual-access-long-path",
            "X-OneEpis-Tenant": "",
        },
    )

    assert response.status_code == 403
    audit_event = _latest_contextual_access_block_event()
    assert audit_event.correlation_id == "blocked-contextual-access-long-path"
    assert audit_event.request_method == "GET"
    assert audit_event.request_path == long_path[:240]
    assert len(audit_event.request_path) == 240


def test_contextual_access_header_rejection_response_and_audit_share_generated_correlation(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient_for_permissions(client, auth)

    response = client.get(
        f"/api/v1/patients/{patient_id}/record",
        headers={**auth, "X-OneEpis-Tenant": "tenant-bloqueado"},
    )

    assert response.status_code == 403
    correlation_id = response.headers["X-OneEpis-Correlation-ID"]
    assert correlation_id.startswith("oneepis-")
    audit_event = _contextual_access_block_event_by_correlation(correlation_id)
    assert audit_event.correlation_id == correlation_id
    assert audit_event.request_method == "GET"
    assert audit_event.request_path == f"/api/v1/patients/{patient_id}/record"


def test_clinical_routes_still_work_without_break_glass_header(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient_for_permissions(client, auth)

    response = client.get(f"/api/v1/patients/{patient_id}/record", headers=auth)

    assert response.status_code == 200


def _latest_contextual_access_block_event() -> AuditEvent:
    override_session = app.dependency_overrides[get_session]
    session_iterator = override_session()
    session = next(session_iterator)
    try:
        return session.scalars(
            select(AuditEvent)
            .where(AuditEvent.action == "security.contextual_access_header_blocked")
            .order_by(AuditEvent.created_at.desc())
            .limit(1)
        ).one()
    finally:
        session_iterator.close()


def _contextual_access_block_event_by_correlation(correlation_id: str) -> AuditEvent:
    override_session = app.dependency_overrides[get_session]
    session_iterator = override_session()
    session = next(session_iterator)
    try:
        return session.scalars(
            select(AuditEvent).where(
                AuditEvent.action == "security.contextual_access_header_blocked",
                AuditEvent.correlation_id == correlation_id,
            )
        ).one()
    finally:
        session_iterator.close()
