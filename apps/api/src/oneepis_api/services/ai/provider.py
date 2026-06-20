from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from oneepis_api.core.config import Settings
from oneepis_api.schemas.ai import ClinicalInsightRequest, ClinicalInsightResponse


class ClinicalAIProvider(Protocol):
    name: str

    def create_insight(self, payload: ClinicalInsightRequest) -> ClinicalInsightResponse:
        raise NotImplementedError


@dataclass(frozen=True)
class DisabledAIProvider:
    name: str = "disabled"

    def create_insight(self, payload: ClinicalInsightRequest) -> ClinicalInsightResponse:
        return ClinicalInsightResponse(
            provider=self.name,
            status="disabled",
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
            summary=summary,
            structured_points=points,
            safety_notes=[
                "Borrador asistido para revision humana.",
                "No reemplaza criterio clinico ni firma profesional.",
            ],
        )


def get_ai_provider(settings: Settings) -> ClinicalAIProvider:
    if settings.ai_provider == "local_rules":
        return LocalRulesProvider()
    return DisabledAIProvider(name=settings.ai_provider)
