from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any

from pydantic import Field

from oneepis_api.models.patient import SexAtBirth
from oneepis_api.schemas.clinical_record import (
    AllergyRead,
    ClinicalEntryRead,
    MedicationRead,
    VitalSignRead,
)
from oneepis_api.schemas.common import APIModel


class PatientBase(APIModel):
    first_name: str = Field(min_length=1, max_length=80)
    last_name: str = Field(min_length=1, max_length=80)
    preferred_name: str | None = Field(default=None, max_length=80)
    birth_date: date
    sex_at_birth: SexAtBirth = SexAtBirth.UNKNOWN
    document_id_hash: str | None = Field(default=None, max_length=128)
    clinical_identifier: str | None = Field(default=None, max_length=64)
    contact_phone: str | None = Field(default=None, max_length=40)
    email: str | None = Field(default=None, max_length=120)
    emergency_contact: dict[str, Any] = Field(default_factory=dict)


class PatientCreate(PatientBase):
    pass


class PatientUpdate(APIModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=80)
    last_name: str | None = Field(default=None, min_length=1, max_length=80)
    preferred_name: str | None = Field(default=None, max_length=80)
    contact_phone: str | None = Field(default=None, max_length=40)
    email: str | None = Field(default=None, max_length=120)
    emergency_contact: dict[str, Any] | None = None


class PatientRead(PatientBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class PatientRecordSnapshot(APIModel):
    patient: PatientRead
    latest_vitals: VitalSignRead | None = None
    active_allergies: list[AllergyRead] = Field(default_factory=list)
    active_medications: list[MedicationRead] = Field(default_factory=list)
    recent_entries: list[ClinicalEntryRead] = Field(default_factory=list)
