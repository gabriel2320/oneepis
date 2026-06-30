from fastapi.testclient import TestClient
from sqlalchemy import select

from oneepis_api.db.session import get_session
from oneepis_api.main import app
from oneepis_api.models.audit import AuditEvent


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


def test_patient_index_read_audit_is_minimized(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
) -> None:
    auth = auth_headers(client)
    create_patient_for_permissions(client, auth)

    response = client.get(
        "/api/v1/patients?search=Permisos&limit=10&offset=0",
        headers={**auth, "X-OneEpis-Correlation-ID": "read-patient-index-001"},
    )

    assert response.status_code == 200
    audit_event = _latest_audit_event("patient_index.read")
    assert audit_event.entity_type == "patient_index"
    assert audit_event.entity_id is None
    assert audit_event.actor_id == "medico@oneepis.local"
    assert audit_event.correlation_id == "read-patient-index-001"
    assert audit_event.request_method == "GET"
    assert audit_event.request_path == "/api/v1/patients"
    assert audit_event.extra_data == {
        "search_present": True,
        "limit": 10,
        "offset": 0,
        "result_count": 1,
    }


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

    _assert_public_read_audit_events(client, audit_auth, patient_id, reads)


def test_patient_vitals_risks_and_orders_emit_read_audit(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
) -> None:
    auth = auth_headers(client)
    audit_auth = auth_headers(client, email="admin@oneepis.local", password="admin")
    patient_id = create_patient_for_permissions(client, auth)
    vital_response = client.post(
        f"/api/v1/patients/{patient_id}/vital-signs",
        headers=auth,
        json={
            "measured_at": "2026-06-20T12:00:00Z",
            "systolic_bp": 118,
            "diastolic_bp": 72,
            "heart_rate_bpm": 78,
        },
    )
    assert vital_response.status_code == 201
    vital_id = vital_response.json()["id"]
    risk_response = client.post(
        f"/api/v1/patients/{patient_id}/clinical-risks",
        headers=auth,
        json={
            "risk_type": "fall",
            "severity": "moderate",
            "source_kind": "manual",
            "reason": "Riesgo para lectura auditada.",
        },
    )
    assert risk_response.status_code == 201
    risk_id = risk_response.json()["id"]
    encounter_response = client.post(
        f"/api/v1/patients/{patient_id}/encounters",
        headers=auth,
        json={
            "type": "ambulatory",
            "status": "in_progress",
            "reason": "Control para orden auditada",
            "started_at": "2026-06-20T09:00:00Z",
        },
    )
    assert encounter_response.status_code == 201
    order_response = client.post(
        f"/api/v1/patients/{patient_id}/clinical-orders",
        headers=auth,
        json={
            "encounter_id": encounter_response.json()["id"],
            "kind": "lab",
            "ordered_at": "2026-06-20T10:00:00Z",
            "title": "Orden borrador auditada",
            "order_text": "No es orden ejecutable.",
        },
    )
    assert order_response.status_code == 201
    reads = [
        (
            "vital_signs.read",
            f"/api/v1/patients/{patient_id}/vital-signs",
            "read-vitals-001",
        ),
        (
            "vital_sign.read",
            f"/api/v1/patients/{patient_id}/vital-signs/{vital_id}",
            "read-vital-001",
        ),
        (
            "clinical_risks.read",
            f"/api/v1/patients/{patient_id}/clinical-risks",
            "read-risks-001",
        ),
        (
            "clinical_risk.read",
            f"/api/v1/patients/{patient_id}/clinical-risks/{risk_id}",
            "read-risk-001",
        ),
        (
            "clinical_orders.read",
            f"/api/v1/patients/{patient_id}/clinical-orders",
            "read-orders-001",
        ),
    ]

    for _, path, correlation_id in reads:
        response = client.get(
            path,
            headers={**auth, "X-OneEpis-Correlation-ID": correlation_id},
        )
        assert response.status_code == 200

    _assert_public_read_audit_events(client, audit_auth, patient_id, reads)


