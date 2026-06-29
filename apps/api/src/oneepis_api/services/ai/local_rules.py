from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from oneepis_api.schemas.ai import (
    AIProviderStatus,
    ClinicalInsightRequest,
    ClinicalInsightResponse,
    PatientAiSuggestionRequest,
    PatientAiSuggestionsResponse,
)
from oneepis_api.schemas.patient import PatientRecordSnapshot
from oneepis_api.services.ai.active_medication_context import medication_context_safety_notes
from oneepis_api.services.ai.snapshot import local_snapshot_suggestions, snapshot_summary


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
        summary = " ".join(sentences[:2]) if sentences else "Sin contenido suficiente para resumir."
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
        suggestions = local_snapshot_suggestions(snapshot)
        safety_notes = [
            "Borrador IA basado en reglas locales.",
            "Requiere revision humana antes de cualquier accion clinica.",
        ]
        if snapshot.active_medications:
            safety_notes.extend(medication_context_safety_notes())
        return PatientAiSuggestionsResponse(
            provider=self.name,
            status="draft",
            model=None,
            patient_id=snapshot.patient.id,
            generated_at=datetime.now(UTC),
            summary=snapshot_summary(snapshot),
            suggestions=suggestions,
            safety_notes=safety_notes,
        )
