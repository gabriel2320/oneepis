from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from oneepis_api.core.config import Settings
from oneepis_api.schemas.ai import AIProviderStatus, ClinicalInsightRequest, ClinicalInsightResponse


class ClinicalAIProvider(Protocol):
    name: str

    def create_insight(self, payload: ClinicalInsightRequest) -> ClinicalInsightResponse:
        raise NotImplementedError

    def status(self) -> AIProviderStatus:
        raise NotImplementedError


@dataclass(frozen=True)
class DisabledAIProvider:
    name: str = "disabled"

    def create_insight(self, payload: ClinicalInsightRequest) -> ClinicalInsightResponse:
        return ClinicalInsightResponse(
            provider=self.name,
            status="disabled",
            model=None,
            summary=(
                "IA local no habilitada. "
                "La ficha clinica queda operativa sin depender de modelos."
            ),
            structured_points=[],
            safety_notes=[
                "No se genero diagnostico.",
                "No se envio informacion clinica a servicios externos.",
            ],
        )

    def status(self) -> AIProviderStatus:
        return AIProviderStatus(
            provider=self.name,
            enabled=False,
            available=False,
            message="IA local deshabilitada por configuracion.",
        )


@dataclass(frozen=True)
class LocalRulesProvider:
    name: str = "local_rules"

    def create_insight(self, payload: ClinicalInsightRequest) -> ClinicalInsightResponse:
        sentences = [
            item.strip()
            for item in payload.source_text.replace("\n", " ").split(".")
            if item.strip()
        ]
        points = sentences[:5]
        summary = " ".join(points[:2]) if points else "Sin contenido suficiente para resumir."
        if summary and not summary.endswith("."):
            summary = f"{summary}."

        return ClinicalInsightResponse(
            provider=self.name,
            status="draft",
            model=None,
            summary=summary,
            structured_points=points,
            safety_notes=[
                "Borrador asistido para revision humana.",
                "No reemplaza criterio clinico ni firma profesional.",
            ],
        )

    def status(self) -> AIProviderStatus:
        return AIProviderStatus(
            provider=self.name,
            enabled=True,
            available=True,
            message="Proveedor deterministico local activo.",
        )


@dataclass(frozen=True)
class OllamaProvider:
    base_url: str
    model: str
    timeout_seconds: float
    name: str = "ollama"

    def create_insight(self, payload: ClinicalInsightRequest) -> ClinicalInsightResponse:
        try:
            content = self._chat(payload)
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            return ClinicalInsightResponse(
                provider=self.name,
                status="error",
                model=self.model,
                summary=f"Ollama no pudo generar el borrador: {exc}",
                structured_points=[],
                safety_notes=[
                    "No se genero diagnostico.",
                    "No se modifico la ficha clinica.",
                    "Verifica que Ollama este corriendo y que el modelo exista localmente.",
                ],
            )

        parsed = _parse_json_content(content)
        summary = parsed.get("summary") or content.strip() or "Sin respuesta util del modelo."
        structured_points = _as_string_list(parsed.get("structured_points"))
        safety_notes = _as_string_list(parsed.get("safety_notes"))
        if not safety_notes:
            safety_notes = [
                "Borrador generado por IA local para revision humana.",
                "No reemplaza criterio clinico ni firma profesional.",
            ]

        return ClinicalInsightResponse(
            provider=self.name,
            status="draft",
            model=self.model,
            summary=summary,
            structured_points=structured_points,
            safety_notes=safety_notes,
        )

    def status(self) -> AIProviderStatus:
        try:
            data = self._request_json("GET", "/api/tags")
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            return AIProviderStatus(
                provider=self.name,
                enabled=True,
                available=False,
                model=self.model,
                base_url=self.base_url,
                message=f"Ollama no disponible: {exc}",
            )

        models = [item.get("name", "") for item in data.get("models", []) if item.get("name")]
        return AIProviderStatus(
            provider=self.name,
            enabled=True,
            available=self.model in models,
            model=self.model,
            base_url=self.base_url,
            available_models=models,
            message=(
                "Ollama activo y modelo disponible."
                if self.model in models
                else "Ollama activo, pero el modelo configurado no esta instalado."
            ),
        )

    def _chat(self, payload: ClinicalInsightRequest) -> str:
        data = self._request_json(
            "POST",
            "/api/chat",
            {
                "model": self.model,
                "stream": False,
                "format": "json",
                "options": {
                    "temperature": 0.1,
                },
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "Eres un asistente local de documentacion clinica para OneEpis. "
                            "No diagnostiques, no indiques tratamientos nuevos, no inventes datos "
                            "y no reemplaces la revision humana. Devuelve JSON valido "
                            "con las claves "
                            "summary, structured_points y safety_notes."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Foco: {payload.focus}.\n"
                            "Resume y ordena el siguiente texto clinico de forma conservadora:\n\n"
                            f"{payload.source_text}"
                        ),
                    },
                ],
            },
        )
        message = data.get("message", {})
        return str(message.get("content", ""))

    def _request_json(
        self,
        method: str,
        path: str,
        body: dict[str, object] | None = None,
    ) -> dict[str, object]:
        url = f"{self.base_url.rstrip('/')}{path}"
        payload = json.dumps(body).encode("utf-8") if body is not None else None
        request = Request(
            url,
            data=payload,
            method=method,
            headers={"Content-Type": "application/json"},
        )
        with urlopen(request, timeout=self.timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8"))


def _parse_json_content(content: str) -> dict[str, object]:
    try:
        value = json.loads(content)
    except json.JSONDecodeError:
        return {}

    return value if isinstance(value, dict) else {}


def _as_string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def get_ai_provider(settings: Settings) -> ClinicalAIProvider:
    if settings.ai_provider == "local_rules":
        return LocalRulesProvider()
    if settings.ai_provider == "ollama":
        return OllamaProvider(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model_summary or settings.ollama_model,
            timeout_seconds=settings.ollama_timeout_seconds,
        )
    return DisabledAIProvider(name=settings.ai_provider)
