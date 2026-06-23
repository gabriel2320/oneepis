from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import Field

from oneepis_api.models.clinical_record import (
    ClinicalEntryKind,
    ClinicalEntryStatus,
    ClinicalEventSourceType,
    ClinicalEventType,
)
from oneepis_api.schemas.common import APIModel


class ClinicalEntryBase(APIModel):
    encounter_id: uuid.UUID | None = None
    kind: ClinicalEntryKind = ClinicalEntryKind.NOTE
    status: ClinicalEntryStatus = ClinicalEntryStatus.DRAFT
    occurred_at: datetime
    title: str = Field(min_length=1, max_length=160)
    subjective: str | None = None
    objective: str | None = None
    assessment: str | None = None
    plan: str | None = None
    tags: list[str] = Field(default_factory=list)
    extra_data: dict[str, Any] = Field(default_factory=dict)
    created_by: str = Field(default="system", max_length=120)


class ClinicalEntryCreate(ClinicalEntryBase):
    pass


class ClinicalEntryUpdate(APIModel):
    encounter_id: uuid.UUID | None = None
    status: ClinicalEntryStatus | None = None
    occurred_at: datetime | None = None
    title: str | None = Field(default=None, min_length=1, max_length=160)
    subjective: str | None = None
    objective: str | None = None
    assessment: str | None = None
    plan: str | None = None
    tags: list[str] | None = None
    extra_data: dict[str, Any] | None = None


class ClinicalEntryRead(ClinicalEntryBase):
    id: uuid.UUID
    patient_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class ClinicalEventBase(APIModel):
    encounter_id: uuid.UUID | None = None
    event_type: ClinicalEventType
    occurred_at: datetime
    summary: str = Field(min_length=1, max_length=280)
    source_type: ClinicalEventSourceType = ClinicalEventSourceType.MANUAL
    source_ref: str | None = Field(default=None, max_length=160)
    payload: dict[str, Any] = Field(default_factory=dict)
    created_by: str = Field(default="system", max_length=120)


class ClinicalEventCreate(ClinicalEventBase):
    pass


class ClinicalEventUpdate(APIModel):
    encounter_id: uuid.UUID | None = None
    event_type: ClinicalEventType | None = None
    occurred_at: datetime | None = None
    summary: str | None = Field(default=None, min_length=1, max_length=280)
    source_type: ClinicalEventSourceType | None = None
    source_ref: str | None = Field(default=None, max_length=160)
    payload: dict[str, Any] | None = None


class ClinicalEventRead(ClinicalEventBase):
    id: uuid.UUID
    patient_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class ClinicalTimelineRead(APIModel):
    events: list[ClinicalEventRead]
    entries: list[ClinicalEntryRead]
