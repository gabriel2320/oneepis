from __future__ import annotations

import uuid
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


class AIProviderStatus(APIModel):
    provider: str
    enabled: bool
    available: bool
    model: str | None = None
    base_url: str | None = None
    available_models: list[str] = Field(default_factory=list)
    message: str
