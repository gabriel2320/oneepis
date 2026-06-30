from fastapi.testclient import TestClient


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
    assert response.json()["detail"] == "Break-glass access is not enabled."


def test_clinical_routes_still_work_without_break_glass_header(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient_for_permissions(client, auth)

    response = client.get(f"/api/v1/patients/{patient_id}/record", headers=auth)

    assert response.status_code == 200
