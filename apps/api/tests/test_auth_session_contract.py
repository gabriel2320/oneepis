from fastapi.testclient import TestClient


def test_patient_detail_and_record_require_authentication(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
) -> None:
    patient_id = create_patient_for_permissions(client, auth_headers(client))
    client.cookies.clear()

    detail_response = client.get(f"/api/v1/patients/{patient_id}")
    record_response = client.get(f"/api/v1/patients/{patient_id}/record")

    assert detail_response.status_code == 401
    assert record_response.status_code == 401


def test_invalid_bearer_rejects_patient_reads(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
) -> None:
    patient_id = create_patient_for_permissions(client, auth_headers(client))
    client.cookies.clear()
    headers = {"Authorization": "Bearer invalid-token"}

    detail_response = client.get(f"/api/v1/patients/{patient_id}", headers=headers)
    record_response = client.get(f"/api/v1/patients/{patient_id}/record", headers=headers)

    assert detail_response.status_code == 401
    assert record_response.status_code == 401


def test_logout_revokes_bearer_access_to_patient_reads(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient_for_permissions(client, auth)
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "medico@oneepis.local", "password": "medico"},
    )
    token = login_response.json()["access_token"]
    bearer_headers = {"Authorization": f"Bearer {token}"}

    before_record = client.get(
        f"/api/v1/patients/{patient_id}/record",
        headers=bearer_headers,
    )
    before_detail = client.get(
        f"/api/v1/patients/{patient_id}",
        headers=bearer_headers,
    )
    assert before_record.status_code == 200
    assert before_detail.status_code == 200

    logout_response = client.post("/api/v1/auth/logout", headers=bearer_headers)
    assert logout_response.status_code == 200

    after_record = client.get(
        f"/api/v1/patients/{patient_id}/record",
        headers=bearer_headers,
    )
    after_detail = client.get(
        f"/api/v1/patients/{patient_id}",
        headers=bearer_headers,
    )
    assert after_record.status_code == 401
    assert after_detail.status_code == 401


def test_logout_revokes_cookie_access_to_patient_reads(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
) -> None:
    patient_id = create_patient_for_permissions(client, auth_headers(client))
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "medico@oneepis.local", "password": "medico"},
    )
    csrf_token = login_response.cookies["oneepis_csrf"]

    before_record = client.get(f"/api/v1/patients/{patient_id}/record")
    before_detail = client.get(f"/api/v1/patients/{patient_id}")
    assert before_record.status_code == 200
    assert before_detail.status_code == 200

    logout_response = client.post(
        "/api/v1/auth/logout",
        headers={"X-OneEpis-CSRF": csrf_token},
    )
    assert logout_response.status_code == 200

    assert client.get(f"/api/v1/patients/{patient_id}/record").status_code == 401
    assert client.get(f"/api/v1/patients/{patient_id}").status_code == 401


def test_refresh_rotation_invalidates_previous_bearer_on_patient_record(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
) -> None:
    patient_id = create_patient_for_permissions(client, auth_headers(client))
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "medico@oneepis.local", "password": "medico"},
    )
    old_token = login_response.json()["access_token"]
    csrf_token = login_response.cookies["oneepis_csrf"]

    refresh_response = client.post(
        "/api/v1/auth/refresh",
        headers={"X-OneEpis-CSRF": csrf_token},
    )
    assert refresh_response.status_code == 200

    stale_response = client.get(
        f"/api/v1/patients/{patient_id}/record",
        headers={"Authorization": f"Bearer {old_token}"},
    )
    assert stale_response.status_code == 401
