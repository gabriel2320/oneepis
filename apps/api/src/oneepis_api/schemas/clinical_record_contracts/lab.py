from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import Field

from oneepis_api.models.clinical_record import (
    ClinicalEventSourceType,
    RecordStatus,
)
from oneepis_api.models.lab import LabResultFlag
from oneepis_api.schemas.common import APIModel


class LabResultBase(APIModel):
    code: str | None = Field(default=None, max_length=80)
    name: str = Field(min_length=1, max_length=160)
    value: str | None = Field(default=None, max_length=80)
    numeric_value: Decimal | None = None
    unit: str | None = Field(default=None, max_length=40)
    reference_range: str | None = Field(default=None, max_length=120)
    flag: LabResultFlag = LabResultFlag.UNKNOWN
    status: RecordStatus = RecordStatus.ACTIVE
    notes: str | None = Field(default=None, max_length=240)


class LabResultCreate(LabResultBase):
    pass


class LabResultUpdate(APIModel):
    code: str | None = Field(default=None, max_length=80)
    name: str | None = Field(default=None, min_length=1, max_length=160)
    value: str | None = Field(default=None, max_length=80)
    numeric_value: Decimal | None = None
    unit: str | None = Field(default=None, max_length=40)
    reference_range: str | None = Field(default=None, max_length=120)
    flag: LabResultFlag | None = None
    status: RecordStatus | None = None
    notes: str | None = Field(default=None, max_length=240)


class LabResultSourceRead(APIModel):
    source_type: ClinicalEventSourceType
    source_ref: str | None = None
    panel_id: uuid.UUID
    panel_name: str
    request_path: str = Field(min_length=1, max_length=240)
    label: str = Field(min_length=1, max_length=200)


class LabResultRead(LabResultBase):
    id: uuid.UUID
    panel_id: uuid.UUID
    patient_id: uuid.UUID
    source: LabResultSourceRead
    created_at: datetime
    updated_at: datetime


class LabPanelBase(APIModel):
    encounter_id: uuid.UUID | None = None
    occurred_at: datetime
    panel_name: str = Field(min_length=1, max_length=160)
    source_type: ClinicalEventSourceType = ClinicalEventSourceType.MANUAL
    source_ref: str | None = Field(default=None, max_length=160)
    status: RecordStatus = RecordStatus.ACTIVE
    summary: str | None = Field(default=None, max_length=280)
    created_by: str = Field(default="system", max_length=120)


class LabPanelCreate(LabPanelBase):
    results: list[LabResultCreate] = Field(min_length=1, max_length=100)


class LabPanelUpdate(APIModel):
    encounter_id: uuid.UUID | None = None
    occurred_at: datetime | None = None
    panel_name: str | None = Field(default=None, min_length=1, max_length=160)
    source_type: ClinicalEventSourceType | None = None
    source_ref: str | None = Field(default=None, max_length=160)
    status: RecordStatus | None = None
    summary: str | None = Field(default=None, max_length=280)


class LabPanelRead(LabPanelBase):
    id: uuid.UUID
    patient_id: uuid.UUID
    results: list[LabResultRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
