from fastapi.testclient import TestClient
from patient_ai_helpers import audit_events, create_patient


def test_clinical_risk_create_read_patch_and_audit(
    client: TestClient,
    auth_headers,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient(client, auth, first_name="Riesgo", last_name="Audit")
    vital = _create_vital(client, auth, patient_id)

    response = client.post(
        f"/api/v1/patients/{patient_id}/clinical-risks",
        headers=auth,
        json={
            "risk_type": "fall",
            "severity": "high",
            "source_kind": "vital_sign",
            "source_ref": vital["id"],
            "reason": "Marcha inestable observada en control.",
            "human_action": "Reevaluar en ronda.",
        },
    )

    assert response.status_code == 201
    risk = response.json()
    assert risk["patient_id"] == patient_id
    assert risk["created_by"] == "medico@oneepis.local"
    assert risk["source_kind"] == "vital_sign"

    readonly_auth = auth_headers(client, email="lector@oneepis.local", password="lector")
    list_response = client.get(
        f"/api/v1/patients/{patient_id}/clinical-risks?status=active",
        headers=readonly_auth,
    )
    get_response = client.get(
        f"/api/v1/patients/{patient_id}/clinical-risks/{risk['id']}",
        headers=readonly_auth,
    )

    assert list_response.status_code == 200
    assert list_response.json()[0]["id"] == risk["id"]
    assert get_response.status_code == 200
    assert get_response.json()["reason"] == "Marcha inestable observada en control."

    patch_response = client.patch(
        f"/api/v1/patients/{patient_id}/clinical-risks/{risk['id']}",
        headers=auth,
        json={"severity": "moderate", "status": "resolved"},
    )

    assert patch_response.status_code == 200
    assert patch_response.json()["severity"] == "moderate"
    assert patch_response.json()["status"] == "resolved"

    events = audit_events(client, auth, patient_id)
    created = next(item for item in events if item["action"] == "clinical_risk.created")
    updated = next(item for item in events if item["action"] == "clinical_risk.updated")
    assert created["extra_data"]["risk_type"] == "fall"
    assert created["extra_data"]["after"]["source_ref"] == vital["id"]
    assert updated["extra_data"]["before"] == {"severity": "high", "status": "active"}
    assert updated["extra_data"]["after"] == {"severity": "moderate", "status": "resolved"}


def test_clinical_risk_permissions_ownership_and_no_delete(
    client: TestClient,
    auth_headers,
) -> None:
    auth = auth_headers(client)
    first_patient = create_patient(client, auth, first_name="Riesgo", last_name="Uno")
    second_patient = create_patient(client, auth, first_name="Riesgo", last_name="Dos")
    second_vital = _create_vital(client, auth, second_patient)
    risk = _create_risk(client, auth, first_patient)

    readonly_auth = auth_headers(client, email="lector@oneepis.local", password="lector")
    readonly_create = client.post(
        f"/api/v1/patients/{first_patient}/clinical-risks",
        headers=readonly_auth,
        json=_risk_payload(),
    )
    nursing_auth = auth_headers(client, email="enfermeria@oneepis.local", password="enfermeria")
    nursing_create = client.post(
        f"/api/v1/patients/{first_patient}/clinical-risks",
        headers=nursing_auth,
        json=_risk_payload(reason="Observado por enfermeria."),
    )
    wrong_patient_get = client.get(
        f"/api/v1/patients/{second_patient}/clinical-risks/{risk['id']}",
        headers=auth,
    )
    wrong_source = client.post(
        f"/api/v1/patients/{first_patient}/clinical-risks",
        headers=auth,
        json=_risk_payload(source_kind="vital_sign", source_ref=second_vital["id"]),
    )
    delete_response = client.delete(
        f"/api/v1/patients/{first_patient}/clinical-risks/{risk['id']}",
        headers=auth,
    )

    assert readonly_create.status_code == 403
    assert nursing_create.status_code == 201
    assert wrong_patient_get.status_code == 404
    assert wrong_source.status_code == 404
    assert delete_response.status_code == 405


def _create_vital(client: TestClient, auth: dict[str, str], patient_id: str) -> dict:
    response = client.post(
        f"/api/v1/patients/{patient_id}/vital-signs",
        headers=auth,
        json={
            "measured_at": "2026-06-20T12:00:00Z",
            "systolic_bp": 110,
            "diastolic_bp": 70,
            "heart_rate_bpm": 82,
        },
    )
    assert response.status_code == 201
    return response.json()


def _create_risk(client: TestClient, auth: dict[str, str], patient_id: str) -> dict:
    response = client.post(
        f"/api/v1/patients/{patient_id}/clinical-risks",
        headers=auth,
        json=_risk_payload(),
    )
    assert response.status_code == 201
    return response.json()


def _risk_payload(
    *,
    reason: str = "Riesgo manual identificado.",
    source_kind: str = "manual",
    source_ref: str | None = None,
) -> dict:
    return {
        "risk_type": "fall",
        "severity": "unknown",
        "source_kind": source_kind,
        "source_ref": source_ref,
        "reason": reason,
        "human_action": "Revisar medidas preventivas.",
    }
