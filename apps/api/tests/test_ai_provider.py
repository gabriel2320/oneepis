import json

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
            return {"models": [{"name": self.model}]}

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


def test_get_ai_provider_selects_ollama() -> None:
    settings = Settings(ai_provider="ollama", ollama_model="llama3.2:latest")

    provider = get_ai_provider(settings)

    assert provider.name == "ollama"


def test_ollama_provider_status_reports_model_available() -> None:
    provider = FakeOllamaProvider(
        base_url="http://localhost:11434",
        model="llama3.2:latest",
        timeout_seconds=1,
    )

    status = provider.status()

    assert status.enabled is True
    assert status.available is True
    assert status.model == "llama3.2:latest"


def test_ollama_provider_parses_json_insight() -> None:
    provider = FakeOllamaProvider(
        base_url="http://localhost:11434",
        model="llama3.2:latest",
        timeout_seconds=1,
    )
    payload = ClinicalInsightRequest(
        source_text="Paciente demo estable.",
        focus="summary",
    )

    response = provider.create_insight(payload)

    assert response.status == "draft"
    assert response.provider == "ollama"
    assert response.model == "llama3.2:latest"
    assert response.summary == "Paciente estable en registro demo."
    assert response.structured_points == ["Sin alertas criticas documentadas."]
