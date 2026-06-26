from functools import lru_cache
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_AUTH_SECRET = "oneepis-local-dev-secret-change-me"
DEFAULT_AUTH_LOCAL_USERS = (
    "admin@oneepis.local|admin|Administrador Dev|admin,dev;"
    "medico@oneepis.local|medico|Medico Dev|medico;"
    "enfermeria@oneepis.local|enfermeria|Enfermeria Dev|enfermeria;"
    "lector@oneepis.local|lector|Lectura Dev|solo_lectura"
)


class Settings(BaseSettings):
    app_name: str = "OneEpis"
    environment: str = "development"
    database_url: str = "postgresql+psycopg://oneepis:oneepis@localhost:5433/oneepis"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])
    ai_provider: str = "ollama"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:latest"
    ollama_model_summary: str | None = "qwen3:8b"
    ollama_model_suggestions: str | None = "qwen3:8b"
    ollama_model_embeddings: str | None = "bge-m3"
    ollama_timeout_seconds: float = 60.0
    auth_enabled: bool = True
    auth_secret: str = DEFAULT_AUTH_SECRET
    auth_token_ttl_minutes: int = 720
    auth_session_cookie_name: str = "oneepis_session"
    auth_csrf_cookie_name: str = "oneepis_csrf"
    auth_allow_dev_actor_header: bool = False
    auth_local_users: str = DEFAULT_AUTH_LOCAL_USERS
    auth_login_max_failed_attempts: int = 5
    auth_login_window_seconds: int = 900
    auth_login_lock_seconds: int = 900
    auth_recovery_token_ttl_minutes: int = 30
    auth_recovery_max_requests: int = 3
    auth_recovery_window_seconds: int = 3600
    auth_notification_provider: Literal["disabled", "development_log"] = "disabled"
    auth_public_web_base_url: str = "http://localhost:3000"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="ONEEPIS_",
        extra="ignore",
    )

    @model_validator(mode="after")
    def validate_non_development_security(self) -> "Settings":
        errors: list[str] = []
        for field_name in (
            "auth_token_ttl_minutes",
            "auth_login_max_failed_attempts",
            "auth_login_window_seconds",
            "auth_login_lock_seconds",
            "auth_recovery_token_ttl_minutes",
            "auth_recovery_max_requests",
            "auth_recovery_window_seconds",
        ):
            if getattr(self, field_name) <= 0:
                errors.append(f"{field_name} must be greater than zero")

        if self.environment.strip().lower() == "development":
            if errors:
                raise ValueError("; ".join(errors))
            return self

        if self.auth_secret == DEFAULT_AUTH_SECRET:
            errors.append("auth_secret must be changed outside development")
        if self.auth_local_users.strip() == DEFAULT_AUTH_LOCAL_USERS:
            errors.append("auth_local_users must be changed outside development")
        if _contains_plain_local_password(self.auth_local_users):
            errors.append(
                "auth_local_users passwords must use pbkdf2_sha256 hashes outside development"
            )
        if self.auth_allow_dev_actor_header:
            errors.append("auth_allow_dev_actor_header is development-only")
        if not self.auth_enabled:
            errors.append("auth_enabled cannot be false outside development")
        if self.auth_notification_provider == "development_log":
            errors.append("auth_notification_provider=development_log is development-only")
        if errors:
            raise ValueError("; ".join(errors))
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


def _contains_plain_local_password(raw_users: str) -> bool:
    for raw_item in raw_users.split(";"):
        item = raw_item.strip()
        if not item:
            continue
        parts = [part.strip() for part in item.split("|")]
        if len(parts) != 4:
            continue
        password = parts[1]
        if password and not password.startswith("pbkdf2_sha256$"):
            return True
    return False
