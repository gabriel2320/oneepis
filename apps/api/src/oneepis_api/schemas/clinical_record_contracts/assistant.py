from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import Field

from oneepis_api.schemas.common import APIModel

AssistantTimelineItemType = Literal[
    "encounter",
    "clinical_entry",
    "clinical_event",
    "vital_sign",
    "medication",
    "problem",
    "allergy",
]


class AssistantTimelineItem(APIModel):
    item_type: AssistantTimelineItemType
    item_id: uuid.UUID
    occurred_at: datetime
    label: str = Field(min_length=1, max_length=160)
    summary: str = Field(min_length=1, max_length=320)
    source_label: str = Field(min_length=1, max_length=160)
    source_path: str = Field(min_length=1, max_length=240)


class AssistantTimelineResponse(APIModel):
    patient_id: uuid.UUID
    items: list[AssistantTimelineItem] = Field(default_factory=list)
    missing_data: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    limit: int = Field(ge=1, le=100)
    has_more: bool = False
    applies_changes: bool = False


class AssistantChartRequest(APIModel):
    series: list[str] = Field(default_factory=list, max_length=16)
    limit: int = Field(default=100, ge=1, le=500)


class AssistantChartPoint(APIModel):
    occurred_at: datetime
    value: float
    source_type: Literal["vital_sign", "clinical_event", "lab_result"]
    source_id: uuid.UUID
    source_path: str = Field(min_length=1, max_length=240)
    note: str | None = Field(default=None, max_length=160)


class AssistantChartSeries(APIModel):
    key: str = Field(min_length=1, max_length=80)
    label: str = Field(min_length=1, max_length=160)
    unit: str | None = Field(default=None, max_length=40)
    source_label: str = Field(min_length=1, max_length=160)
    points: list[AssistantChartPoint] = Field(default_factory=list)


class AssistantChartResponse(APIModel):
    patient_id: uuid.UUID
    series: list[AssistantChartSeries] = Field(default_factory=list)
    missing_data: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    limit: int = Field(ge=1, le=500)
    has_more: bool = False
    applies_changes: bool = False


AssistantCorrelationPreset = Literal[
    "fever_infection",
    "renal_medications",
    "respiratory_oxygen",
    "hemoglobin_bleeding",
    "medication_changes",
]


class AssistantCorrelationRequest(APIModel):
    presets: list[AssistantCorrelationPreset] = Field(default_factory=list, max_length=8)
    limit: int = Field(default=100, ge=1, le=500)


class AssistantCorrelationEvidence(APIModel):
    source_type: Literal["vital_sign", "clinical_event", "lab_result", "medication"]
    source_id: uuid.UUID
    occurred_at: datetime
    label: str = Field(min_length=1, max_length=160)
    summary: str = Field(min_length=1, max_length=320)
    source_path: str = Field(min_length=1, max_length=240)


class AssistantCorrelationResult(APIModel):
    preset: AssistantCorrelationPreset
    label: str = Field(min_length=1, max_length=160)
    summary: str = Field(min_length=1, max_length=320)
    evidence: list[AssistantCorrelationEvidence] = Field(default_factory=list)
    missing_data: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class AssistantCorrelationResponse(APIModel):
    patient_id: uuid.UUID
    correlations: list[AssistantCorrelationResult] = Field(default_factory=list)
    missing_data: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    limit: int = Field(ge=1, le=500)
    has_more: bool = False
    applies_changes: bool = False


class AssistantSearchResult(APIModel):
    item_type: AssistantTimelineItemType
    item_id: uuid.UUID
    occurred_at: datetime
    label: str = Field(min_length=1, max_length=160)
    snippet: str = Field(min_length=1, max_length=320)
    matched_fields: list[str] = Field(default_factory=list)
    source_label: str = Field(min_length=1, max_length=160)
    source_path: str = Field(min_length=1, max_length=240)


class AssistantSearchResponse(APIModel):
    patient_id: uuid.UUID
    query: str = Field(min_length=2, max_length=120)
    results: list[AssistantSearchResult] = Field(default_factory=list)
    missing_data: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    limit: int = Field(ge=1, le=100)
    has_more: bool = False
    applies_changes: bool = False
