from fastapi.testclient import TestClient


def test_patient_read_endpoints_emit_read_audit_events(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient_for_permissions(client, auth)

    patient_response = client.get(f"/api/v1/patients/{patient_id}", headers=auth)
    assert patient_response.status_code == 200

    record_response = client.get(f"/api/v1/patients/{patient_id}/record", headers=auth)
    assert record_response.status_code == 200

    audit_response = client.get(f"/api/v1/patients/{patient_id}/audit-events", headers=auth)
    assert audit_response.status_code == 200
    actions = [item["action"] for item in audit_response.json()]
    assert actions.count("patient.read") == 1
    assert actions.count("record.read") == 1
    read_events = [item for item in audit_response.json() if item["action"].endswith(".read")]
    assert {item["actor_id"] for item in read_events} == {"medico@oneepis.local"}


def test_patient_read_audit_dedupes_repeated_same_route_reads(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient_for_permissions(client, auth)

    for _ in range(3):
        response = client.get(f"/api/v1/patients/{patient_id}/record", headers=auth)
        assert response.status_code == 200

    audit_response = client.get(f"/api/v1/patients/{patient_id}/audit-events", headers=auth)
    assert audit_response.status_code == 200
    record_reads = [
        item for item in audit_response.json() if item["action"] == "record.read"
    ]
    assert len(record_reads) == 1
    assert record_reads[0]["extra_data"]["deduped_count"] == 2


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
