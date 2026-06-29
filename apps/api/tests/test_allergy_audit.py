from __future__ import annotations

from fastapi.testclient import TestClient


def test_allergy_audit_uses_structural_allowlist(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
    audit_events_for_patient,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient_for_permissions(client, auth)

    create_response = client.post(
        f"/api/v1/patients/{patient_id}/allergies",
        headers=auth,
        json={
            "substance": "Alergeno sensible ALR-177",
            "reaction": "Reaccion libre sensible inicial",
            "severity": "moderate",
            "recorded_at": "2026-06-20T10:30:00Z",
        },
    )
    assert create_response.status_code == 201
    allergy_id = create_response.json()["id"]

    update_response = client.patch(
        f"/api/v1/patients/{patient_id}/allergies/{allergy_id}",
        headers=auth,
        json={
            "substance": "Alergeno sensible actualizado",
            "reaction": "Reaccion libre sensible actualizada",
            "severity": "severe",
        },
    )
    assert update_response.status_code == 200

    allergy_events = audit_events_for_patient(patient_id)
    allergy_create = next(
        item for item in allergy_events if item["action"] == "allergy.created"
    )
    assert allergy_create["extra_data"]["after"] == {
        "patient_id": patient_id,
        "recorded_at": "2026-06-20T10:30:00+00:00",
        "severity": "moderate",
        "status": "active",
    }

    allergy_update = next(
        item for item in allergy_events if item["action"] == "allergy.updated"
    )
    assert allergy_update["extra_data"]["fields"] == [
        "reaction",
        "severity",
        "substance",
    ]
    assert allergy_update["extra_data"]["before"] == {"severity": "moderate"}
    assert allergy_update["extra_data"]["after"] == {"severity": "severe"}

    audit_payload = str([allergy_create["extra_data"], allergy_update["extra_data"]])
    assert "Alergeno sensible" not in audit_payload
    assert "Reaccion libre sensible" not in audit_payload
