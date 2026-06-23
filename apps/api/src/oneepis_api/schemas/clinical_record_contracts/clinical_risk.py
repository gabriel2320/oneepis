from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import Field

from oneepis_api.models.clinical_record import RecordStatus
from oneepis_api.models.clinical_risk import (
    ClinicalRiskSeverity,
    ClinicalRiskSourceKind,
    ClinicalRiskType,
)
from oneepis_api.schemas.common import APIModel


class ClinicalRiskBase(APIModel):
    encounter_id: uuid.UUID | None = None
    risk_type: ClinicalRiskType
    severity: ClinicalRiskSeverity = ClinicalRiskSeverity.UNKNOWN
    source_kind: ClinicalRiskSourceKind = ClinicalRiskSourceKind.MANUAL
    source_ref: str | None = Field(default=None, max_length=160)
    reason: str = Field(min_length=1, max_length=320)
    human_action: str | None = Field(default=None, max_length=320)
    reviewed_at: datetime | None = None


class ClinicalRiskCreate(ClinicalRiskBase):
    pass


class ClinicalRiskUpdate(APIModel):
    encounter_id: uuid.UUID | None = None
    risk_type: ClinicalRiskType | None = None
    severity: ClinicalRiskSeverity | None = None
    status: RecordStatus | None = None
    source_kind: ClinicalRiskSourceKind | None = None
    source_ref: str | None = Field(default=None, max_length=160)
    reason: str | None = Field(default=None, min_length=1, max_length=320)
    human_action: str | None = Field(default=None, max_length=320)
    reviewed_at: datetime | None = None


class ClinicalRiskRead(ClinicalRiskBase):
    id: uuid.UUID
    patient_id: uuid.UUID
    status: RecordStatus
    created_by: str
    created_at: datetime
    updated_at: datetime
