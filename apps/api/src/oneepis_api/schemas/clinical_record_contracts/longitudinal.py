from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import Field

from oneepis_api.models.clinical_record import (
    AllergySeverity,
    EncounterStatus,
    EncounterType,
    EncounterWorkflowKind,
    RecordStatus,
)
from oneepis_api.models.medication_catalog import (
    MedicationSourceReviewStatus,
    MedicationSourceSystem,
)
from oneepis_api.schemas.common import APIModel


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
    catalog_item_id: uuid.UUID | None = None
    name: str = Field(min_length=1, max_length=160)
    dose: str | None = Field(default=None, max_length=120)
    route: str | None = Field(default=None, max_length=80)
    frequency: str | None = Field(default=None, max_length=120)
    status: RecordStatus = RecordStatus.ACTIVE
    started_on: date | None = None
    ended_on: date | None = None
    dose_override_reason: str | None = Field(default=None, max_length=280)


class MedicationCreate(MedicationBase):
    pass


class MedicationUpdate(APIModel):
    catalog_item_id: uuid.UUID | None = None
    name: str | None = Field(default=None, min_length=1, max_length=160)
    dose: str | None = Field(default=None, max_length=120)
    route: str | None = Field(default=None, max_length=80)
    frequency: str | None = Field(default=None, max_length=120)
    status: RecordStatus | None = None
    started_on: date | None = None
    ended_on: date | None = None
    dose_override_reason: str | None = Field(default=None, max_length=280)


class MedicationSourceRead(APIModel):
    source_system: MedicationSourceSystem
    source_label: str = Field(max_length=160)
    source_url: str | None = Field(default=None, max_length=400)
    external_id: str | None = Field(default=None, max_length=120)
    source_version: str | None = Field(default=None, max_length=80)
    retrieved_at: datetime | None = None
    reviewed_at: datetime | None = None
    review_status: MedicationSourceReviewStatus = MedicationSourceReviewStatus.DRAFT


class MedicationRead(MedicationBase):
    id: uuid.UUID
    patient_id: uuid.UUID
    dose_check_snapshot: dict = Field(default_factory=dict)
    source: MedicationSourceRead | None = None
    missing_fields: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class ActiveProblemBase(APIModel):
    title: str = Field(min_length=1, max_length=160)
    code_system: str | None = Field(default=None, max_length=80)
    code: str | None = Field(default=None, max_length=80)
    status: RecordStatus = RecordStatus.ACTIVE
    onset_date: date | None = None
    resolved_on: date | None = None
    notes: str | None = Field(default=None, max_length=280)


class ActiveProblemCreate(ActiveProblemBase):
    pass


class ActiveProblemUpdate(APIModel):
    title: str | None = Field(default=None, min_length=1, max_length=160)
    code_system: str | None = Field(default=None, max_length=80)
    code: str | None = Field(default=None, max_length=80)
    status: RecordStatus | None = None
    onset_date: date | None = None
    resolved_on: date | None = None
    notes: str | None = Field(default=None, max_length=280)


class ActiveProblemRead(ActiveProblemBase):
    id: uuid.UUID
    patient_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class ClinicalEncounterBase(APIModel):
    type: EncounterType = EncounterType.UNKNOWN
    status: EncounterStatus = EncounterStatus.IN_PROGRESS
    workflow_kind: EncounterWorkflowKind = EncounterWorkflowKind.GENERAL
    reason: str = Field(min_length=1, max_length=200)
    started_at: datetime
    ended_at: datetime | None = None
    location_label: str | None = Field(default=None, max_length=120)
    notes: str | None = Field(default=None, max_length=320)


class ClinicalEncounterCreate(ClinicalEncounterBase):
    pass


class ClinicalEncounterUpdate(APIModel):
    type: EncounterType | None = None
    status: EncounterStatus | None = None
    workflow_kind: EncounterWorkflowKind | None = None
    reason: str | None = Field(default=None, min_length=1, max_length=200)
    started_at: datetime | None = None
    ended_at: datetime | None = None
    location_label: str | None = Field(default=None, max_length=120)
    notes: str | None = Field(default=None, max_length=320)


class ClinicalEncounterRead(ClinicalEncounterBase):
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
