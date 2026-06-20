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


class ClinicalEntryUpdate(APIModel):
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


class AllergyBase(APIModel):
    substance: str = Field(min_length=1, max_length=160)
    reaction: str | None = Field(default=None, max_length=240)
    severity: AllergySeverity = AllergySeverity.UNKNOWN
    status: RecordStatus = RecordStatus.ACTIVE
    recorded_at: datetime


class AllergyCreate(AllergyBase):
    pass


class AllergyUpdate(APIModel):
    substance: str | None = Field(default=None, min_length=1, max_length=160)
    reaction: str | None = Field(default=None, max_length=240)
    severity: AllergySeverity | None = None
    status: RecordStatus | None = None
    recorded_at: datetime | None = None


class AllergyRead(AllergyBase):
    id: uuid.UUID
    patient_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class MedicationBase(APIModel):
    name: str = Field(min_length=1, max_length=160)
    dose: str | None = Field(default=None, max_length=120)
    route: str | None = Field(default=None, max_length=80)
    frequency: str | None = Field(default=None, max_length=120)
    status: RecordStatus = RecordStatus.ACTIVE
    started_on: date | None = None
    ended_on: date | None = None


class MedicationCreate(MedicationBase):
    pass


class MedicationUpdate(APIModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    dose: str | None = Field(default=None, max_length=120)
    route: str | None = Field(default=None, max_length=80)
    frequency: str | None = Field(default=None, max_length=120)
    status: RecordStatus | None = None
    started_on: date | None = None
    ended_on: date | None = None


class MedicationRead(MedicationBase):
    id: uuid.UUID
    patient_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class VitalSignBase(APIModel):
    measured_at: datetime
    temperature_c: Decimal | None = None
    systolic_bp: int | None = Field(default=None, ge=40, le=300)
    diastolic_bp: int | None = Field(default=None, ge=20, le=200)
    heart_rate_bpm: int | None = Field(default=None, ge=20, le=260)
    respiratory_rate_bpm: int | None = Field(default=None, ge=4, le=80)
    oxygen_saturation_pct: Decimal | None = Field(default=None, ge=0, le=100)
    notes: str | None = Field(default=None, max_length=240)


class VitalSignCreate(VitalSignBase):
    pass


class VitalSignUpdate(APIModel):
    measured_at: datetime | None = None
    temperature_c: Decimal | None = None
    systolic_bp: int | None = Field(default=None, ge=40, le=300)
    diastolic_bp: int | None = Field(default=None, ge=20, le=200)
    heart_rate_bpm: int | None = Field(default=None, ge=20, le=260)
    respiratory_rate_bpm: int | None = Field(default=None, ge=4, le=80)
    oxygen_saturation_pct: Decimal | None = Field(default=None, ge=0, le=100)
    notes: str | None = Field(default=None, max_length=240)


class VitalSignRead(VitalSignBase):
    id: uuid.UUID
    patient_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
