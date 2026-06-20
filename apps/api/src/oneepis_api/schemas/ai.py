from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import Field

from oneepis_api.schemas.common import APIModel


class ClinicalInsightRequest(APIModel):
    patient_id: uuid.UUID | None = None
    source_text: str = Field(min_length=1, max_length=8000)
    focus: Literal["summary", "risks", "next_steps"] = "summary"


class ClinicalInsightResponse(APIModel):
    provider: str
    status: Literal["disabled", "draft", "error"]
    model: str | None = None
    summary: str
    structured_points: list[str] = Field(default_factory=list)
    safety_notes: list[str] = Field(default_factory=list)


class AiTaskStatus(APIModel):
    task: Literal["summary", "suggestions", "fallback", "embeddings"]
    model: str
    available: bool
    enabled: bool = True


class AIProviderStatus(APIModel):
    provider: str
    enabled: bool
    available: bool
    model: str | None = None
    summary_model: str | None = None
    suggestions_model: str | None = None
    fallback_model: str | None = None
    embeddings_model: str | None = None
    base_url: str | None = None
    available_models: list[str] = Field(default_factory=list)
    tasks: list[AiTaskStatus] = Field(default_factory=list)
    message: str


class PatientAiSuggestionRequest(APIModel):
    focus: Literal["summary", "safety", "documentation"] = "summary"


class ClinicalAiSuggestion(APIModel):
    title: str = Field(min_length=1, max_length=120)
    detail: str = Field(min_length=1, max_length=600)
    severity: Literal["info", "warning", "critical"] = "info"
    source: Literal["ollama", "local_rules"] = "local_rules"
    action_label: str | None = Field(default=None, max_length=80)


class PatientAiSuggestionsResponse(APIModel):
    provider: str
    status: Literal["disabled", "draft", "error"]
    model: str | None = None
    patient_id: uuid.UUID
    generated_at: datetime
    summary: str
    suggestions: list[ClinicalAiSuggestion] = Field(default_factory=list)
    safety_notes: list[str] = Field(default_factory=list)
