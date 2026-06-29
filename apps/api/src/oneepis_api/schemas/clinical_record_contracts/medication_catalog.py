from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import Field

from oneepis_api.models.medication_catalog import (
    MedicationCatalogStatus,
    MedicationDoseSeverity,
    MedicationSourceReviewStatus,
    MedicationSourceSystem,
)
from oneepis_api.schemas.clinical_record_contracts.longitudinal import MedicationRead
from oneepis_api.schemas.common import APIModel


class MedicationSourceReference(APIModel):
    source_system: MedicationSourceSystem
    source_label: str = Field(max_length=160)
    source_url: str | None = Field(default=None, max_length=400)
    external_id: str | None = Field(default=None, max_length=120)
    source_version: str | None = Field(default=None, max_length=80)
    retrieved_at: datetime | None = None
    reviewed_at: datetime | None = None
    review_status: MedicationSourceReviewStatus = MedicationSourceReviewStatus.DRAFT


class MedicationDoseRuleRead(MedicationSourceReference):
    id: uuid.UUID
    catalog_item_id: uuid.UUID
    population: str = Field(max_length=80)
    route: str | None = Field(default=None, max_length=80)
    unit: str | None = Field(default=None, max_length=40)
    min_value: Decimal | None = None
    max_value: Decimal | None = None
    frequency_text: str | None = Field(default=None, max_length=160)
    usual_dose_text: str | None = Field(default=None, max_length=280)
    avoid_dose_text: str | None = Field(default=None, max_length=280)
    severity: MedicationDoseSeverity = MedicationDoseSeverity.WARNING
    created_at: datetime
    updated_at: datetime


class MedicationClinicalUse(APIModel):
    indication: str = Field(max_length=200)
    population: str | None = Field(default=None, max_length=80)
    notes: str | None = Field(default=None, max_length=280)


class MedicationInteractionAlert(APIModel):
    substance: str = Field(max_length=160)
    effect: str = Field(max_length=280)
    recommendation: str | None = Field(default=None, max_length=280)
    severity: MedicationDoseSeverity = MedicationDoseSeverity.WARNING


class MedicationSafetyAlert(APIModel):
    title: str = Field(max_length=160)
    description: str = Field(max_length=320)
    action: str | None = Field(default=None, max_length=280)
    severity: MedicationDoseSeverity = MedicationDoseSeverity.WARNING


class MedicationCatalogItemRead(MedicationSourceReference):
    id: uuid.UUID
    display_name: str = Field(max_length=160)
    generic_name: str = Field(max_length=160)
    form: str | None = Field(default=None, max_length=80)
    strength: str | None = Field(default=None, max_length=80)
    route: str | None = Field(default=None, max_length=80)
    status: MedicationCatalogStatus = MedicationCatalogStatus.AVAILABLE
    tags: list[str] = Field(default_factory=list)
    clinical_uses: list[MedicationClinicalUse] = Field(default_factory=list)
    administration_routes: list[str] = Field(default_factory=list)
    interaction_alerts: list[MedicationInteractionAlert] = Field(default_factory=list)
    safety_alerts: list[MedicationSafetyAlert] = Field(default_factory=list)
    monitoring_notes: list[str] = Field(default_factory=list)
    dose_rules: list[MedicationDoseRuleRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class MedicationDoseWarning(APIModel):
    severity: MedicationDoseSeverity
    message: str
    requires_override: bool = False
    rule_id: uuid.UUID | None = None
    source: MedicationSourceReference | None = None


class MedicationDraftValidationRequest(APIModel):
    catalog_item_id: uuid.UUID | None = None
    name: str = Field(min_length=1, max_length=160)
    dose: str | None = Field(default=None, max_length=120)
    route: str | None = Field(default=None, max_length=80)
    frequency: str | None = Field(default=None, max_length=120)


class MedicationDraftValidationResponse(APIModel):
    warnings: list[MedicationDoseWarning] = Field(default_factory=list)
    blocking: bool = False
    limitations: list[str] = Field(default_factory=list)
    source_refs: list[MedicationSourceReference] = Field(default_factory=list)
    normalized_dose: dict[str, Any] = Field(default_factory=dict)
    applies_changes: bool = False


class MedicationDraftingContext(APIModel):
    active_medications: list[MedicationRead] = Field(default_factory=list)
    recent_medications: list[MedicationRead] = Field(default_factory=list)
    previous_day_indication_texts: list[str] = Field(default_factory=list)
    suggested_catalog_items: list[MedicationCatalogItemRead] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    applies_changes: bool = False
