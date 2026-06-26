from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import Field

from oneepis_api.models.clinical_record import EncounterStatus, EncounterType
from oneepis_api.models.patient import CareContext, PatientClinicalStatus, SexAtBirth
from oneepis_api.schemas.common import APIModel

PatientContextScope = Literal["ambulatory", "hospitalization", "emergency", "unknown"]


class PatientContextPatient(APIModel):
    id: uuid.UUID
    first_name: str = Field(min_length=1, max_length=80)
    last_name: str = Field(min_length=1, max_length=80)
    preferred_name: str | None = Field(default=None, max_length=80)
    sex_at_birth: SexAtBirth
    clinical_status: PatientClinicalStatus
    current_care_context: CareContext
    clinical_identifier: str | None = Field(default=None, max_length=64)


class PatientContextEncounter(APIModel):
    id: uuid.UUID
    type: EncounterType
    status: EncounterStatus
    reason: str = Field(min_length=1, max_length=200)
    started_at: datetime
    ended_at: datetime | None = None
    location_label: str | None = Field(default=None, max_length=120)


class PatientContextListItem(APIModel):
    id: uuid.UUID
    label: str = Field(min_length=1, max_length=200)
    summary: str | None = Field(default=None, max_length=320)
    source_type: str = Field(min_length=1, max_length=80)
    source_path: str = Field(min_length=1, max_length=240)
    encounter_id: uuid.UUID | None = None
    encounter_type: EncounterType | None = None


class PatientContextTimelineItem(APIModel):
    item_type: str = Field(min_length=1, max_length=80)
    item_id: uuid.UUID
    occurred_at: datetime
    label: str = Field(min_length=1, max_length=160)
    summary: str = Field(min_length=1, max_length=320)
    source_path: str = Field(min_length=1, max_length=240)
    encounter_id: uuid.UUID | None = None
    encounter_type: EncounterType | None = None


class PatientContextResponse(APIModel):
    patient_id: uuid.UUID
    patient: PatientContextPatient
    derived_care_context: PatientContextScope
    active_encounter: PatientContextEncounter | None = None
    active_hospitalization: PatientContextEncounter | None = None
    recent_ambulatory_encounters: list[PatientContextEncounter] = Field(default_factory=list)
    active_problems: list[PatientContextListItem] = Field(default_factory=list)
    allergies: list[PatientContextListItem] = Field(default_factory=list)
    active_medications: list[PatientContextListItem] = Field(default_factory=list)
    active_risks: list[PatientContextListItem] = Field(default_factory=list)
    recent_labs: list[PatientContextListItem] = Field(default_factory=list)
    timeline: list[PatientContextTimelineItem] = Field(default_factory=list)
    missing_data: list[str] = Field(default_factory=list)
    limits: list[str] = Field(default_factory=list)
    applies_changes: bool = False
