from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from oneepis_api.core.config import Settings, get_settings
from oneepis_api.main import app
from oneepis_api.services.auth import (
    AuthError,
    authenticate_local_user,
    create_access_token,
    verify_access_token,
)


@pytest.fixture
def client() -> TestClient:
    def override_settings() -> Settings:
        return Settings(auth_secret="test-secret")

    app.dependency_overrides[get_settings] = override_settings
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_login_and_me_return_local_user(client: TestClient) -> None:
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "medico@oneepis.local", "password": "medico"},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    me_response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert me_response.status_code == 200
    assert me_response.json()["email"] == "medico@oneepis.local"
    assert me_response.json()["roles"] == ["medico"]


def test_login_rejects_invalid_password(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "medico@oneepis.local", "password": "wrong"},
    )

    assert response.status_code == 401


def test_token_expiration_is_enforced() -> None:
    settings = Settings(auth_secret="test-secret", auth_token_ttl_minutes=1)
    user = authenticate_local_user(settings, "medico@oneepis.local", "medico")
    assert user is not None
    token, _expires_at = create_access_token(
        settings,
        user,
        now=datetime(2026, 6, 20, 12, 0, tzinfo=UTC),
    )

    with pytest.raises(AuthError):
        verify_access_token(
            settings,
            token,
            now=datetime(2026, 6, 20, 12, 2, tzinfo=UTC) + timedelta(seconds=1),
        )
