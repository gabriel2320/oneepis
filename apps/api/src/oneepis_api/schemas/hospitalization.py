from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import Field

from oneepis_api.models.hospitalization import HospitalBedStatus
from oneepis_api.schemas.clinical_record import ClinicalEncounterRead
from oneepis_api.schemas.common import APIModel
from oneepis_api.schemas.patient import PatientRead


class HospitalBedBase(APIModel):
    ward: str = Field(min_length=1, max_length=80)
    room: str = Field(min_length=1, max_length=80)
    bed_label: str = Field(min_length=1, max_length=80)
    status: HospitalBedStatus = HospitalBedStatus.AVAILABLE
    encounter_id: uuid.UUID | None = None
    notes: str | None = Field(default=None, max_length=240)


class HospitalBedCreate(HospitalBedBase):
    pass


class HospitalBedUpdate(APIModel):
    ward: str | None = Field(default=None, min_length=1, max_length=80)
    room: str | None = Field(default=None, min_length=1, max_length=80)
    bed_label: str | None = Field(default=None, min_length=1, max_length=80)
    status: HospitalBedStatus | None = None
    encounter_id: uuid.UUID | None = None
    notes: str | None = Field(default=None, max_length=240)


class HospitalBedRead(HospitalBedBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class HospitalizationBoardItem(APIModel):
    patient: PatientRead
    encounter: ClinicalEncounterRead
    bed: HospitalBedRead | None = None


class HospitalDailySheetBase(APIModel):
    sheet_date: date
    clinical_summary: str = Field(min_length=1, max_length=2000)
    overnight_events: str | None = Field(default=None, max_length=2000)
    active_plan: str | None = Field(default=None, max_length=2000)
    pending_tasks: str | None = Field(default=None, max_length=2000)
    safety_notes: str | None = Field(default=None, max_length=2000)


class HospitalDailySheetCreate(HospitalDailySheetBase):
    pass


class HospitalDailySheetUpdate(APIModel):
    sheet_date: date | None = None
    clinical_summary: str | None = Field(default=None, min_length=1, max_length=2000)
    overnight_events: str | None = Field(default=None, max_length=2000)
    active_plan: str | None = Field(default=None, max_length=2000)
    pending_tasks: str | None = Field(default=None, max_length=2000)
    safety_notes: str | None = Field(default=None, max_length=2000)


class HospitalDailySheetRead(HospitalDailySheetBase):
    id: uuid.UUID
    patient_id: uuid.UUID
    encounter_id: uuid.UUID
    created_by: str
    created_at: datetime
    updated_at: datetime
