from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import select

from oneepis_api.api.deps import PatientReadActorDep, VitalSignActorDep
from oneepis_api.models.clinical_record import RecordStatus, VitalSign
from oneepis_api.schemas.clinical_record import VitalSignCreate, VitalSignRead, VitalSignUpdate
from oneepis_api.services.audit import audit_snapshot, changed_field_snapshots, record_audit_event

from .patient_shared import (
    PATIENT_ROUTER_OPTIONS,
    LimitQuery,
    OffsetQuery,
    SessionDep,
    apply_update,
    record_patient_scoped_read,
    require_patient,
    require_patient_child,
)

router = APIRouter(**PATIENT_ROUTER_OPTIONS)
VITAL_SIGN_AUDIT_FIELDS = ["patient_id", "measured_at", "status"]


@router.get("/{patient_id}/vital-signs", response_model=list[VitalSignRead])
def list_vital_signs(
    patient_id: uuid.UUID,
    session: SessionDep,
    actor: PatientReadActorDep,
    limit: LimitQuery = 50,
    offset: OffsetQuery = 0,
) -> list[VitalSign]:
    require_patient(session, patient_id)
    record_patient_scoped_read(
        session,
        patient_id=patient_id,
        actor_id=actor,
        action="vital_signs.read",
    )
    statement = (
        select(VitalSign)
        .where(
            VitalSign.patient_id == patient_id,
            VitalSign.status != RecordStatus.ENTERED_IN_ERROR,
        )
        .order_by(VitalSign.measured_at.desc())
        .offset(offset)
        .limit(limit)
    )
    return list(session.scalars(statement))


@router.post(
    "/{patient_id}/vital-signs",
    response_model=VitalSignRead,
    status_code=status.HTTP_201_CREATED,
)
def create_vital_sign(
    patient_id: uuid.UUID,
    payload: VitalSignCreate,
    session: SessionDep,
    actor: VitalSignActorDep,
) -> VitalSign:
    require_patient(session, patient_id)
    vital = VitalSign(patient_id=patient_id, **payload.model_dump())
    _reject_entered_in_error_status(vital.status)
    session.add(vital)
    session.flush()
    record_audit_event(
        session,
        action="vital_sign.created",
        entity_type="vital_sign",
        entity_id=vital.id,
        actor_id=actor,
        metadata=_vital_sign_audit_metadata(vital),
        after=audit_snapshot(vital, VITAL_SIGN_AUDIT_FIELDS),
    )
    session.commit()
    session.refresh(vital)
    return vital


@router.get("/{patient_id}/vital-signs/{vital_sign_id}", response_model=VitalSignRead)
def get_vital_sign(
    patient_id: uuid.UUID,
    vital_sign_id: uuid.UUID,
    session: SessionDep,
    actor: PatientReadActorDep,
) -> VitalSign:
    require_patient(session, patient_id)
    vital = require_patient_child(
        session,
        VitalSign,
        vital_sign_id,
        patient_id,
        "Vital sign not found",
    )
    if _vital_sign_is_hidden(vital):
        raise _vital_sign_not_found()
    record_patient_scoped_read(
        session,
        patient_id=patient_id,
        actor_id=actor,
        action="vital_sign.read",
    )
    return vital


@router.patch("/{patient_id}/vital-signs/{vital_sign_id}", response_model=VitalSignRead)
def update_vital_sign(
    patient_id: uuid.UUID,
    vital_sign_id: uuid.UUID,
    payload: VitalSignUpdate,
    session: SessionDep,
    actor: VitalSignActorDep,
) -> VitalSign:
    require_patient(session, patient_id)
    vital = require_patient_child(
        session,
        VitalSign,
        vital_sign_id,
        patient_id,
        "Vital sign not found",
    )
    if _vital_sign_is_hidden(vital):
        raise _vital_sign_not_found()
    _reject_entered_in_error_status(payload.status)
    update_fields = sorted(payload.model_dump(exclude_unset=True).keys())
    audit_fields = _vital_sign_audit_fields(update_fields)
    before = audit_snapshot(vital, audit_fields) if audit_fields else {}
    fields = apply_update(vital, payload)
    changed_audit_fields = _vital_sign_audit_fields(fields)
    if changed_audit_fields:
        before_changed, after_changed = changed_field_snapshots(
            before=before,
            after_model=vital,
            fields=changed_audit_fields,
        )
    else:
        before_changed, after_changed = {}, {}
    record_audit_event(
        session,
        action="vital_sign.updated",
        entity_type="vital_sign",
        entity_id=vital.id,
        actor_id=actor,
        metadata=_vital_sign_audit_metadata(vital, fields),
        before=before_changed,
        after=after_changed,
    )
    session.commit()
    session.refresh(vital)
    return vital


@router.delete("/{patient_id}/vital-signs/{vital_sign_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vital_sign(
    patient_id: uuid.UUID,
    vital_sign_id: uuid.UUID,
    session: SessionDep,
    actor: VitalSignActorDep,
) -> Response:
    require_patient(session, patient_id)
    vital = require_patient_child(
        session,
        VitalSign,
        vital_sign_id,
        patient_id,
        "Vital sign not found",
    )
    if _vital_sign_is_hidden(vital):
        raise _vital_sign_not_found()
    record_audit_event(
        session,
        action="vital_sign.entered_in_error",
        entity_type="vital_sign",
        entity_id=vital.id,
        actor_id=actor,
        metadata={**_vital_sign_audit_metadata(vital), "reason_code": "entered_in_error"},
        before=audit_snapshot(vital, ["status"]),
        after={"status": RecordStatus.ENTERED_IN_ERROR.value},
    )
    vital.status = RecordStatus.ENTERED_IN_ERROR
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _vital_sign_audit_fields(fields: list[str]) -> list[str]:
    return [field for field in fields if field in VITAL_SIGN_AUDIT_FIELDS]


def _vital_sign_is_hidden(vital: VitalSign) -> bool:
    return vital.status == RecordStatus.ENTERED_IN_ERROR


def _reject_entered_in_error_status(status_value: RecordStatus | None) -> None:
    if status_value == RecordStatus.ENTERED_IN_ERROR:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Use DELETE to mark a vital sign as entered in error",
        )


def _vital_sign_not_found() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vital sign not found")


def _vital_sign_audit_metadata(
    vital: VitalSign,
    fields: list[str] | None = None,
) -> dict[str, object]:
    metadata: dict[str, object] = {
        "patient_id": str(vital.patient_id),
        "measured_at": vital.measured_at.isoformat(),
    }
    if fields is not None:
        metadata["fields"] = fields
    return metadata