def test_patient_medications_allergies_and_problems_emit_read_audit(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
) -> None:
    auth = auth_headers(client)
    audit_auth = auth_headers(client, email="admin@oneepis.local", password="admin")
    patient_id = create_patient_for_permissions(client, auth)
    medication_response = client.post(
        f"/api/v1/patients/{patient_id}/medications",
        headers=auth,
        json={
            "name": "Medicamento para lectura auditada",
            "dose": "500 mg",
            "route": "oral",
            "frequency": "cada 12 horas",
        },
    )
    assert medication_response.status_code == 201
    medication_id = medication_response.json()["id"]
    allergy_response = client.post(
        f"/api/v1/patients/{patient_id}/allergies",
        headers=auth,
        json={
            "substance": "Alergeno auditado",
            "reaction": "Exantema",
            "recorded_at": "2026-06-20T12:00:00Z",
        },
    )
    assert allergy_response.status_code == 201
    allergy_id = allergy_response.json()["id"]
    problem_response = client.post(
        f"/api/v1/patients/{patient_id}/problems",
        headers=auth,
        json={
            "title": "Problema activo auditado",
            "status": "active",
        },
    )
    assert problem_response.status_code == 201
    problem_id = problem_response.json()["id"]
    reads = [
        (
            "medications.read",
            f"/api/v1/patients/{patient_id}/medications",
            "read-medications-001",
        ),
        (
            "medication.read",
            f"/api/v1/patients/{patient_id}/medications/{medication_id}",
            "read-medication-001",
        ),
        (
            "medication_drafting_context.read",
            f"/api/v1/patients/{patient_id}/medication-drafting-context",
            "read-medication-context-001",
        ),
        (
            "allergies.read",
            f"/api/v1/patients/{patient_id}/allergies",
            "read-allergies-001",
        ),
        (
            "allergy.read",
            f"/api/v1/patients/{patient_id}/allergies/{allergy_id}",
            "read-allergy-001",
        ),
        (
            "problems.read",
            f"/api/v1/patients/{patient_id}/problems",
            "read-problems-001",
        ),
        (
            "problem.read",
            f"/api/v1/patients/{patient_id}/problems/{problem_id}",
            "read-problem-001",
        ),
    ]

    for _, path, correlation_id in reads:
        response = client.get(
            path,
            headers={**auth, "X-OneEpis-Correlation-ID": correlation_id},
        )
        assert response.status_code == 200

    _assert_public_read_audit_events(client, audit_auth, patient_id, reads)


def test_patient_labs_encounters_and_hospital_drafts_emit_read_audit(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
) -> None:
    auth = auth_headers(client)
    audit_auth = auth_headers(client, email="admin@oneepis.local", password="admin")
    patient_id = create_patient_for_permissions(client, auth)
    encounter_response = client.post(
        f"/api/v1/patients/{patient_id}/encounters",
        headers=auth,
        json={
            "type": "hospitalization",
            "status": "in_progress",
            "reason": "Ingreso para lecturas auditadas",
            "started_at": "2026-06-20T07:00:00Z",
        },
    )
    assert encounter_response.status_code == 201
    encounter_id = encounter_response.json()["id"]
    panel_response = client.post(
        f"/api/v1/patients/{patient_id}/lab-panels",
        headers=auth,
        json={
            "occurred_at": "2026-06-20T09:00:00Z",
            "panel_name": "Panel para lectura auditada",
            "results": [
                {
                    "code": "hb",
                    "name": "Hemoglobina",
                    "value": "13.4",
                    "numeric_value": "13.4",
                    "unit": "g/dL",
                }
            ],
        },
    )
    assert panel_response.status_code == 201
    panel = panel_response.json()
    daily_sheet_response = client.post(
        f"/api/v1/hospitalization/patients/{patient_id}/daily-sheets",
        headers=auth,
        json={
            "sheet_date": "2026-06-20",
            "clinical_summary": "Borrador hospitalario para lectura auditada.",
        },
    )
    assert daily_sheet_response.status_code == 201
    indication_response = client.post(
        f"/api/v1/hospitalization/patients/{patient_id}/indications",
        headers=auth,
        json={
            "indicated_at": "2026-06-20T10:00:00Z",
            "title": "Indicacion draft auditada",
            "indication_text": "Borrador no ejecutable.",
        },
    )
    assert indication_response.status_code == 201
    reads = [
        (
            "lab_panels.read",
            f"/api/v1/patients/{patient_id}/lab-panels",
            "read-lab-panels-001",
        ),
        (
            "lab_panel.read",
            f"/api/v1/patients/{patient_id}/lab-panels/{panel['id']}",
            "read-lab-panel-001",
        ),
        (
            "lab_result.read",
            f"/api/v1/patients/{patient_id}/lab-panels/{panel['id']}/results/"
            f"{panel['results'][0]['id']}",
            "read-lab-result-001",
        ),
        (
            "encounters.read",
            f"/api/v1/patients/{patient_id}/encounters",
            "read-encounters-001",
        ),
        (
            "encounter.read",
            f"/api/v1/patients/{patient_id}/encounters/{encounter_id}",
            "read-encounter-001",
        ),
        (
            "hospital_daily_sheets.read",
            f"/api/v1/hospitalization/patients/{patient_id}/daily-sheets",
            "read-hospital-daily-sheets-001",
        ),
        (
            "hospital_indications.read",
            f"/api/v1/hospitalization/patients/{patient_id}/indications",
            "read-hospital-indications-001",
        ),
    ]

    for _, path, correlation_id in reads:
        response = client.get(
            path,
            headers={**auth, "X-OneEpis-Correlation-ID": correlation_id},
        )
        assert response.status_code == 200

    _assert_public_read_audit_events(client, audit_auth, patient_id, reads)


