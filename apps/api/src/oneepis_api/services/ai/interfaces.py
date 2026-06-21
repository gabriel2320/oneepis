from __future__ import annotations

from typing import Protocol

from oneepis_api.schemas.ai import (
    AIProviderStatus,
    ClinicalInsightRequest,
    ClinicalInsightResponse,
    PatientAiSuggestionRequest,
    PatientAiSuggestionsResponse,
)
from oneepis_api.schemas.patient import PatientRecordSnapshot


class ClinicalAIProvider(Protocol):
    name: str

    def create_insight(self, payload: ClinicalInsightRequest) -> ClinicalInsightResponse:
        ...

    def status(self) -> AIProviderStatus:
        ...

    def create_patient_suggestions(
        self,
        patient_id: str,
        snapshot: PatientRecordSnapshot,
        payload: PatientAiSuggestionRequest,
    ) -> PatientAiSuggestionsResponse:
        ...
