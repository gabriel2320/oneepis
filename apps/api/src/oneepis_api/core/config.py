from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "OneEpis"
    environment: str = "development"
    database_url: str = "postgresql+psycopg://oneepis:oneepis@localhost:5433/oneepis"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])
    ai_provider: str = "disabled"
    ollama_base_url: str = "http://localhost:11434"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="ONEEPIS_",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