def test_patient_appointments_emit_read_audit(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
) -> None:
    auth = auth_headers(client)
    audit_auth = auth_headers(client, email="admin@oneepis.local", password="admin")
    patient_id = create_patient_for_permissions(client, auth)
    appointment_response = client.post(
        f"/api/v1/patients/{patient_id}/appointments",
        headers=auth,
        json={
            "starts_at": "2026-06-20T12:00:00Z",
            "ends_at": "2026-06-20T12:30:00Z",
            "reason": "Control auditado",
            "notes": "Nota clinica que no debe duplicarse en metadata.",
        },
    )
    assert appointment_response.status_code == 201
    appointment_id = appointment_response.json()["id"]

    reads = [
        (
            "appointments.read",
            f"/api/v1/patients/{patient_id}/appointments",
            "read-appointments-001",
        ),
        (
            "appointment.read",
            f"/api/v1/patients/{patient_id}/appointments/{appointment_id}",
            "read-appointment-001",
        ),
    ]

    for _, path, correlation_id in reads:
        response = client.get(
            path,
            headers={**auth, "X-OneEpis-Correlation-ID": correlation_id},
        )
        assert response.status_code == 200

    _assert_public_read_audit_events(client, audit_auth, patient_id, reads)


def test_appointment_index_read_audit_is_minimized(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient_for_permissions(client, auth)
    appointment_response = client.post(
        f"/api/v1/patients/{patient_id}/appointments",
        headers=auth,
        json={
            "starts_at": "2026-06-20T12:00:00Z",
            "ends_at": "2026-06-20T12:30:00Z",
            "reason": "Motivo sensible",
            "notes": "Nota sensible",
        },
    )
    assert appointment_response.status_code == 201

    response = client.get(
        "/api/v1/appointments?date_from=2026-06-20T00:00:00Z&limit=10&offset=0",
        headers={**auth, "X-OneEpis-Correlation-ID": "read-appointments-index-001"},
    )

    assert response.status_code == 200
    audit_event = _latest_audit_event("appointments_index.read")
    assert audit_event.entity_type == "appointment_index"
    assert audit_event.entity_id is None
    assert audit_event.actor_id == "medico@oneepis.local"
    assert audit_event.correlation_id == "read-appointments-index-001"
    assert audit_event.extra_data == {
        "date_from_present": True,
        "date_to_present": False,
        "limit": 10,
        "offset": 0,
        "result_count": 1,
    }


def test_patient_assistant_and_context_reads_emit_read_audit(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
) -> None:
    auth = auth_headers(client)
    audit_auth = auth_headers(client, email="admin@oneepis.local", password="admin")
    patient_id = create_patient_for_permissions(client, auth)
    event_response = client.post(
        f"/api/v1/patients/{patient_id}/clinical-events",
        headers=auth,
        json={
            "event_type": "clinical_note",
            "occurred_at": "2026-06-20T12:00:00Z",
            "summary": "Lectura assistant auditada",
        },
    )
    assert event_response.status_code == 201
    vital_response = client.post(
        f"/api/v1/patients/{patient_id}/vital-signs",
        headers=auth,
        json={"measured_at": "2026-06-20T12:05:00Z", "heart_rate_bpm": 72},
    )
    assert vital_response.status_code == 201
    reads = [
        (
            "patient_context.read",
            f"/api/v1/patients/{patient_id}/context",
            "read-patient-context-001",
        ),
        (
            "assistant_timeline.read",
            f"/api/v1/patients/{patient_id}/assistant/timeline",
            "read-assistant-timeline-001",
        ),
        (
            "assistant_search.read",
            f"/api/v1/patients/{patient_id}/assistant/search",
            "read-assistant-search-001",
        ),
        (
            "assistant_chart.read",
            f"/api/v1/patients/{patient_id}/assistant/chart",
            "read-assistant-chart-001",
            "POST",
        ),
    ]

    context_response = client.get(
        reads[0][1],
        headers={**auth, "X-OneEpis-Correlation-ID": reads[0][2]},
    )
    timeline_response = client.get(
        reads[1][1],
        headers={**auth, "X-OneEpis-Correlation-ID": reads[1][2]},
    )
    search_response = client.get(
        f"{reads[2][1]}?q=assistant",
        headers={**auth, "X-OneEpis-Correlation-ID": reads[2][2]},
    )
    chart_response = client.post(
        reads[3][1],
        headers={**auth, "X-OneEpis-Correlation-ID": reads[3][2]},
        json={"series": ["heart_rate_bpm"]},
    )

    assert context_response.status_code == 200
    assert timeline_response.status_code == 200
    assert search_response.status_code == 200
    assert chart_response.status_code == 200
    _assert_public_read_audit_events(client, audit_auth, patient_id, reads)


def test_patient_audit_events_require_audit_read_access(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
    audit_events_for_patient,
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
    raw_events = audit_events_for_patient(patient_id)
    audit_read = next(item for item in raw_events if item["action"] == "patient_audit.read")
    assert audit_read["actor_id"] == "admin@oneepis.local"
    assert audit_read["entity_type"] == "patient"
    assert audit_read["entity_id"] == patient_id
    assert audit_read["request_method"] == "GET"
    assert audit_read["request_path"] == f"/api/v1/patients/{patient_id}/audit-events"


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


def _latest_audit_event(action: str) -> AuditEvent:
    override_session = app.dependency_overrides[get_session]
    session_iterator = override_session()
    session = next(session_iterator)
    try:
        return session.scalars(
            select(AuditEvent)
            .where(AuditEvent.action == action)
            .order_by(AuditEvent.created_at.desc())
            .limit(1)
        ).one()
    finally:
        session_iterator.close()


def _assert_public_read_audit_events(
    client: TestClient,
    audit_auth: dict[str, str],
    patient_id: str,
    reads: list[tuple[str, str, str] | tuple[str, str, str, str]],
) -> None:
    audit_response = client.get(
        f"/api/v1/patients/{patient_id}/audit-events",
        headers=audit_auth,
    )
    assert audit_response.status_code == 200
    audit_events = audit_response.json()
    for read in reads:
        action, path, correlation_id, *method = read
        read_event = next(item for item in audit_events if item["action"] == action)
        assert read_event["actor_id"] == "medico@oneepis.local"
        assert read_event["correlation_id"] == correlation_id
        assert read_event["request_method"] == (method[0] if method else "GET")
        assert read_event["request_path"] == path
        assert "extra_data" not in read_event

    audit_response = client.get(
        f"/api/v1/patients/{patient_id}/audit-events",
        headers=audit_auth,
    )
    assert audit_response.status_code == 200
    assert all(item["action"] != "record.read" for item in audit_response.json())
