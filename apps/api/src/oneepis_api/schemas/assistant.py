from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any, Literal

from pydantic import Field

from oneepis_api.schemas.common import APIModel

AssistantTimelineSourceType = Literal[
    "encounter",
    "clinical_entry",
    "clinical_event",
    "vital_sign",
    "active_problem",
    "medication",
    "allergy",
    "hospital_indication",
]


class AssistantTimelineItem(APIModel):
    source_type: AssistantTimelineSourceType
    source_id: uuid.UUID
    patient_id: uuid.UUID
    encounter_id: uuid.UUID | None = None
    occurred_at: datetime | None = None
    occurred_on: date | None = None
    label: str = Field(min_length=1, max_length=160)
    summary: str = Field(min_length=1, max_length=500)
    status: str | None = Field(default=None, max_length=80)
    details: list[str] = Field(default_factory=list)
    source_ref: str | None = Field(default=None, max_length=160)
    payload: dict[str, Any] = Field(default_factory=dict)


class AssistantTimelineResponse(APIModel):
    patient_id: uuid.UUID
    items: list[AssistantTimelineItem]
    missing: list[str] = Field(default_factory=list)
    limits: list[str] = Field(default_factory=list)


class AssistantSearchRequest(APIModel):
    query: str = Field(min_length=2, max_length=120)
    source_types: list[AssistantTimelineSourceType] = Field(default_factory=list)
    limit: int = Field(default=20, ge=1, le=50)


class AssistantSearchMatch(APIModel):
    item: AssistantTimelineItem
    matched_fields: list[str] = Field(default_factory=list)
    snippets: list[str] = Field(default_factory=list)


class AssistantSearchResponse(APIModel):
    patient_id: uuid.UUID
    query: str
    matches: list[AssistantSearchMatch]
    searched_source_types: list[AssistantTimelineSourceType]
    limits: list[str] = Field(default_factory=list)
