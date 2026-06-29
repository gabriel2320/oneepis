from fastapi.testclient import TestClient

from oneepis_api.models.clinical_order import ClinicalOrderKind, ClinicalOrderStatus
from oneepis_api.schemas.clinical_order import ClinicalOrderCreate


def test_clinical_order_status_enum_stays_non_executable() -> None:
    assert {status.value for status in ClinicalOrderStatus} == {
        "draft",
        "cancelled",
        "entered_in_error",
    }
    assert {kind.value for kind in ClinicalOrderKind} == {
        "lab",
        "imaging",
        "nursing",
        "other",
    }


def test_clinical_order_create_schema_does_not_expose_status() -> None:
    assert "status" not in ClinicalOrderCreate.model_fields


def test_clinical_order_update_rejects_executable_status(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient_for_permissions(client, auth)
    encounter_id = client.post(
        f"/api/v1/patients/{patient_id}/encounters",
        headers=auth,
        json={
            "type": "ambulatory",
            "status": "in_progress",
            "reason": "Control para guard de orden",
            "started_at": "2026-06-20T09:00:00Z",
        },
    ).json()["id"]
    order_id = client.post(
        f"/api/v1/patients/{patient_id}/clinical-orders",
        headers=auth,
        json={
            "encounter_id": encounter_id,
            "kind": "lab",
            "ordered_at": "2026-06-20T10:00:00Z",
            "title": "Hemograma borrador",
            "order_text": "Solicitar hemograma en borrador.",
        },
    ).json()["id"]

    for forbidden_status in ("signed", "active", "executed", "administered", "dispensed"):
        response = client.patch(
            f"/api/v1/patients/{patient_id}/clinical-orders/{order_id}",
            headers=auth,
            json={"status": forbidden_status},
        )
        assert response.status_code == 422, forbidden_status


def test_clinical_order_create_list_update_cancel_and_audit(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
    audit_events_for_patient,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient_for_permissions(client, auth)
    encounter_response = client.post(
        f"/api/v1/patients/{patient_id}/encounters",
        headers=auth,
        json={
            "type": "ambulatory",
            "status": "in_progress",
            "reason": "Control para orden borrador",
            "started_at": "2026-06-20T09:00:00Z",
        },
    )
    assert encounter_response.status_code == 201
    encounter_id = encounter_response.json()["id"]

    create_response = client.post(
        f"/api/v1/patients/{patient_id}/clinical-orders",
        headers=auth,
        json={
            "encounter_id": encounter_id,
            "kind": "lab",
            "ordered_at": "2026-06-20T10:00:00Z",
            "title": "Hemograma completo",
            "order_text": "Solicitar hemograma completo en borrador.",
            "rationale": "Seguimiento ambulatorio.",
        },
    )
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["patient_id"] == patient_id
    assert created["encounter_id"] == encounter_id
    assert created["status"] == "draft"
    assert created["kind"] == "lab"
    assert created["created_by"] == "medico@oneepis.local"

    list_response = client.get(
        f"/api/v1/patients/{patient_id}/clinical-orders",
        headers=auth,
    )
    assert list_response.status_code == 200
    assert list_response.json()[0]["id"] == created["id"]

    update_response = client.patch(
        f"/api/v1/patients/{patient_id}/clinical-orders/{created['id']}",
        headers=auth,
        json={
            "title": "Hemograma y perfil bioquimico",
            "order_text": "Solicitar hemograma y perfil bioquimico en borrador.",
            "rationale": "Cambio narrativo de seguimiento ambulatorio.",
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["title"] == "Hemograma y perfil bioquimico"

    cancel_response = client.patch(
        f"/api/v1/patients/{patient_id}/clinical-orders/{created['id']}",
        headers=auth,
        json={"status": "cancelled"},
    )
    assert cancel_response.status_code == 200
    assert cancel_response.json()["status"] == "cancelled"

    locked_update_response = client.patch(
        f"/api/v1/patients/{patient_id}/clinical-orders/{created['id']}",
        headers=auth,
        json={"title": "No debe editarse"},
    )
    assert locked_update_response.status_code == 409

    events = audit_events_for_patient(patient_id)
    created_event = next(item for item in events if item["action"] == "clinical_order.created")
    content_event = next(
        item
        for item in events
        if item["action"] == "clinical_order.updated"
        and item["extra_data"]["fields"] == ["order_text", "rationale", "title"]
    )
    cancel_event = next(
        item
        for item in events
        if item["action"] == "clinical_order.updated"
        and item["extra_data"]["after"].get("status") == "cancelled"
    )
    assert "title" not in created_event["extra_data"]["after"]
    assert "order_text" not in created_event["extra_data"]["after"]
    assert "rationale" not in created_event["extra_data"]["after"]
    assert content_event["extra_data"]["before"] == {}
    assert content_event["extra_data"]["after"] == {}
    assert cancel_event["extra_data"]["patient_id"] == patient_id
    assert cancel_event["extra_data"]["encounter_id"] == encounter_id
    assert cancel_event["extra_data"]["before"] == {"status": "draft"}
    assert cancel_event["extra_data"]["after"] == {"status": "cancelled"}
    audit_payload = str(
        [
            created_event["extra_data"],
            content_event["extra_data"],
            cancel_event["extra_data"],
        ]
    )
    assert "Hemograma completo" not in audit_payload
    assert "Solicitar hemograma" not in audit_payload
    assert "Seguimiento ambulatorio" not in audit_payload


def test_clinical_order_requires_patient_encounter(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient_for_permissions(client, auth)
    other_patient_id = create_patient_for_permissions(client, auth)
    encounter_response = client.post(
        f"/api/v1/patients/{other_patient_id}/encounters",
        headers=auth,
        json={
            "type": "ambulatory",
            "status": "in_progress",
            "reason": "Encuentro de otro paciente",
            "started_at": "2026-06-20T09:00:00Z",
        },
    )
    assert encounter_response.status_code == 201
    encounter_id = encounter_response.json()["id"]

    response = client.post(
        f"/api/v1/patients/{patient_id}/clinical-orders",
        headers=auth,
        json={
            "encounter_id": encounter_id,
            "kind": "other",
            "ordered_at": "2026-06-20T10:00:00Z",
            "title": "Orden cruzada",
            "order_text": "No debe crearse.",
        },
    )

    assert response.status_code == 404


def test_clinical_order_status_and_content_cannot_change_together(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient_for_permissions(client, auth)
    encounter_id = client.post(
        f"/api/v1/patients/{patient_id}/encounters",
        headers=auth,
        json={
            "type": "ambulatory",
            "status": "in_progress",
            "reason": "Control",
            "started_at": "2026-06-20T09:00:00Z",
        },
    ).json()["id"]
    created = client.post(
        f"/api/v1/patients/{patient_id}/clinical-orders",
        headers=auth,
        json={
            "encounter_id": encounter_id,
            "kind": "imaging",
            "ordered_at": "2026-06-20T10:00:00Z",
            "title": "Radiografia torax",
            "order_text": "Borrador de imagen.",
        },
    ).json()

    response = client.patch(
        f"/api/v1/patients/{patient_id}/clinical-orders/{created['id']}",
        headers=auth,
        json={"status": "entered_in_error", "title": "Cambio simultaneo"},
    )

    assert response.status_code == 409


def test_readonly_user_cannot_create_clinical_order(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
) -> None:
    patient_id = create_patient_for_permissions(client, auth_headers(client))
    readonly_auth = auth_headers(client, email="lector@oneepis.local", password="lector")
    encounter_id = client.post(
        f"/api/v1/patients/{patient_id}/encounters",
        headers=auth_headers(client),
        json={
            "type": "ambulatory",
            "status": "in_progress",
            "reason": "Control",
            "started_at": "2026-06-20T09:00:00Z",
        },
    ).json()["id"]

    response = client.post(
        f"/api/v1/patients/{patient_id}/clinical-orders",
        headers=readonly_auth,
        json={
            "encounter_id": encounter_id,
            "kind": "lab",
            "ordered_at": "2026-06-20T10:00:00Z",
            "title": "Orden no permitida",
            "order_text": "Lectura solamente.",
        },
    )

    assert response.status_code == 403
