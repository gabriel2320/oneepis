from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import Field

from oneepis_api.models.clinical_record import (
    AllergySeverity,
    ClinicalEntryKind,
    ClinicalEntryStatus,
    ClinicalEventSourceType,
    ClinicalEventType,
    EncounterStatus,
    EncounterType,
    RecordStatus,
)
from oneepis_api.schemas.common import APIModel


class ClinicalEntryBase(APIModel):
    encounter_id: uuid.UUID | None = None
    kind: ClinicalEntryKind = ClinicalEntryKind.NOTE
    status: ClinicalEntryStatus = ClinicalEntryStatus.DRAFT
    occurred_at: datetime
    title: str = Field(min_length=1, max_length=160)
    subjective: str | None = None
    objective: str | None = None
    assessment: str | None = None
    plan: str | None = None
    tags: list[str] = Field(default_factory=list)
    extra_data: dict[str, Any] = Field(default_factory=dict)
    created_by: str = Field(default="system", max_length=120)


class ClinicalEntryCreate(ClinicalEntryBase):
    pass


class ClinicalEntryUpdate(APIModel):
    encounter_id: uuid.UUID | None = None
    status: ClinicalEntryStatus | None = None
    occurred_at: datetime | None = None
    title: str | None = Field(default=None, min_length=1, max_length=160)
    subjective: str | None = None
    objective: str | None = None
    assessment: str | None = None
    plan: str | None = None
    tags: list[str] | None = None
    extra_data: dict[str, Any] | None = None


class ClinicalEntryRead(ClinicalEntryBase):
    id: uuid.UUID
    patient_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class ClinicalEventBase(APIModel):
    encounter_id: uuid.UUID | None = None
    event_type: ClinicalEventType
    occurred_at: datetime
    summary: str = Field(min_length=1, max_length=280)
    source_type: ClinicalEventSourceType = ClinicalEventSourceType.MANUAL
    source_ref: str | None = Field(default=None, max_length=160)
    payload: dict[str, Any] = Field(default_factory=dict)
    created_by: str = Field(default="system", max_length=120)


class ClinicalEventCreate(ClinicalEventBase):
    pass


class ClinicalEventUpdate(APIModel):
    encounter_id: uuid.UUID | None = None
    event_type: ClinicalEventType | None = None
    occurred_at: datetime | None = None
    summary: str | None = Field(default=None, min_length=1, max_length=280)
    source_type: ClinicalEventSourceType | None = None
    source_ref: str | None = Field(default=None, max_length=160)
    payload: dict[str, Any] | None = None


class ClinicalEventRead(ClinicalEventBase):
    id: uuid.UUID
    patient_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class ClinicalTimelineRead(APIModel):
    events: list[ClinicalEventRead]
    entries: list[ClinicalEntryRead]


class ClinicalEventSource(APIModel):
    clinical_event_id: uuid.UUID
    label: str


class DraftSoapSectionSource(APIModel):
    section: Literal["subjective", "objective", "assessment", "plan"]
    source_type: str
    source_id: uuid.UUID | None = None
    label: str
    reason: str


class DraftSoapFromEventsRequest(APIModel):
    clinical_event_ids: list[uuid.UUID] = Field(min_length=1, max_length=20)
    encounter_id: uuid.UUID | None = None


class DraftSoapFromEventsResponse(APIModel):
    title: str
    subjective: str
    objective: str
    assessment: str
    plan: str
    sources: list[ClinicalEventSource]
    section_sources: list[DraftSoapSectionSource] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    ai_available: bool
    provider: str
    requires_human_confirmation: bool = True


class EventProposalFromEntryRequest(APIModel):
    entry_id: uuid.UUID
    max_proposals: int = Field(default=6, ge=1, le=12)


ClinicalPatchTarget = Literal[
    "clinical_event",
    "evolution",
    "problem",
    "medication",
    "document",
]
ClinicalPatchMode = Literal["draft", "suggestion"]
ClinicalPatchOperationType = Literal["add", "replace", "annotate"]


