import pytest
from pydantic import ValidationError

from oneepis_api.core.config import Settings
from oneepis_api.services.auth import hash_password


def test_development_allows_default_security_settings() -> None:
    settings = Settings()

    assert settings.environment == "development"
    assert settings.abac_enforcement_enabled is False


@pytest.mark.parametrize(
    "override",
    [
        {},
        {"auth_local_users": "admin@example.local|secret|Admin|admin"},
        {"auth_secret": "prod-secret"},
        {
            "auth_secret": "prod-secret",
            "auth_local_users": "admin@example.local|secret|Admin|admin",
            "auth_allow_dev_actor_header": True,
        },
        {
            "auth_secret": "prod-secret",
            "auth_local_users": "admin@example.local|secret|Admin|admin",
            "auth_enabled": False,
        },
        {
            "auth_secret": "prod-secret",
            "auth_local_users": f"admin@example.local|{hash_password('secret')}|Admin|admin",
            "auth_notification_provider": "development_log",
        },
        {
            "auth_secret": "prod-secret",
            "auth_local_users": f"admin@example.local|{hash_password('secret')}|Admin|admin",
            "abac_enforcement_enabled": True,
        },
    ],
)
def test_non_development_rejects_insecure_auth_settings(override: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        Settings(environment="production", **override)


def test_non_development_accepts_explicit_secure_auth_settings() -> None:
    password_hash = hash_password("secret")
    settings = Settings(
        environment="production",
        auth_secret="prod-secret",
        auth_local_users=f"admin@example.local|{password_hash}|Admin|admin",
    )

    assert settings.environment == "production"


def test_non_development_rejects_wildcard_cors_origin() -> None:
    password_hash = hash_password("secret")

    with pytest.raises(ValidationError):
        Settings(
            environment="production",
            auth_secret="prod-secret",
            auth_local_users=f"admin@example.local|{password_hash}|Admin|admin",
            cors_origins=["*"],
        )


def test_non_development_rejects_external_ollama_base_url() -> None:
    password_hash = hash_password("secret")

    with pytest.raises(ValidationError):
        Settings(
            environment="production",
            auth_secret="prod-secret",
            auth_local_users=f"admin@example.local|{password_hash}|Admin|admin",
            ollama_base_url="https://ollama.example.local",
        )
