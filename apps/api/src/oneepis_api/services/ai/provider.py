from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from oneepis_api.core.config import Settings
from oneepis_api.schemas.ai import (
    AIProviderStatus,
    AiTaskStatus,
    ClinicalAiSuggestion,
    ClinicalInsightRequest,
    ClinicalInsightResponse,
    PatientAiSuggestionRequest,
    PatientAiSuggestionsResponse,
)
from oneepis_api.schemas.patient import PatientRecordSnapshot


class ClinicalAIProvider(Protocol):
    name: str

    def create_insight(self, payload: ClinicalInsightRequest) -> ClinicalInsightResponse:
        raise NotImplementedError

    def status(self) -> AIProviderStatus:
        raise NotImplementedError

    def create_patient_suggestions(
        self,
        patient_id: str,
        snapshot: PatientRecordSnapshot,
        payload: PatientAiSuggestionRequest,
    ) -> PatientAiSuggestionsResponse:
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

    def create_patient_suggestions(
        self,
        patient_id: str,
        snapshot: PatientRecordSnapshot,
        payload: PatientAiSuggestionRequest,
    ) -> PatientAiSuggestionsResponse:
        return PatientAiSuggestionsResponse(
            provider=self.name,
            status="disabled",
            model=None,
            patient_id=snapshot.patient.id,
            generated_at=datetime.now(UTC),
            summary="IA local deshabilitada.",
            suggestions=[],
            safety_notes=[
                "No se genero diagnostico.",
                "No se modifico la ficha clinica.",
            ],
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

    def create_patient_suggestions(
        self,
        patient_id: str,
        snapshot: PatientRecordSnapshot,
        payload: PatientAiSuggestionRequest,
    ) -> PatientAiSuggestionsResponse:
        suggestions = _local_snapshot_suggestions(snapshot)
        return PatientAiSuggestionsResponse(
            provider=self.name,
            status="draft",
            model=None,
            patient_id=snapshot.patient.id,
            generated_at=datetime.now(UTC),
            summary=_snapshot_summary(snapshot),
            suggestions=suggestions,
            safety_notes=[
                "Borrador IA basado en reglas locales.",
                "Requiere revision humana antes de cualquier accion clinica.",
            ],
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
        try:
            content = self._patient_suggestions_chat(snapshot, payload, model)
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            local_suggestions = _local_snapshot_suggestions(snapshot)
            return PatientAiSuggestionsResponse(
                provider=self.name,
                status="error",
                model=model,
                patient_id=snapshot.patient.id,
                generated_at=datetime.now(UTC),
                summary=f"Ollama no pudo generar sugerencias: {exc}",
                suggestions=local_suggestions,
                safety_notes=[
                    "Fallback local no generativo.",
                    "No se modifico la ficha clinica.",
                    "Verifica que Ollama este corriendo y que el modelo exista localmente.",
                ],
            )

        parsed = _parse_json_content(content)
        suggestions = _parse_suggestions(parsed.get("suggestions"), source="ollama")
        if not suggestions:
            suggestions = _local_snapshot_suggestions(snapshot)

        safety_notes = _as_string_list(parsed.get("safety_notes")) or [
            "Borrador generado por Ollama local.",
            "Requiere revision humana antes de cualquier accion clinica.",
        ]
        summary = str(parsed.get("summary") or _snapshot_summary(snapshot)).strip()

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
                "options": {
                    "temperature": 0.1,
                },
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "Eres un asistente local de documentacion clinica para OneEpis. "
                            "No diagnostiques, no indiques tratamientos nuevos, no inventes datos, "
                            "no firmes y no escribas ficha. Devuelve solo JSON valido "
                            "con las claves "
                            "summary, suggestions y safety_notes. Cada suggestion debe incluir "
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
                            f"{_snapshot_payload(snapshot)}"
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


def _parse_suggestions(value: object, *, source: str) -> list[ClinicalAiSuggestion]:
    if not isinstance(value, list):
        return []

    suggestions: list[ClinicalAiSuggestion] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or "").strip()
        detail = str(item.get("detail") or "").strip()
        severity = str(item.get("severity") or "info").strip()
        if severity not in {"info", "warning", "critical"}:
            severity = "info"
        action_label = item.get("action_label")
        if not title or not detail:
            continue
        suggestions.append(
            ClinicalAiSuggestion(
                title=title,
                detail=detail,
                severity=severity,  # type: ignore[arg-type]
                source=source,  # type: ignore[arg-type]
                action_label=str(action_label).strip() if action_label else None,
            )
        )
    return suggestions[:8]


def _local_snapshot_suggestions(snapshot: PatientRecordSnapshot) -> list[ClinicalAiSuggestion]:
    suggestions: list[ClinicalAiSuggestion] = []
    if snapshot.latest_vitals is None:
        suggestions.append(
            ClinicalAiSuggestion(
                title="Faltan signos vitales recientes",
                detail="No hay un control de signos vitales en el snapshot actual.",
                severity="warning",
                source="local_rules",
                action_label="Registrar signos",
            )
        )

    for entry in snapshot.recent_entries[:3]:
        if not entry.plan:
            suggestions.append(
                ClinicalAiSuggestion(
                    title="Evolucion sin plan explicito",
                    detail=f"La evolucion '{entry.title}' no tiene plan documentado.",
                    severity="warning",
                    source="local_rules",
                    action_label="Revisar SOAP",
                )
            )

    for medication in snapshot.active_medications:
        if medication.started_on is None:
            suggestions.append(
                ClinicalAiSuggestion(
                    title="Medicacion sin fecha de inicio",
                    detail=f"{medication.name} esta activa sin fecha de inicio registrada.",
                    severity="info",
                    source="local_rules",
                    action_label="Revisar medicacion",
                )
            )

    severe_allergies = [
        item.substance for item in snapshot.active_allergies if item.severity == "severe"
    ]
    if severe_allergies:
        suggestions.append(
            ClinicalAiSuggestion(
                title="Alergia severa activa",
                detail=f"Alergias severas registradas: {', '.join(severe_allergies)}.",
                severity="critical",
                source="local_rules",
                action_label="Ver alergias",
            )
        )

    if not suggestions:
        suggestions.append(
            ClinicalAiSuggestion(
                title="Ficha sin vacios criticos detectados",
                detail="El snapshot no muestra alertas documentales basicas segun reglas locales.",
                severity="info",
                source="local_rules",
            )
        )

    return suggestions[:8]


def _snapshot_summary(snapshot: PatientRecordSnapshot) -> str:
    patient = snapshot.patient
    entry_count = len(snapshot.recent_entries)
    allergy_count = len(snapshot.active_allergies)
    medication_count = len(snapshot.active_medications)
    return (
        f"Snapshot de {patient.first_name} {patient.last_name}: "
        f"{entry_count} evoluciones recientes, {allergy_count} alergias activas, "
        f"{medication_count} medicamentos activos."
    )


def _snapshot_payload(snapshot: PatientRecordSnapshot) -> str:
    return json.dumps(
        snapshot.model_dump(mode="json"),
        ensure_ascii=True,
        default=str,
    )


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
