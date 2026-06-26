from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from oneepis_api.core.config import Settings, get_settings
from oneepis_api.db.base import Base
from oneepis_api.db.session import get_session
from oneepis_api.main import app
from oneepis_api.models import auth_security as _auth_security_models  # noqa: F401
from oneepis_api.models import patient as _patient_models  # noqa: F401
from oneepis_api.models.auth_security import (
    AuthLoginLock,
    AuthRecoveryPurpose,
    AuthRecoveryToken,
    AuthSecurityEvent,
)
from oneepis_api.services.auth import (
    AuthError,
    authenticate_local_user,
    create_access_token,
    hash_password,
    verify_access_token,
)
from oneepis_api.services.auth_notifications import dispatch_auth_recovery_notification
from oneepis_api.services.auth_recovery import create_recovery_request
from oneepis_api.services.auth_security import AuthRequestMetadata


@pytest.fixture
def client() -> Iterator[TestClient]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    testing_session = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def override_session() -> Iterator[Session]:
        with testing_session() as session:
            yield session

    def override_settings() -> Settings:
        return Settings(
            auth_secret="test-secret",
            auth_login_max_failed_attempts=2,
            auth_login_window_seconds=60,
            auth_login_lock_seconds=300,
            auth_recovery_max_requests=2,
            auth_recovery_window_seconds=3600,
        )

    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[get_settings] = override_settings
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)


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


def test_login_sets_http_only_session_cookie(client: TestClient) -> None:
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "medico@oneepis.local", "password": "medico"},
    )
    me_response = client.get("/api/v1/auth/me")

    assert login_response.status_code == 200
    assert "oneepis_session=" in login_response.headers["set-cookie"]
    assert "HttpOnly" in login_response.headers["set-cookie"]
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "medico@oneepis.local"


def test_logout_clears_session_cookie(client: TestClient) -> None:
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "medico@oneepis.local", "password": "medico"},
    )
    token = login_response.json()["access_token"]
    csrf_token = login_response.cookies["oneepis_csrf"]
    logout_response = client.post("/api/v1/auth/logout", headers={"X-OneEpis-CSRF": csrf_token})
    me_response = client.get("/api/v1/auth/me")
    bearer_response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert logout_response.status_code == 200
    assert "oneepis_session=" in logout_response.headers["set-cookie"]
    assert me_response.status_code == 401
    assert bearer_response.status_code == 401


def test_refresh_rotates_session_token(client: TestClient) -> None:
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "medico@oneepis.local", "password": "medico"},
    )
    old_token = login_response.json()["access_token"]
    csrf_token = login_response.cookies["oneepis_csrf"]

    refresh_response = client.post("/api/v1/auth/refresh", headers={"X-OneEpis-CSRF": csrf_token})
    new_token = refresh_response.json()["access_token"]
    old_token_response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {old_token}"},
    )
    new_token_response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {new_token}"},
    )

    assert refresh_response.status_code == 200
    assert new_token != old_token
    assert old_token_response.status_code == 401
    assert new_token_response.status_code == 200


def test_cookie_authenticated_mutations_require_csrf(client: TestClient) -> None:
    client.post(
        "/api/v1/auth/login",
        json={"email": "medico@oneepis.local", "password": "medico"},
    )
    response = client.post(
        "/api/v1/patients",
        json={
            "first_name": "Csrf",
            "last_name": "Paciente",
            "birth_date": "1990-01-01",
            "sex_at_birth": "unknown",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "CSRF token missing or invalid"


def test_cookie_authenticated_mutations_accept_csrf(client: TestClient) -> None:
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "medico@oneepis.local", "password": "medico"},
    )
    response = client.post(
        "/api/v1/patients",
        headers={"X-OneEpis-CSRF": login_response.cookies["oneepis_csrf"]},
        json={
            "first_name": "Csrf",
            "last_name": "Paciente",
            "birth_date": "1990-01-01",
            "sex_at_birth": "unknown",
        },
    )

    assert response.status_code == 201