class ClinicalPatchSource(APIModel):
    source_type: str
    source_id: uuid.UUID | None = None
    label: str


class ClinicalPatchOperation(APIModel):
    op: ClinicalPatchOperationType
    path: str = Field(min_length=1, max_length=120)
    value: Any = None
    reason: str = Field(min_length=1, max_length=320)


class ClinicalPatch(APIModel):
    patch_id: str = Field(min_length=1, max_length=180)
    target: ClinicalPatchTarget
    mode: ClinicalPatchMode = "suggestion"
    operations: list[ClinicalPatchOperation] = Field(min_length=1, max_length=20)
    sources: list[ClinicalPatchSource] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    requires_human_confirmation: bool = True


class ConfirmClinicalPatchRequest(APIModel):
    decision: Literal["accepted", "rejected"]
    patch: ClinicalPatch
    note: str | None = Field(default=None, max_length=600)


class ConfirmClinicalPatchResponse(APIModel):
    decision: Literal["accepted", "rejected"]
    audited: bool = True
    applies_changes: bool
    clinical_event: ClinicalEventRead | None = None
    clinical_entry: ClinicalEntryRead | None = None
    message: str


class EventProposalFromEntry(APIModel):
    proposal_id: str
    event_type: ClinicalEventType
    occurred_at: datetime
    summary: str = Field(min_length=1, max_length=280)
    source_type: ClinicalEventSourceType = ClinicalEventSourceType.CLINICAL_ENTRY
    source_ref: str
    payload: dict[str, Any] = Field(default_factory=dict)
    evidence_label: str
    patch: ClinicalPatch
    requires_human_confirmation: bool = True


class EventProposalsFromEntryResponse(APIModel):
    entry_id: uuid.UUID
    entry_title: str
    proposals: list[EventProposalFromEntry] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    applies_changes: bool = False
    requires_human_confirmation: bool = True


ClinicalIntentType = Literal[
    "summarize_patient",
    "daily_changes",
    "active_problems",
    "timeline",
    "draft_soap",
    "show_sources",
]
ClinicalIntentMode = Literal["read", "draft", "structured_proposal", "human_confirmation"]


class ClinicalIntentRequest(APIModel):
    intent_type: ClinicalIntentType
    mode: ClinicalIntentMode = "read"
    focus: str | None = Field(default=None, max_length=240)
    max_events: int = Field(default=10, ge=1, le=50)


class ClinicalIntentRouteRequest(APIModel):
    text: str = Field(min_length=1, max_length=320)
    max_events: int = Field(default=10, ge=1, le=50)


class ClinicalIntentSource(APIModel):
    source_type: str
    source_id: uuid.UUID | None = None
    label: str


class ClinicalIntentAction(APIModel):
    action_type: Literal[
        "create_event",
        "create_soap_draft",
        "review_sources",
        "add_pending",
        "none",
    ]
    label: str
    action_id: str | None = None
    description: str | None = None
    confirmation_label: str | None = None
    requires_confirmation: bool = False


class ClinicalIntentActionDecisionRequest(APIModel):
    decision: Literal["reviewed", "accepted", "rejected"]
    action_type: Literal[
        "create_event",
        "create_soap_draft",
        "review_sources",
        "add_pending",
        "none",
    ]
    label: str = Field(min_length=1, max_length=240)
    action_id: str | None = Field(default=None, max_length=180)
    description: str | None = Field(default=None, max_length=600)
    requires_confirmation: bool = False
    note: str | None = Field(default=None, max_length=600)


class ClinicalIntentActionDecisionResponse(APIModel):
    decision: Literal["reviewed", "accepted", "rejected"]
    audited: bool = True
    applies_changes: bool = False
    message: str


class ClinicalEvidenceMark(APIModel):
    label: str
    status: Literal["confirmed", "inferred", "missing", "needs_review"]
    detail: str
    source_id: uuid.UUID | None = None


