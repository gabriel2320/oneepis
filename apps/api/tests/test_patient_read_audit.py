from fastapi.testclient import TestClient


def test_patient_read_endpoints_emit_read_audit_events(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
) -> None:
    auth = auth_headers(client)
    audit_auth = auth_headers(client, email="admin@oneepis.local", password="admin")
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

    audit_response = client.get(
        f"/api/v1/patients/{patient_id}/audit-events",
        headers=audit_auth,
    )
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


def test_patient_clinical_entries_events_and_timeline_emit_read_audit(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
) -> None:
    auth = auth_headers(client)
    audit_auth = auth_headers(client, email="admin@oneepis.local", password="admin")
    patient_id = create_patient_for_permissions(client, auth)
    entry_response = client.post(
        f"/api/v1/patients/{patient_id}/clinical-entries",
        headers=auth,
        json={
            "kind": "progress",
            "occurred_at": "2026-06-20T12:00:00Z",
            "title": "Evolucion para lectura auditada",
        },
    )
    assert entry_response.status_code == 201
    entry_id = entry_response.json()["id"]
    event_response = client.post(
        f"/api/v1/patients/{patient_id}/clinical-events",
        headers=auth,
        json={
            "event_type": "clinical_note",
            "occurred_at": "2026-06-20T12:05:00Z",
            "summary": "Evento para lectura auditada",
        },
    )
    assert event_response.status_code == 201
    event_id = event_response.json()["id"]
    reads = [
        (
            "clinical_entries.read",
            f"/api/v1/patients/{patient_id}/clinical-entries",
            "read-entries-001",
        ),
        (
            "clinical_entry.read",
            f"/api/v1/patients/{patient_id}/clinical-entries/{entry_id}",
            "read-entry-001",
        ),
        (
            "clinical_events.read",
            f"/api/v1/patients/{patient_id}/clinical-events",
            "read-events-001",
        ),
        (
            "clinical_event.read",
            f"/api/v1/patients/{patient_id}/clinical-events/{event_id}",
            "read-event-001",
        ),
        (
            "timeline.read",
            f"/api/v1/patients/{patient_id}/timeline",
            "read-timeline-001",
        ),
    ]

    for _, path, correlation_id in reads:
        response = client.get(
            path,
            headers={**auth, "X-OneEpis-Correlation-ID": correlation_id},
        )
        assert response.status_code == 200

    audit_response = client.get(
        f"/api/v1/patients/{patient_id}/audit-events",
        headers=audit_auth,
    )
    assert audit_response.status_code == 200
    audit_events = audit_response.json()
    for action, path, correlation_id in reads:
        read_event = next(item for item in audit_events if item["action"] == action)
        assert read_event["actor_id"] == "medico@oneepis.local"
        assert read_event["correlation_id"] == correlation_id
        assert read_event["request_method"] == "GET"
        assert read_event["request_path"] == path
        assert "extra_data" not in read_event


def test_patient_audit_events_require_audit_read_access(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
) -> None:
    auth = auth_headers(client)
    readonly_auth = auth_headers(client, email="lector@oneepis.local", password="lector")
    audit_auth = auth_headers(client, email="admin@oneepis.local", password="admin")
    patient_id = create_patient_for_permissions(client, auth)

    medico_response = client.get(f"/api/v1/patients/{patient_id}/audit-events", headers=auth)
    readonly_response = client.get(
        f"/api/v1/patients/{patient_id}/audit-events",
        headers=readonly_auth,
    )
    admin_response = client.get(
        f"/api/v1/patients/{patient_id}/audit-events",
        headers=audit_auth,
    )

    assert medico_response.status_code == 403
    assert readonly_response.status_code == 403
    assert admin_response.status_code == 200


