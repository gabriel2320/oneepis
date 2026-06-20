from __future__ import annotations

import uuid
from datetime import datetime

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
