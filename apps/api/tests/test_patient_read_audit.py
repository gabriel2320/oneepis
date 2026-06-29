from fastapi.testclient import TestClient


def test_patient_read_endpoints_emit_read_audit_events(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient_for_permissions(client, auth)

    patient_read_headers = {**auth, "X-OneEpis-Correlation-ID": "read-patient-001"}
    record_read_headers = {**auth, "X-OneEpis-Correlation-ID": "read-record-001"}

    patient_response = client.get(
        f"/api/v1/patients/{patient_id}",
        headers=patient_read_headers,
    )
    assert patient_response.status_code == 200
    assert patient_response.headers["X-OneEpis-Correlation-ID"] == "read-patient-001"

    record_response = client.get(
        f"/api/v1/patients/{patient_id}/record",
        headers=record_read_headers,
    )
    assert record_response.status_code == 200
    assert record_response.headers["X-OneEpis-Correlation-ID"] == "read-record-001"

    audit_response = client.get(f"/api/v1/patients/{patient_id}/audit-events", headers=auth)
    assert audit_response.status_code == 200
    audit_events = audit_response.json()
    actions = [item["action"] for item in audit_events]
    assert actions.count("patient.read") == 1
    assert actions.count("record.read") == 1
    read_events = [item for item in audit_events if item["action"].endswith(".read")]
    assert {item["actor_id"] for item in read_events} == {"medico@oneepis.local"}
    patient_read = next(item for item in read_events if item["action"] == "patient.read")
    assert patient_read["correlation_id"] == "read-patient-001"
    assert patient_read["request_method"] == "GET"
    assert patient_read["request_path"] == f"/api/v1/patients/{patient_id}"
    record_read = next(item for item in read_events if item["action"] == "record.read")
    assert record_read["correlation_id"] == "read-record-001"
    assert record_read["request_method"] == "GET"
    assert record_read["request_path"] == f"/api/v1/patients/{patient_id}/record"


def test_patient_read_audit_dedupes_repeated_same_route_reads(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient_for_permissions(client, auth)

    for index in range(3):
        response = client.get(
            f"/api/v1/patients/{patient_id}/record",
            headers={**auth, "X-OneEpis-Correlation-ID": f"dedupe-read-00{index + 1}"},
        )
        assert response.status_code == 200

    audit_response = client.get(f"/api/v1/patients/{patient_id}/audit-events", headers=auth)
    assert audit_response.status_code == 200
    record_reads = [
        item for item in audit_response.json() if item["action"] == "record.read"
    ]
    assert len(record_reads) == 1
    assert record_reads[0]["correlation_id"] == "dedupe-read-001"
    assert record_reads[0]["request_method"] == "GET"
    assert record_reads[0]["request_path"] == f"/api/v1/patients/{patient_id}/record"
    assert record_reads[0]["extra_data"]["deduped_count"] == 2
    assert record_reads[0]["extra_data"]["last_correlation_id"] == "dedupe-read-003"


def test_patient_read_audit_skips_missing_patient(
    client: TestClient,
    auth_headers,
) -> None:
    auth = auth_headers(client)
    missing_id = "99999999-9999-4999-8999-999999999999"

    response = client.get(f"/api/v1/patients/{missing_id}", headers=auth)

    assert response.status_code == 404


def test_solo_lectura_read_audit_uses_readonly_actor(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
) -> None:
    auth = auth_headers(client)
    readonly_auth = auth_headers(client, email="lector@oneepis.local", password="lector")
    patient_id = create_patient_for_permissions(client, auth)

    response = client.get(f"/api/v1/patients/{patient_id}/record", headers=readonly_auth)
    assert response.status_code == 200

    audit_response = client.get(f"/api/v1/patients/{patient_id}/audit-events", headers=auth)
    assert audit_response.status_code == 200
    record_read = next(
        item for item in audit_response.json() if item["action"] == "record.read"
    )
    assert record_read["actor_id"] == "lector@oneepis.local"


def test_audit_events_list_does_not_emit_record_read(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient_for_permissions(client, auth)

    audit_response = client.get(f"/api/v1/patients/{patient_id}/audit-events", headers=auth)
    assert audit_response.status_code == 200
    assert all(item["action"] != "record.read" for item in audit_response.json())

    audit_response = client.get(f"/api/v1/patients/{patient_id}/audit-events", headers=auth)
    assert audit_response.status_code == 200
    assert all(item["action"] != "record.read" for item in audit_response.json())