class ClinicalContextSection(APIModel):
    title: str
    items: list[str] = Field(default_factory=list)


class ClinicalProblemContext(APIModel):
    problem_id: uuid.UUID | None = None
    title: str
    status: Literal["structured", "unlinked"]
    evidence: list[ClinicalEvidenceMark] = Field(default_factory=list)
    pending: list[str] = Field(default_factory=list)
    explanations: list[str] = Field(default_factory=list)


class ClinicalChangeSet(APIModel):
    baseline: str | None = None
    new_items: list[str] = Field(default_factory=list)
    rule_findings: list[str] = Field(default_factory=list)
    missing_for_comparison: list[str] = Field(default_factory=list)


ClinicalReviewItemType = Literal[
    "missing_medication_dose",
    "missing_medication_frequency",
    "unstructured_medication_event",
    "unlinked_medication_event",
]


class ClinicalReviewItem(APIModel):
    item_type: ClinicalReviewItemType
    label: str
    detail: str
    severity: Literal["info", "warning", "critical"] = "warning"
    source_type: str
    source_id: uuid.UUID | None = None
    suggested_action: str
    decision_status: Literal["pending", "accepted", "rejected"] = "pending"
    decision_actor_id: str | None = None
    decision_at: datetime | None = None
    decision_audit_event_id: uuid.UUID | None = None


class ClinicalReviewItemDecisionRequest(APIModel):
    decision: Literal["accepted", "rejected"]
    item_type: ClinicalReviewItemType
    label: str = Field(min_length=1, max_length=240)
    detail: str = Field(min_length=1, max_length=600)
    source_type: str = Field(min_length=1, max_length=80)
    source_id: uuid.UUID | None = None
    note: str | None = Field(default=None, max_length=600)


class ClinicalReviewItemDecisionResponse(APIModel):
    decision: Literal["accepted", "rejected"]
    audited: bool = True
    message: str


class ClinicalIntentResponse(APIModel):
    intent_type: str
    mode: str
    clinical_answer: str
    sources: list[ClinicalIntentSource]
    certainty: Literal["high", "moderate", "low"]
    missing_data: list[str] = Field(default_factory=list)
    proposed_actions: list[ClinicalIntentAction] = Field(default_factory=list)
    evidence_marks: list[ClinicalEvidenceMark] = Field(default_factory=list)
    context_sections: list[ClinicalContextSection] = Field(default_factory=list)
    problem_contexts: list[ClinicalProblemContext] = Field(default_factory=list)
    change_set: ClinicalChangeSet | None = None
    review_items: list[ClinicalReviewItem] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    requires_human_confirmation: bool = False


class ClinicalIntentRouteResponse(APIModel):
    recognized: bool
    original_text: str
    intent_type: ClinicalIntentType | None = None
    mode: ClinicalIntentMode = "read"
    confidence: Literal["high", "moderate", "low"]
    explanation: str
    suggested_actions: list[ClinicalIntentAction] = Field(default_factory=list)
    fallback_options: list[ClinicalIntentAction] = Field(default_factory=list)


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
    name: str = Field(min_length=1, max_length=160)
    dose: str | None = Field(default=None, max_length=120)
    route: str | None = Field(default=None, max_length=80)
    frequency: str | None = Field(default=None, max_length=120)
    status: RecordStatus = RecordStatus.ACTIVE
    started_on: date | None = None
    ended_on: date | None = None


class MedicationCreate(MedicationBase):
    pass


class MedicationUpdate(APIModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    dose: str | None = Field(default=None, max_length=120)
    route: str | None = Field(default=None, max_length=80)
    frequency: str | None = Field(default=None, max_length=120)
    status: RecordStatus | None = None
    started_on: date | None = None
    ended_on: date | None = None


class MedicationRead(MedicationBase):
    id: uuid.UUID
    patient_id: uuid.UUID
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
