from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from oneepis_api.models.clinical_record import ClinicalEntry, ClinicalEvent
from oneepis_api.schemas.clinical_record import ConfirmClinicalPatchRequest
from oneepis_api.services.audit import audit_snapshot, record_audit_event

CLINICAL_ENTRY_AUDIT_FIELDS = [
    "created_by",
    "encounter_id",
    "kind",
    "occurred_at",
    "patient_id",
    "status",
]
CLINICAL_EVENT_AUDIT_FIELDS = [
    "created_by",
    "encounter_id",
    "event_type",
    "occurred_at",
    "patient_id",
    "source_ref",
    "source_type",
]


def _text_presence(value: str | None) -> dict[str, int | bool]:
    text = value.strip() if value else ""
    return {"present": bool(text), "length": len(text)}


def _patch_metadata(
    *,
    patient_id: uuid.UUID,
    payload: ConfirmClinicalPatchRequest,
    applies_changes: bool,
) -> dict[str, object]:
    return {
        "patient_id": str(patient_id),
        "patch_id": payload.patch.patch_id,
        "target": payload.patch.target,
        "operation_count": len(payload.patch.operations),
        "source_count": len(payload.patch.sources),
        "note": _text_presence(payload.note),
        "applies_changes": applies_changes,
        "requires_human_confirmation": payload.patch.requires_human_confirmation,
    }


def _patch_after_fields(entity_type: str) -> list[str]:
    if entity_type == "clinical_entry":
        return CLINICAL_ENTRY_AUDIT_FIELDS
    return CLINICAL_EVENT_AUDIT_FIELDS


def record_patch_rejection(
    *,
    session: Session,
    patient_id: uuid.UUID,
    payload: ConfirmClinicalPatchRequest,
    actor: str,
) -> None:
    record_audit_event(
        session,
        action="ai.clinical_patch.rejected",
        entity_type="patient",
        entity_id=patient_id,
        actor_id=actor,
        metadata=_patch_metadata(patient_id=patient_id, payload=payload, applies_changes=False),
    )


def record_patch_unsupported(
    *,
    session: Session,
    patient_id: uuid.UUID,
    payload: ConfirmClinicalPatchRequest,
    actor: str,
) -> None:
    record_audit_event(
        session,
        action="ai.clinical_patch.unsupported",
        entity_type="patient",
        entity_id=patient_id,
        actor_id=actor,
        metadata=_patch_metadata(patient_id=patient_id, payload=payload, applies_changes=False),
    )


def record_patch_acceptance(
    *,
    session: Session,
    patient_id: uuid.UUID,
    payload: ConfirmClinicalPatchRequest,
    actor: str,
    entity_type: str,
    entity_id: uuid.UUID,
    after_model: ClinicalEntry | ClinicalEvent,
) -> None:
    record_audit_event(
        session,
        action="ai.clinical_patch.accepted",
        entity_type=entity_type,
        entity_id=entity_id,
        actor_id=actor,
        metadata=_patch_metadata(patient_id=patient_id, payload=payload, applies_changes=True),
        after=audit_snapshot(after_model, _patch_after_fields(entity_type)),
    )


def record_patch_blocked(
    *,
    session: Session,
    patient_id: uuid.UUID,
    payload: ConfirmClinicalPatchRequest,
    actor: str,
    reason: str,
) -> None:
    record_audit_event(
        session,
        action="ai.clinical_patch.blocked",
        entity_type="patient",
        entity_id=patient_id,
        actor_id=actor,
        metadata={
            **_patch_metadata(patient_id=patient_id, payload=payload, applies_changes=False),
            "reason": reason,
        },
    )
