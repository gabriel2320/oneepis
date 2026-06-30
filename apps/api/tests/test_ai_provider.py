import json

from fastapi.testclient import TestClient

from oneepis_api.core.config import Settings
from oneepis_api.schemas.ai import ClinicalInsightRequest
from oneepis_api.services.ai.provider import OllamaProvider, get_ai_provider


class FakeOllamaProvider(OllamaProvider):
    def _request_json(
        self,
        method: str,
        path: str,
        body: dict[str, object] | None = None,
    ) -> dict[str, object]:
        if path == "/api/tags":
            return {
                "models": [
                    {"name": self.summary_model},
                    {"name": self.suggestions_model},
                    {"name": self.fallback_model},
                ]
            }

        return {
            "message": {
                "content": json.dumps(
                    {
                        "summary": "Paciente estable en registro demo.",
                        "structured_points": ["Sin alertas criticas documentadas."],
                        "safety_notes": ["Revision humana obligatoria."],
                    }
                )
            }
        }


class FakeMissingModelOllamaProvider(FakeOllamaProvider):
    def _request_json(
        self,
        method: str,
        path: str,
        body: dict[str, object] | None = None,
    ) -> dict[str, object]:
        if path == "/api/tags":
            return {"models": [{"name": "other-model"}]}
        return super()._request_json(method, path, body)


class FakeInvalidJsonOllamaProvider(FakeOllamaProvider):
    def _request_json(
        self,
        method: str,
        path: str,
        body: dict[str, object] | None = None,
    ) -> dict[str, object]:
        if path == "/api/tags":
            return super()._request_json(method, path, body)
        return {"message": {"content": "not json"}}


def test_get_ai_provider_selects_ollama() -> None:
    settings = Settings(ai_provider="ollama", ollama_model="llama3.2:latest")

    provider = get_ai_provider(settings)

    assert provider.name == "ollama"


def test_ai_status_requires_ai_access(client: TestClient, auth_headers) -> None:
    medico_auth = auth_headers(client)
    nursing_auth = auth_headers(
        client,
        email="enfermeria@oneepis.local",
        password="enfermeria",
    )
    readonly_auth = auth_headers(client, email="lector@oneepis.local", password="lector")

    medico_response = client.get("/api/v1/ai/status", headers=medico_auth)
    nursing_response = client.get("/api/v1/ai/status", headers=nursing_auth)
    readonly_response = client.get("/api/v1/ai/status", headers=readonly_auth)

    assert medico_response.status_code == 200
    assert nursing_response.status_code == 403
    assert readonly_response.status_code == 403


def test_get_ai_provider_prefers_summary_model_for_clinical_insights() -> None:
    settings = Settings(
        ai_provider="ollama",
        ollama_model="llama3.2:latest",
        ollama_model_summary="qwen3:8b",
    )

    provider = get_ai_provider(settings)

    assert provider.name == "ollama"
    assert provider.model == "qwen3:8b"


def test_get_ai_provider_prefers_suggestions_model() -> None:
    settings = Settings(
        ai_provider="ollama",
        ollama_model="llama3.2:latest",
        ollama_model_summary="qwen3:8b",
        ollama_model_suggestions="qwen3:14b",
    )

    provider = get_ai_provider(settings)

    assert provider.name == "ollama"
    assert provider.suggestions_model == "qwen3:14b"


def test_ollama_provider_status_reports_model_available() -> None:
    provider = FakeOllamaProvider(
        base_url="http://localhost:11434",
        summary_model="qwen3:8b",
        suggestions_model="qwen3:8b",
        fallback_model="llama3.2:latest",
        embeddings_model="bge-m3",
        timeout_seconds=1,
    )

    status = provider.status()

    assert status.enabled is True
    assert status.available is True
    assert status.model == "qwen3:8b"
    assert {task.task for task in status.tasks} == {
        "summary",
        "suggestions",
        "fallback",
        "embeddings",
    }


def test_ollama_provider_status_reports_missing_models() -> None:
    provider = FakeMissingModelOllamaProvider(
        base_url="http://localhost:11434",
        summary_model="qwen3:8b",
        suggestions_model="qwen3:8b",
        fallback_model="llama3.2:latest",
        embeddings_model="bge-m3",
        timeout_seconds=1,
    )

    status = provider.status()

    assert status.enabled is True
    assert status.available is False
    assert all(task.available is False for task in status.tasks)


def test_ollama_provider_parses_json_insight() -> None:
    provider = FakeOllamaProvider(
        base_url="http://localhost:11434",
        summary_model="qwen3:8b",
        suggestions_model="qwen3:8b",
        fallback_model="llama3.2:latest",
        embeddings_model="bge-m3",
        timeout_seconds=1,
    )
    payload = ClinicalInsightRequest(
        source_text="Paciente demo estable.",
        focus="summary",
    )

    response = provider.create_insight(payload)

    assert response.status == "draft"
    assert response.provider == "ollama"
    assert response.model == "qwen3:8b"
    assert response.summary == "Paciente estable en registro demo."
    assert response.structured_points == ["Sin alertas criticas documentadas."]


def test_ollama_provider_handles_invalid_json_insight() -> None:
    provider = FakeInvalidJsonOllamaProvider(
        base_url="http://localhost:11434",
        summary_model="qwen3:8b",
        suggestions_model="qwen3:8b",
        fallback_model="llama3.2:latest",
        embeddings_model="bge-m3",
        timeout_seconds=1,
    )
    payload = ClinicalInsightRequest(source_text="Paciente estable.", focus="summary")

    response = provider.create_insight(payload)

    assert response.status == "draft"
    assert response.summary == "not json"
