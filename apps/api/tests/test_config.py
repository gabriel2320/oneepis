import pytest
from pydantic import ValidationError

from oneepis_api.core.config import Settings


def test_development_allows_default_security_settings() -> None:
    settings = Settings()

    assert settings.environment == "development"


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
    ],
)
def test_non_development_rejects_insecure_auth_settings(override: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        Settings(environment="production", **override)


def test_non_development_accepts_explicit_secure_auth_settings() -> None:
    settings = Settings(
        environment="production",
        auth_secret="prod-secret",
        auth_local_users="admin@example.local|secret|Admin|admin",
    )

    assert settings.environment == "production"
