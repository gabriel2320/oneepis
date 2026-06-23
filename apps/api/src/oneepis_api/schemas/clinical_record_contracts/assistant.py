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
