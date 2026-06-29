from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from oneepis_api.schemas.ai import (
    AIProviderStatus,
    AiTaskStatus,
    ClinicalInsightRequest,
    ClinicalInsightResponse,
    PatientAiSuggestionRequest,
    PatientAiSuggestionsResponse,
)
from oneepis_api.schemas.patient import PatientRecordSnapshot
from oneepis_api.services.ai.active_medication_context import (
    active_medication_suggestions,
    medication_context_safety_notes,
    merge_readonly_suggestions,
)
from oneepis_api.services.ai.parsing import as_string_list, parse_json_content, parse_suggestions
from oneepis_api.services.ai.snapshot import (
    local_snapshot_suggestions,
    snapshot_payload,
    snapshot_summary,
)


@dataclass(frozen=True)
class OllamaProvider:
    base_url: str
    summary_model: str
    suggestions_model: str
    fallback_model: str
    embeddings_model: str
    timeout_seconds: float
    name: str = "ollama"

    @property
    def model(self) -> str:
        return self.summary_model

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

        parsed = parse_json_content(content)
        summary = parsed.get("summary") or content.strip() or "Sin respuesta util del modelo."
        structured_points = as_string_list(parsed.get("structured_points"))
        safety_notes = as_string_list(parsed.get("safety_notes")) or [
            "Borrador generado por IA local para revision humana.",
            "No reemplaza criterio clinico ni firma profesional.",
        ]

        return ClinicalInsightResponse(
            provider=self.name,
            status="draft",
            model=self.model,
            summary=str(summary),
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
                model=self.summary_model,
                summary_model=self.summary_model,
                suggestions_model=self.suggestions_model,
                fallback_model=self.fallback_model,
                embeddings_model=self.embeddings_model,
                base_url=self.base_url,
                message=f"Ollama no disponible: {exc}",
            )

        models = [item.get("name", "") for item in data.get("models", []) if item.get("name")]
        task_status = self._task_status(models)
        available = any(item.available for item in task_status if item.task != "embeddings")
        return AIProviderStatus(
            provider=self.name,
            enabled=True,
            available=available,
            model=self.summary_model,
            summary_model=self.summary_model,
            suggestions_model=self.suggestions_model,
            fallback_model=self.fallback_model,
            embeddings_model=self.embeddings_model,
            base_url=self.base_url,
            available_models=models,
            tasks=task_status,
            message=(
                "Ollama activo y al menos un modelo clinico esta disponible."
                if available
                else "Ollama activo, pero los modelos clinicos configurados no estan instalados."
            ),
        )

    def create_patient_suggestions(
        self,
        patient_id: str,
        snapshot: PatientRecordSnapshot,
        payload: PatientAiSuggestionRequest,
    ) -> PatientAiSuggestionsResponse:
        model = self.suggestions_model or self.summary_model or self.fallback_model
        readonly_suggestions = active_medication_suggestions(snapshot)
        try:
            content = self._patient_suggestions_chat(snapshot, payload, model)
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            suggestions = merge_readonly_suggestions(
                readonly_suggestions,
                local_snapshot_suggestions(snapshot),
            )
            safety_notes = [
                "Fallback local no generativo.",
                "No se modifico la ficha clinica.",
                "Verifica que Ollama este corriendo y que el modelo exista localmente.",
            ]
            if readonly_suggestions:
                safety_notes.extend(medication_context_safety_notes())
            return PatientAiSuggestionsResponse(
                provider=self.name,
                status="error",
                model=model,
                patient_id=snapshot.patient.id,
                generated_at=datetime.now(UTC),
                summary=f"Ollama no pudo generar sugerencias: {exc}",
                suggestions=suggestions,
                safety_notes=safety_notes,
            )

        parsed = parse_json_content(content)
        suggestions = parse_suggestions(parsed.get("suggestions"), source="ollama")
        if not suggestions:
            suggestions = local_snapshot_suggestions(snapshot)
        suggestions = merge_readonly_suggestions(readonly_suggestions, suggestions)

        safety_notes = as_string_list(parsed.get("safety_notes")) or [
            "Borrador generado por Ollama local.",
            "Requiere revision humana antes de cualquier accion clinica.",
        ]
        if readonly_suggestions:
            safety_notes.extend(medication_context_safety_notes())
        summary = str(parsed.get("summary") or snapshot_summary(snapshot)).strip()

        return PatientAiSuggestionsResponse(
            provider=self.name,
            status="draft",
            model=model,
            patient_id=snapshot.patient.id,
            generated_at=datetime.now(UTC),
            summary=summary,
            suggestions=suggestions,
            safety_notes=safety_notes,
        )

    def _task_status(self, available_models: list[str]) -> list[AiTaskStatus]:
        return [
            AiTaskStatus(
                task="summary",
                model=self.summary_model,
                available=self.summary_model in available_models,
            ),
            AiTaskStatus(
                task="suggestions",
                model=self.suggestions_model,
                available=self.suggestions_model in available_models,
            ),
            AiTaskStatus(
                task="fallback",
                model=self.fallback_model,
                available=self.fallback_model in available_models,
            ),
            AiTaskStatus(
                task="embeddings",
                model=self.embeddings_model,
                available=self.embeddings_model in available_models,
                enabled=False,
            ),
        ]

    def _chat(self, payload: ClinicalInsightRequest) -> str:
        data = self._request_json(
            "POST",
            "/api/chat",
            {
                "model": self.summary_model,
                "stream": False,
                "format": "json",
                "options": {"temperature": 0.1},
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "Eres un asistente local de documentacion clinica para OneEpis. "
                            "No diagnostiques, no indiques tratamientos nuevos, no inventes datos "
                            "y no reemplaces la revision humana. Devuelve JSON valido "
                            "con las claves summary, structured_points y safety_notes."
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

    def _patient_suggestions_chat(
        self,
        snapshot: PatientRecordSnapshot,
        payload: PatientAiSuggestionRequest,
        model: str,
    ) -> str:
        data = self._request_json(
            "POST",
            "/api/chat",
            {
                "model": model,
                "stream": False,
                "format": "json",
                "options": {"temperature": 0.1},
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "Eres un asistente local de documentacion clinica para OneEpis. "
                            "No diagnostiques, no indiques tratamientos nuevos, no inventes datos, "
                            "no firmes y no escribas ficha. Devuelve solo JSON valido "
                            "con las claves summary, suggestions y safety_notes. "
                            "Cada suggestion debe incluir "
                            "title, detail, severity y action_label opcional."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Foco: {payload.focus}.\n"
                            "Analiza este snapshot estructurado y entrega sugerencias "
                            "conservadoras de documentacion clinica. No uses conocimiento "
                            "externo para diagnosticar.\n\n"
                            f"{snapshot_payload(snapshot)}"
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
