from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import Field

from oneepis_api.models.clinical_record import (
    AllergySeverity,
    ClinicalEntryKind,
    ClinicalEntryStatus,
    RecordStatus,
)
from oneepis_api.schemas.common import APIModel


class ClinicalEntryBase(APIModel):
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


class ClinicalEntryRead(ClinicalEntryBase):
    id: uuid.UUID
    patient_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class AllergyRead(APIModel):
    id: uuid.UUID
    patient_id: uuid.UUID
    substance: str
    reaction: str | None
    severity: AllergySeverity
    status: RecordStatus
    recorded_at: datetime
    created_at: datetime
    updated_at: datetime


class MedicationRead(APIModel):
    id: uuid.UUID
    patient_id: uuid.UUID
    name: str
    dose: str | None
    route: str | None
    frequency: str | None
    status: RecordStatus
    started_on: date | None
    ended_on: date | None
    created_at: datetime
    updated_at: datetime


class VitalSignRead(APIModel):
    id: uuid.UUID
    patient_id: uuid.UUID
    measured_at: datetime
    temperature_c: Decimal | None
    systolic_bp: int | None
    diastolic_bp: int | None
    heart_rate_bpm: int | None
    respiratory_rate_bpm: int | None
    oxygen_saturation_pct: Decimal | None
    notes: str | None
    created_at: datetime
    updated_at: datetime
