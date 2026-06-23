from fastapi.testclient import TestClient
from patient_ai_helpers import audit_events, create_patient


def test_lab_panel_create_read_patch_and_audit(
    client: TestClient,
    auth_headers,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient(client, auth, first_name="Lab", last_name="Audit")
    encounter = _create_encounter(client, auth, patient_id)

    response = client.post(
        f"/api/v1/patients/{patient_id}/lab-panels",
        headers=auth,
        json={
            "encounter_id": encounter["id"],
            "occurred_at": "2026-06-20T09:00:00Z",
            "panel_name": "Perfil renal",
            "summary": "Control inicial",
            "results": [
                {
                    "code": "creatinina",
                    "name": "Creatinina",
                    "value": "1.10",
                    "numeric_value": "1.10",
                    "unit": "mg/dL",
                    "reference_range": "0.7-1.3",
                    "flag": "normal",
                },
                {
                    "code": "urea",
                    "name": "Urea",
                    "value": "34",
                    "numeric_value": "34",
                    "unit": "mg/dL",
                },
            ],
        },
    )

    assert response.status_code == 201
    panel = response.json()
    assert panel["created_by"] == "medico@oneepis.local"
    assert panel["patient_id"] == patient_id
    assert len(panel["results"]) == 2
    assert float(panel["results"][0]["numeric_value"]) == 1.1

    readonly_auth = auth_headers(client, email="lector@oneepis.local", password="lector")
    list_response = client.get(f"/api/v1/patients/{patient_id}/lab-panels", headers=readonly_auth)
    result_response = client.get(
        f"/api/v1/patients/{patient_id}/lab-panels/{panel['id']}/results/"
        f"{panel['results'][0]['id']}",
        headers=readonly_auth,
    )

    assert list_response.status_code == 200
    assert list_response.json()[0]["id"] == panel["id"]
    assert result_response.status_code == 200
    assert result_response.json()["name"] == "Creatinina"

    panel_patch = client.patch(
        f"/api/v1/patients/{patient_id}/lab-panels/{panel['id']}",
        headers=auth,
        json={"summary": "Control corregido"},
    )
    result_patch = client.patch(
        f"/api/v1/patients/{patient_id}/lab-panels/{panel['id']}/results/"
        f"{panel['results'][0]['id']}",
        headers=auth,
        json={"numeric_value": "1.20", "status": "entered_in_error"},
    )

    assert panel_patch.status_code == 200
    assert panel_patch.json()["summary"] == "Control corregido"
    assert result_patch.status_code == 200
    assert result_patch.json()["status"] == "entered_in_error"

    events = audit_events(client, auth, patient_id)
    created = next(item for item in events if item["action"] == "lab_panel.created")
    panel_updated = next(item for item in events if item["action"] == "lab_panel.updated")
    result_updated = next(item for item in events if item["action"] == "lab_result.updated")
    assert created["extra_data"]["result_count"] == 2
    assert created["extra_data"]["after"]["panel_name"] == "Perfil renal"
    assert panel_updated["extra_data"]["before"] == {"summary": "Control inicial"}
    assert panel_updated["extra_data"]["after"] == {"summary": "Control corregido"}
    assert result_updated["extra_data"]["before"]["status"] == "active"
    assert result_updated["extra_data"]["after"]["status"] == "entered_in_error"


def test_lab_panel_permissions_and_ownership(
    client: TestClient,
    auth_headers,
) -> None:
    auth = auth_headers(client)
    first_patient = create_patient(client, auth, first_name="Lab", last_name="Owner")
    second_patient = create_patient(client, auth, first_name="Lab", last_name="Other")
    second_encounter = _create_encounter(client, auth, second_patient)
    panel = _create_lab_panel(client, auth, first_patient)

    readonly_auth = auth_headers(client, email="lector@oneepis.local", password="lector")
    readonly_create = client.post(
        f"/api/v1/patients/{first_patient}/lab-panels",
        headers=readonly_auth,
        json=_lab_panel_payload(),
    )
    readonly_patch = client.patch(
        f"/api/v1/patients/{first_patient}/lab-panels/{panel['id']}",
        headers=readonly_auth,
        json={"summary": "No permitido"},
    )
    nursing_auth = auth_headers(client, email="enfermeria@oneepis.local", password="enfermeria")
    nursing_create = client.post(
        f"/api/v1/patients/{first_patient}/lab-panels",
        headers=nursing_auth,
        json=_lab_panel_payload(panel_name="Panel enfermeria"),
    )
    wrong_encounter = client.post(
        f"/api/v1/patients/{first_patient}/lab-panels",
        headers=auth,
        json=_lab_panel_payload(encounter_id=second_encounter["id"]),
    )
    wrong_patient_panel = client.get(
        f"/api/v1/patients/{second_patient}/lab-panels/{panel['id']}",
        headers=auth,
    )
    wrong_patient_result = client.get(
        f"/api/v1/patients/{second_patient}/lab-panels/{panel['id']}/results/"
        f"{panel['results'][0]['id']}",
        headers=auth,
    )

    assert readonly_create.status_code == 403
    assert readonly_patch.status_code == 403
    assert nursing_create.status_code == 201
    assert wrong_encounter.status_code == 404
    assert wrong_patient_panel.status_code == 404
    assert wrong_patient_result.status_code == 404


def test_lab_panel_result_requires_panel_ownership_and_has_no_delete(
    client: TestClient,
    auth_headers,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient(client, auth, first_name="Lab", last_name="NoDelete")
    first_panel = _create_lab_panel(client, auth, patient_id, panel_name="Primer panel")
    second_panel = _create_lab_panel(client, auth, patient_id, panel_name="Segundo panel")

    wrong_panel_result = client.get(
        f"/api/v1/patients/{patient_id}/lab-panels/{second_panel['id']}/results/"
        f"{first_panel['results'][0]['id']}",
        headers=auth,
    )
    delete_panel = client.delete(
        f"/api/v1/patients/{patient_id}/lab-panels/{first_panel['id']}",
        headers=auth,
    )
    delete_result = client.delete(
        f"/api/v1/patients/{patient_id}/lab-panels/{first_panel['id']}/results/"
        f"{first_panel['results'][0]['id']}",
        headers=auth,
    )

    assert wrong_panel_result.status_code == 404
    assert delete_panel.status_code == 405
    assert delete_result.status_code == 405


def _create_encounter(client: TestClient, auth: dict[str, str], patient_id: str) -> dict:
    response = client.post(
        f"/api/v1/patients/{patient_id}/encounters",
        headers=auth,
        json={
            "type": "ambulatory",
            "reason": "Control laboratorio",
            "started_at": "2026-06-20T08:00:00Z",
        },
    )
    assert response.status_code == 201
    return response.json()


def _create_lab_panel(
    client: TestClient,
    auth: dict[str, str],
    patient_id: str,
    *,
    panel_name: str = "Hemograma",
) -> dict:
    response = client.post(
        f"/api/v1/patients/{patient_id}/lab-panels",
        headers=auth,
        json=_lab_panel_payload(panel_name=panel_name),
    )
    assert response.status_code == 201
    return response.json()


def _lab_panel_payload(
    *,
    panel_name: str = "Hemograma",
    encounter_id: str | None = None,
) -> dict:
    return {
        "encounter_id": encounter_id,
        "occurred_at": "2026-06-20T09:00:00Z",
        "panel_name": panel_name,
        "results": [
            {
                "code": "hb",
                "name": "Hemoglobina",
                "value": "13.4",
                "numeric_value": "13.4",
                "unit": "g/dL",
            }
        ],
    }
