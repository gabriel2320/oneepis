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