def test_login_rejects_invalid_password(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "medico@oneepis.local", "password": "wrong"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Credenciales invalidas o cuenta no disponible"


def test_login_locks_after_multiple_failed_attempts(client: TestClient) -> None:
    first_response = client.post(
        "/api/v1/auth/login",
        json={"email": "medico@oneepis.local", "password": "wrong"},
    )
    second_response = client.post(
        "/api/v1/auth/login",
        json={"email": "medico@oneepis.local", "password": "wrong"},
    )
    valid_response = client.post(
        "/api/v1/auth/login",
        json={"email": "medico@oneepis.local", "password": "medico"},
    )

    assert first_response.status_code == 401
    assert second_response.status_code == 423
    assert valid_response.status_code == 423
    assert valid_response.json()["detail"] == "Credenciales invalidas o cuenta no disponible"


def test_active_login_lock_does_not_extend_on_additional_attempts(client: TestClient) -> None:
    client.post("/api/v1/auth/login", json={"email": "medico@oneepis.local", "password": "wrong"})
    client.post("/api/v1/auth/login", json={"email": "medico@oneepis.local", "password": "wrong"})
    override_session = app.dependency_overrides[get_session]
    session_iterator = override_session()
    session = next(session_iterator)
    try:
        lock_before = session.scalars(select(AuthLoginLock)).one()
        locked_until = lock_before.locked_until
        failed_attempts = lock_before.failed_attempts
    finally:
        session_iterator.close()

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "medico@oneepis.local", "password": "wrong"},
    )

    session_iterator = override_session()
    session = next(session_iterator)
    try:
        lock_after = session.scalars(select(AuthLoginLock)).one()
        assert lock_after.locked_until == locked_until
        assert lock_after.failed_attempts == failed_attempts
    finally:
        session_iterator.close()
    assert response.status_code == 423


def test_recovery_and_unlock_requests_do_not_enumerate_users(client: TestClient) -> None:
    recovery_response = client.post(
        "/api/v1/auth/password-recovery-requests",
        json={"email": "nobody@example.test"},
    )
    unlock_response = client.post(
        "/api/v1/auth/unlock-requests",
        json={"email": "medico@oneepis.local"},
    )

    assert recovery_response.status_code == 202
    assert recovery_response.json() == {"accepted": True}
    assert unlock_response.status_code == 202
    assert unlock_response.json() == {"accepted": True}


def test_auth_security_events_and_tokens_are_recorded(client: TestClient) -> None:
    client.post("/api/v1/auth/login", json={"email": "medico@oneepis.local", "password": "wrong"})
    client.post(
        "/api/v1/auth/password-recovery-requests",
        json={"email": "medico@oneepis.local"},
    )

    override_session = app.dependency_overrides[get_session]
    session_iterator = override_session()
    session = next(session_iterator)
    try:
        events = session.scalars(select(AuthSecurityEvent)).all()
        tokens = session.scalars(select(AuthRecoveryToken)).all()
    finally:
        session_iterator.close()

    assert len(events) >= 2
    assert tokens
    assert all(event.reason for event in events)
    assert any(event.reason == "notification_disabled" for event in events)


def test_recovery_requests_are_rate_limited_without_enumerating_users(
    client: TestClient,
) -> None:
    for _index in range(3):
        response = client.post(
            "/api/v1/auth/password-recovery-requests",
            json={"email": "medico@oneepis.local"},
        )
        assert response.status_code == 202
        assert response.json() == {"accepted": True}

    override_session = app.dependency_overrides[get_session]
    session_iterator = override_session()
    session = next(session_iterator)
    try:
        tokens = session.scalars(select(AuthRecoveryToken)).all()
        events = session.scalars(select(AuthSecurityEvent)).all()
    finally:
        session_iterator.close()

    assert len(tokens) == 2
    assert any(event.reason == "rate_limited" for event in events)


