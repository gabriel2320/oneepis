from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import select

from oneepis_api.api.deps import VitalSignActorDep
from oneepis_api.models.clinical_record import RecordStatus
from oneepis_api.models.vital_sign import VitalSign
from oneepis_api.schemas.clinical_record import VitalSignCreate, VitalSignRead, VitalSignUpdate
from oneepis_api.services.audit import audit_snapshot, changed_field_snapshots, record_audit_event

from .patient_shared import (
    PATIENT_ROUTER_OPTIONS,
    LimitQuery,
    OffsetQuery,
    SessionDep,
    apply_update,
    require_patient,
    require_patient_child,
)

router = APIRouter(**PATIENT_ROUTER_OPTIONS)

@router.get("/{patient_id}/vital-signs", response_model=list[VitalSignRead])
def list_vital_signs(
    patient_id: uuid.UUID,
    session: SessionDep,
    limit: LimitQuery = 50,
    offset: OffsetQuery = 0,
) -> list[VitalSign]:
    require_patient(session, patient_id)
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
    _validate_vital_status_input(payload.status)
    vital = VitalSign(patient_id=patient_id, **payload.model_dump())
    session.add(vital)
    session.flush()
    record_audit_event(
        session,
        action="vital_sign.created",
        entity_type="vital_sign",
        entity_id=vital.id,
        actor_id=actor,
        metadata={"patient_id": str(patient_id), "measured_at": vital.measured_at.isoformat()},
        after=audit_snapshot(vital),
    )
    session.commit()
    session.refresh(vital)
    return vital


@router.get("/{patient_id}/vital-signs/{vital_sign_id}", response_model=VitalSignRead)
def get_vital_sign(
    patient_id: uuid.UUID,
    vital_sign_id: uuid.UUID,
    session: SessionDep,
) -> VitalSign:
    require_patient(session, patient_id)
    return require_patient_child(
        session,
        VitalSign,
        vital_sign_id,
        patient_id,
        "Vital sign not found",
    )


@router.patch(
    "/{patient_id}/vital-signs/{vital_sign_id}",
    response_model=VitalSignRead,
    responses={
        status.HTTP_409_CONFLICT: {
            "description": "Entered-in-error vital signs cannot be edited",
        },
    },
)
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
    _validate_vital_editable(vital)
    if "status" in payload.model_dump(exclude_unset=True):
        _validate_vital_status_input(payload.status)
    update_fields = sorted(payload.model_dump(exclude_unset=True).keys())
    before = audit_snapshot(vital, update_fields)
    fields = apply_update(vital, payload)
    before_changed, after_changed = changed_field_snapshots(
        before=before,
        after_model=vital,
        fields=fields,
    )
    record_audit_event(
        session,
        action="vital_sign.updated",
        entity_type="vital_sign",
        entity_id=vital.id,
        actor_id=actor,
        metadata={"patient_id": str(patient_id), "fields": fields},
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
    if vital.status == RecordStatus.ENTERED_IN_ERROR:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    before = audit_snapshot(vital, ["status"])
    vital.status = RecordStatus.ENTERED_IN_ERROR
    after = audit_snapshot(vital, ["status"])
    record_audit_event(
        session,
        action="vital_sign.deleted",
        entity_type="vital_sign",
        entity_id=vital.id,
        actor_id=actor,
        metadata={"patient_id": str(patient_id), "measured_at": vital.measured_at.isoformat()},
        before=before,
        after=after,
    )
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _validate_vital_editable(vital: VitalSign) -> None:
    if vital.status == RecordStatus.ENTERED_IN_ERROR:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Entered-in-error vital signs cannot be edited",
        )


def _validate_vital_status_input(record_status: RecordStatus | None) -> None:
    if record_status == RecordStatus.ENTERED_IN_ERROR:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Use DELETE to mark a vital sign as entered_in_error",
        )
