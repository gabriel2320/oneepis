from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from oneepis_api.models.clinical_record import ClinicalEntry, ClinicalEvent
from oneepis_api.schemas.clinical_record import ConfirmClinicalPatchRequest
from oneepis_api.services.audit import audit_snapshot, record_audit_event


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
        metadata={
            "patient_id": str(patient_id),
            "patch_id": payload.patch.patch_id,
            "target": payload.patch.target,
            "note": payload.note,
            "applies_changes": False,
            "requires_human_confirmation": payload.patch.requires_human_confirmation,
        },
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
        metadata={
            "patient_id": str(patient_id),
            "patch_id": payload.patch.patch_id,
            "target": payload.patch.target,
            "operation_count": len(payload.patch.operations),
            "source_count": len(payload.patch.sources),
            "note": payload.note,
            "applies_changes": False,
            "requires_human_confirmation": payload.patch.requires_human_confirmation,
        },
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
        metadata={
            "patient_id": str(patient_id),
            "patch_id": payload.patch.patch_id,
            "target": payload.patch.target,
            "operation_count": len(payload.patch.operations),
            "source_count": len(payload.patch.sources),
            "note": payload.note,
            "applies_changes": True,
            "requires_human_confirmation": payload.patch.requires_human_confirmation,
        },
        after=audit_snapshot(after_model),
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
            "patient_id": str(patient_id),
            "patch_id": payload.patch.patch_id,
            "target": payload.patch.target,
            "operation_count": len(payload.patch.operations),
            "source_count": len(payload.patch.sources),
            "note": payload.note,
            "applies_changes": False,
            "requires_human_confirmation": payload.patch.requires_human_confirmation,
            "reason": reason,
        },
    )
