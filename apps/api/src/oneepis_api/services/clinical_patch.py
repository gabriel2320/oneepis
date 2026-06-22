from __future__ import annotations

import uuid
from collections.abc import Callable

from fastapi import HTTPException, status
from pydantic import ValidationError
from sqlalchemy.orm import Session

from oneepis_api.models.clinical_record import ClinicalEntry, ClinicalEvent
from oneepis_api.schemas.clinical_record import (
    ClinicalEntryCreate,
    ClinicalEventCreate,
    ClinicalPatch,
    ConfirmClinicalPatchRequest,
    ConfirmClinicalPatchResponse,
)
from oneepis_api.services.audit import audit_snapshot, record_audit_event


def confirm_clinical_patch(
    *,
    session: Session,
    patient_id: uuid.UUID,
    payload: ConfirmClinicalPatchRequest,
    actor: str,
    validate_encounter: Callable[[uuid.UUID | None], None],
) -> ConfirmClinicalPatchResponse:
    if payload.decision == "rejected":
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
        session.commit()
        return ConfirmClinicalPatchResponse(
            decision="rejected",
            applies_changes=False,
            message="Propuesta rechazada y auditada. No se aplicaron cambios a la ficha.",
        )

    if payload.patch.target == "evolution":
        return _accept_evolution_patch(
            session=session,
            patient_id=patient_id,
            payload=payload,
            actor=actor,
            validate_encounter=validate_encounter,
        )
    if payload.patch.target == "clinical_event":
        return _accept_clinical_event_patch(
            session=session,
            patient_id=patient_id,
            payload=payload,
            actor=actor,
            validate_encounter=validate_encounter,
        )

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
    session.commit()
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail="ClinicalPatch target is not supported yet",
    )


def _accept_evolution_patch(
    *,
    session: Session,
    patient_id: uuid.UUID,
    payload: ConfirmClinicalPatchRequest,
    actor: str,
    validate_encounter: Callable[[uuid.UUID | None], None],
) -> ConfirmClinicalPatchResponse:
    entry_payload = _clinical_entry_create_from_patch(payload.patch)
    validate_encounter(entry_payload.encounter_id)
    entry_data = entry_payload.model_dump()
    entry_data["created_by"] = actor
    entry_data["extra_data"] = {
        **entry_data.get("extra_data", {}),
        "clinical_patch_id": payload.patch.patch_id,
        "confirmed_from_patch": True,
        "human_reviewed": True,
        "human_reviewed_by": actor,
        "human_review_note": payload.note,
    }
    entry = ClinicalEntry(patient_id=patient_id, **entry_data)
    session.add(entry)
    session.flush()
    _audit_patch_acceptance(
        session=session,
        patient_id=patient_id,
        payload=payload,
        actor=actor,
        entity_type="clinical_entry",
        entity_id=entry.id,
        after_model=entry,
    )
    session.commit()
    session.refresh(entry)
    return ConfirmClinicalPatchResponse(
        decision="accepted",
        applies_changes=True,
        clinical_entry=entry,
        message="Propuesta aceptada por humano y guardada como borrador de evolucion.",
    )


def _accept_clinical_event_patch(
    *,
    session: Session,
    patient_id: uuid.UUID,
    payload: ConfirmClinicalPatchRequest,
    actor: str,
    validate_encounter: Callable[[uuid.UUID | None], None],
) -> ConfirmClinicalPatchResponse:
    event_payload = _clinical_event_create_from_patch(payload.patch)
    validate_encounter(event_payload.encounter_id)
    event_data = event_payload.model_dump()
    event_data["created_by"] = actor
    event_data["payload"] = {
        **event_data.get("payload", {}),
        "clinical_patch_id": payload.patch.patch_id,
        "confirmed_from_patch": True,
        "human_reviewed": True,
        "human_reviewed_by": actor,
        "human_review_note": payload.note,
    }
    event = ClinicalEvent(patient_id=patient_id, **event_data)
    session.add(event)
    session.flush()
    _audit_patch_acceptance(
        session=session,
        patient_id=patient_id,
        payload=payload,
        actor=actor,
        entity_type="clinical_event",
        entity_id=event.id,
        after_model=event,
    )
    session.commit()
    session.refresh(event)
    return ConfirmClinicalPatchResponse(
        decision="accepted",
        applies_changes=True,
        clinical_event=event,
        message="Propuesta aceptada por humano y registrada como evento clinico.",
    )


def _audit_patch_acceptance(
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


def _clinical_event_create_from_patch(patch: ClinicalPatch) -> ClinicalEventCreate:
    values = _patch_values(patch)
    allowed_fields = {
        "encounter_id",
        "event_type",
        "occurred_at",
        "summary",
        "source_type",
        "source_ref",
        "payload",
    }
    return _validate_patch_payload(ClinicalEventCreate, values, allowed_fields)


def _clinical_entry_create_from_patch(patch: ClinicalPatch) -> ClinicalEntryCreate:
    values = _patch_values(patch)
    allowed_fields = {
        "encounter_id",
        "kind",
        "status",
        "occurred_at",
        "title",
        "subjective",
        "objective",
        "assessment",
        "plan",
        "tags",
        "extra_data",
    }
    return _validate_patch_payload(ClinicalEntryCreate, values, allowed_fields)


def _patch_values(patch: ClinicalPatch) -> dict[str, object]:
    return {
        operation.path.lstrip("/"): operation.value
        for operation in patch.operations
        if operation.op in {"add", "replace"}
    }


def _validate_patch_payload(
    schema: type[ClinicalEntryCreate] | type[ClinicalEventCreate],
    values: dict[str, object],
    allowed_fields: set[str],
) -> ClinicalEntryCreate | ClinicalEventCreate:
    payload = {key: value for key, value in values.items() if key in allowed_fields}
    try:
        return schema.model_validate(payload)
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=exc.errors(),
        ) from exc