def test_patient_read_audit_appends_repeated_same_route_reads(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
    audit_events_for_patient,
) -> None:
    auth = auth_headers(client)
    audit_auth = auth_headers(client, email="admin@oneepis.local", password="admin")
    patient_id = create_patient_for_permissions(client, auth)

    for index in range(3):
        response = client.get(
            f"/api/v1/patients/{patient_id}/record",
            headers={**auth, "X-OneEpis-Correlation-ID": f"dedupe-read-00{index + 1}"},
        )
        assert response.status_code == 200

    audit_response = client.get(
        f"/api/v1/patients/{patient_id}/audit-events",
        headers=audit_auth,
    )
    assert audit_response.status_code == 200
    audit_events = audit_response.json()
    record_reads = [item for item in audit_events if item["action"] == "record.read"]
    deduped_reads = [
        item for item in audit_events if item["action"] == "record.read_deduped"
    ]
    assert len(record_reads) == 1
    assert len(deduped_reads) == 2
    assert record_reads[0]["correlation_id"] == "dedupe-read-001"
    assert record_reads[0]["request_method"] == "GET"
    assert record_reads[0]["request_path"] == f"/api/v1/patients/{patient_id}/record"
    assert "extra_data" not in record_reads[0]
    raw_events = audit_events_for_patient(patient_id)
    raw_record_read = next(item for item in raw_events if item["action"] == "record.read")
    raw_deduped_reads = [
        item for item in raw_events if item["action"] == "record.read_deduped"
    ]
    assert "deduped_count" not in raw_record_read["extra_data"]
    assert "last_correlation_id" not in raw_record_read["extra_data"]
    assert {item["correlation_id"] for item in raw_deduped_reads} == {
        "dedupe-read-002",
        "dedupe-read-003",
    }
    assert {
        item["extra_data"]["deduped_from_audit_event_id"] for item in raw_deduped_reads
    } == {raw_record_read["id"]}
    assert {
        item["extra_data"]["deduped_from_correlation_id"] for item in raw_deduped_reads
    } == {"dedupe-read-001"}


def test_patient_audit_events_filter_by_patient_before_limit(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
) -> None:
    auth = auth_headers(client)
    audit_auth = auth_headers(client, email="admin@oneepis.local", password="admin")
    patient_id = create_patient_for_permissions(client, auth)
    other_patient_id = create_patient_for_permissions(client, auth)

    target_response = client.patch(
        f"/api/v1/patients/{patient_id}",
        headers={**auth, "X-OneEpis-Correlation-ID": "target-patient-update"},
        json={"last_name": "Paciente Auditado"},
    )
    assert target_response.status_code == 200

    for index in range(9):
        other_response = client.patch(
            f"/api/v1/patients/{other_patient_id}",
            headers={**auth, "X-OneEpis-Correlation-ID": f"other-patient-update-{index}"},
            json={"last_name": f"Paciente Externo {index}"},
        )
        assert other_response.status_code == 200

    audit_response = client.get(
        f"/api/v1/patients/{patient_id}/audit-events?limit=2",
        headers=audit_auth,
    )
    assert audit_response.status_code == 200
    audit_events = audit_response.json()
    assert "target-patient-update" in [item["correlation_id"] for item in audit_events]
    assert {item["entity_id"] for item in audit_events} == {patient_id}


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
    audit_auth = auth_headers(client, email="admin@oneepis.local", password="admin")
    readonly_auth = auth_headers(client, email="lector@oneepis.local", password="lector")
    patient_id = create_patient_for_permissions(client, auth)

    response = client.get(f"/api/v1/patients/{patient_id}/record", headers=readonly_auth)
    assert response.status_code == 200

    audit_response = client.get(
        f"/api/v1/patients/{patient_id}/audit-events",
        headers=audit_auth,
    )
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
    audit_auth = auth_headers(client, email="admin@oneepis.local", password="admin")
    patient_id = create_patient_for_permissions(client, auth)

    audit_response = client.get(
        f"/api/v1/patients/{patient_id}/audit-events",
        headers=audit_auth,
    )
    assert audit_response.status_code == 200
    assert all(item["action"] != "record.read" for item in audit_response.json())

    audit_response = client.get(
        f"/api/v1/patients/{patient_id}/audit-events",
        headers=audit_auth,
    )
    assert audit_response.status_code == 200
    assert all(item["action"] != "record.read" for item in audit_response.json())
