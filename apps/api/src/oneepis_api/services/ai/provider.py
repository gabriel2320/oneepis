from __future__ import annotations

from oneepis_api.core.config import Settings
from oneepis_api.services.ai.disabled import DisabledAIProvider
from oneepis_api.services.ai.interfaces import ClinicalAIProvider
from oneepis_api.services.ai.local_rules import LocalRulesProvider
from oneepis_api.services.ai.ollama import OllamaProvider

__all__ = [
    "ClinicalAIProvider",
    "DisabledAIProvider",
    "LocalRulesProvider",
    "OllamaProvider",
    "get_ai_provider",
]


def get_ai_provider(settings: Settings) -> ClinicalAIProvider:
    if settings.ai_provider == "local_rules":
        return LocalRulesProvider()
    if settings.ai_provider == "ollama":
        return OllamaProvider(
            base_url=settings.ollama_base_url,
            summary_model=settings.ollama_model_summary or settings.ollama_model,
            suggestions_model=settings.ollama_model_suggestions
            or settings.ollama_model_summary
            or settings.ollama_model,
            fallback_model=settings.ollama_model,
            embeddings_model=settings.ollama_model_embeddings or "bge-m3",
            timeout_seconds=settings.ollama_timeout_seconds,
        )
    return DisabledAIProvider(name=settings.ai_provider)
