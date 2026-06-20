from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


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
    auth_secret: str = "oneepis-local-dev-secret-change-me"
    auth_token_ttl_minutes: int = 720
    auth_allow_dev_actor_header: bool = False
    auth_local_users: str = (
        "admin@oneepis.local|admin|Administrador Dev|admin,dev;"
        "medico@oneepis.local|medico|Medico Dev|medico;"
        "enfermeria@oneepis.local|enfermeria|Enfermeria Dev|enfermeria;"
        "lector@oneepis.local|lector|Lectura Dev|solo_lectura"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="ONEEPIS_",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