def test_unlock_confirmation_consumes_token_and_clears_login_lock(
    client: TestClient,
) -> None:
    client.post("/api/v1/auth/login", json={"email": "medico@oneepis.local", "password": "wrong"})
    client.post("/api/v1/auth/login", json={"email": "medico@oneepis.local", "password": "wrong"})

    override_session = app.dependency_overrides[get_session]
    session_iterator = override_session()
    session = next(session_iterator)
    try:
        dispatch = create_recovery_request(
            session,
            Settings(auth_secret="test-secret"),
            identifier="medico@oneepis.local",
            purpose=AuthRecoveryPurpose.UNLOCK,
            metadata=AuthRequestMetadata(),
        )
        session.commit()
    finally:
        session_iterator.close()

    assert dispatch is not None
    response = client.post(
        "/api/v1/auth/unlock-confirmations",
        json={"token": dispatch.token},
    )
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "medico@oneepis.local", "password": "medico"},
    )

    session_iterator = override_session()
    session = next(session_iterator)
    try:
        lock = session.scalars(select(AuthLoginLock)).one()
        token = session.scalars(
            select(AuthRecoveryToken).where(AuthRecoveryToken.purpose == AuthRecoveryPurpose.UNLOCK)
        ).one()
        events = session.scalars(select(AuthSecurityEvent)).all()
    finally:
        session_iterator.close()

    assert response.status_code == 202
    assert response.json() == {"accepted": True}
    assert login_response.status_code == 200
    assert lock.locked_until is None
    assert token.used_at is not None
    assert any(event.reason == "token_consumed" for event in events)


def test_unlock_confirmation_invalid_token_does_not_enumerate(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/unlock-confirmations",
        json={"token": "invalid-token-value-with-enough-length"},
    )

    assert response.status_code == 202
    assert response.json() == {"accepted": True}


def test_development_log_notification_builds_unlock_link(client: TestClient) -> None:
    settings = Settings(
        auth_secret="test-secret",
        auth_notification_provider="development_log",
        auth_public_web_base_url="https://oneepis.example.test",
    )
    override_session = app.dependency_overrides[get_session]
    session_iterator = override_session()
    session = next(session_iterator)
    try:
        dispatch = create_recovery_request(
            session,
            settings,
            identifier="medico@oneepis.local",
            purpose=AuthRecoveryPurpose.UNLOCK,
            metadata=AuthRequestMetadata(),
        )
        result = dispatch_auth_recovery_notification(
            session,
            settings,
            identifier="medico@oneepis.local",
            dispatch=dispatch,
            metadata=AuthRequestMetadata(),
        )
        session.commit()
    finally:
        session_iterator.close()

    assert dispatch is not None
    assert result.status == "development_logged"
    assert result.link == (
        "https://oneepis.example.test/login/desbloquear/confirmar"
        f"?token={dispatch.token}"
    )


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


def test_pbkdf2_password_hashes_are_supported() -> None:
    password_hash = hash_password("secret")
    settings = Settings(
        auth_secret="test-secret",
        auth_local_users=f"hash@oneepis.local|{password_hash}|Hash User|medico",
    )

    assert authenticate_local_user(settings, "hash@oneepis.local", "secret") is not None
    assert authenticate_local_user(settings, "hash@oneepis.local", "wrong") is None


def test_plain_local_passwords_are_rejected_outside_development() -> None:
    with pytest.raises(ValueError, match="pbkdf2_sha256"):
        Settings(
            environment="test",
            auth_secret="test-secret",
            auth_local_users="plain@oneepis.local|plain|Plain User|medico",
        )


def test_auth_numeric_settings_must_be_positive() -> None:
    with pytest.raises(ValueError, match="auth_login_lock_seconds"):
        Settings(auth_secret="test-secret", auth_login_lock_seconds=0)
