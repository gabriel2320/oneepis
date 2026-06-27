from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import Field, field_validator

from oneepis_api.models.clinical_order import ClinicalOrderKind, ClinicalOrderStatus
from oneepis_api.schemas.common import APIModel


class ClinicalOrderBase(APIModel):
    kind: ClinicalOrderKind = ClinicalOrderKind.OTHER
    ordered_at: datetime
    title: str = Field(min_length=1, max_length=160)
    order_text: str = Field(min_length=1, max_length=4000)
    rationale: str | None = Field(default=None, max_length=2000)


class ClinicalOrderCreate(ClinicalOrderBase):
    encounter_id: uuid.UUID


class ClinicalOrderUpdate(APIModel):
    kind: ClinicalOrderKind | None = None
    ordered_at: datetime | None = None
    title: str | None = Field(default=None, min_length=1, max_length=160)
    order_text: str | None = Field(default=None, min_length=1, max_length=4000)
    rationale: str | None = Field(default=None, max_length=2000)
    status: ClinicalOrderStatus | None = None

    @field_validator("status")
    @classmethod
    def validate_terminal_status(
        cls,
        value: ClinicalOrderStatus | None,
    ) -> ClinicalOrderStatus | None:
        if value is None or value == ClinicalOrderStatus.DRAFT:
            return value
        if value in {ClinicalOrderStatus.CANCELLED, ClinicalOrderStatus.ENTERED_IN_ERROR}:
            return value
        raise ValueError(
            "Clinical order status updates only allow draft, cancelled or entered_in_error",
        )


class ClinicalOrderRead(ClinicalOrderBase):
    id: uuid.UUID
    patient_id: uuid.UUID
    encounter_id: uuid.UUID
    status: ClinicalOrderStatus
    created_by: str
    created_at: datetime
    updated_at: datetime
