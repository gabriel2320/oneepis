from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import Field, model_validator

from oneepis_api.models.clinical_record import AppointmentStatus
from oneepis_api.schemas.common import APIModel


class ClinicalAppointmentBase(APIModel):
    starts_at: datetime
    ends_at: datetime | None = None
    reason: str = Field(min_length=1, max_length=200)
    location_label: str | None = Field(default=None, max_length=120)
    clinician_label: str | None = Field(default=None, max_length=120)
    notes: str | None = Field(default=None, max_length=320)
    status: AppointmentStatus = AppointmentStatus.SCHEDULED

    @model_validator(mode="after")
    def validate_time_window(self) -> ClinicalAppointmentBase:
        if self.ends_at is not None and self.ends_at <= self.starts_at:
            raise ValueError("ends_at must be after starts_at")
        return self


class ClinicalAppointmentCreate(ClinicalAppointmentBase):
    pass


class ClinicalAppointmentUpdate(APIModel):
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    reason: str | None = Field(default=None, min_length=1, max_length=200)
    location_label: str | None = Field(default=None, max_length=120)
    clinician_label: str | None = Field(default=None, max_length=120)
    notes: str | None = Field(default=None, max_length=320)
    status: AppointmentStatus | None = None

    @model_validator(mode="after")
    def validate_time_window(self) -> ClinicalAppointmentUpdate:
        if (
            self.starts_at is not None
            and self.ends_at is not None
            and self.ends_at <= self.starts_at
        ):
            raise ValueError("ends_at must be after starts_at")
        return self


class ClinicalAppointmentRead(ClinicalAppointmentBase):
    id: uuid.UUID
    patient_id: uuid.UUID
    created_by: str
    created_at: datetime
    updated_at: datetime
