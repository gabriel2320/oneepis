from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any

from pydantic import Field, model_validator

from oneepis_api.models.clinical_record import ClinicalEventSourceType
from oneepis_api.models.patient import CareContext, PatientClinicalStatus, SexAtBirth
from oneepis_api.schemas.clinical_record import (
    ActiveProblemRead,
    AllergyRead,
    ClinicalEntryRead,
    MedicationRead,
    VitalSignRead,
)
from oneepis_api.schemas.clinical_record_contracts.diagnostics import (
    DiagnosisCodeReference,
    legacy_diagnostic_code_reference,
)
from oneepis_api.schemas.common import APIModel


class PatientBase(APIModel):
    first_name: str = Field(min_length=1, max_length=80)
    last_name: str = Field(min_length=1, max_length=80)
    preferred_name: str | None = Field(default=None, max_length=80)
    birth_date: date
    sex_at_birth: SexAtBirth = SexAtBirth.UNKNOWN
    clinical_status: PatientClinicalStatus = PatientClinicalStatus.ACTIVE
    current_care_context: CareContext = CareContext.UNKNOWN
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
    clinical_status: PatientClinicalStatus | None = None
    current_care_context: CareContext | None = None


class PatientRead(PatientBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class HistoricalDiagnosisRead(APIModel):
    source_event_id: uuid.UUID
    title: str = Field(min_length=1, max_length=280)
    occurred_at: datetime
    source_type: ClinicalEventSourceType
    source_ref: str | None = Field(default=None, max_length=160)
    source_label: str = Field(min_length=1, max_length=160)
    limit: str = Field(min_length=1, max_length=280)
    code_system: str | None = Field(default=None, max_length=80)
    code: str | None = Field(default=None, max_length=80)
    coding_references: list[DiagnosisCodeReference] = Field(default_factory=list)

    @model_validator(mode="after")
    def populate_legacy_coding_reference(self) -> HistoricalDiagnosisRead:
        if self.coding_references:
            return self
        reference = legacy_diagnostic_code_reference(
            system=self.code_system,
            code=self.code,
            label=self.title,
        )
        if reference is not None:
            self.coding_references = [reference]
        return self


class PatientRecordSnapshot(APIModel):
    patient: PatientRead
    latest_vitals: VitalSignRead | None = None
    active_allergies: list[AllergyRead] = Field(default_factory=list)
    active_medications: list[MedicationRead] = Field(default_factory=list)
    active_problems: list[ActiveProblemRead] = Field(default_factory=list)
    historical_diagnoses: list[HistoricalDiagnosisRead] = Field(default_factory=list)
    recent_entries: list[ClinicalEntryRead] = Field(default_factory=list)
