from __future__ import annotations

import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from oneepis_api.api.deps import ReadAccessDep, VitalSignWriteAccessDep
from oneepis_api.models.clinical_record import RecordStatus, VitalSign
from oneepis_api.schemas.clinical_record import VitalSignCreate, VitalSignRead, VitalSignUpdate
from oneepis_api.services.audit import audit_snapshot, changed_field_snapshots, record_audit_event
from oneepis_api.services.patient_scope_enforcement import (
    enforce_patient_scope_for_read,
    enforce_patient_scope_for_write,
)

from .patient_shared import (
    PATIENT_ROUTER_OPTIONS,
    LimitQuery,
    OffsetQuery,
    SessionDep,
    SettingsDep,
    apply_update,
    record_patient_scoped_read,
    require_patient,
    require_patient_child,
)

router = APIRouter(**PATIENT_ROUTER_OPTIONS)
VITAL_SIGN_AUDIT_FIELDS = ["patient_id", "measured_at", "status"]
BeforeMeasuredAtQuery = Annotated[datetime | None, Query(alias="before_measured_at")]


@router.get("/{patient_id}/vital-signs", response_model=list[VitalSignRead])
def list_vital_signs(
    patient_id: uuid.UUID,
    session: SessionDep,
    user: ReadAccessDep,
    settings: SettingsDep,
    limit: LimitQuery = 50,
    offset: OffsetQuery = 0,
    before_measured_at: BeforeMeasuredAtQuery = None,
) -> list[VitalSign]:
    require_patient(session, patient_id)
    enforce_patient_scope_for_read(
        session,
        patient_id=patient_id,
        actor_id=user.actor_id,
        roles=user.roles,
        settings=settings,
    )
    record_patient_scoped_read(
        session,
        patient_id=patient_id,
        actor_id=user.actor_id,
        action="vital_signs.read",
    )
    statement = select(VitalSign).where(
        VitalSign.patient_id == patient_id,
        VitalSign.status != RecordStatus.ENTERED_IN_ERROR,
    )
    if before_measured_at is not None:
        statement = statement.where(VitalSign.measured_at < before_measured_at)
    else:
        statement = statement.offset(offset)
    statement = statement.order_by(VitalSign.measured_at.desc()).limit(limit)
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
    user: VitalSignWriteAccessDep,
    settings: SettingsDep,
) -> VitalSign:
    require_patient(session, patient_id)
    enforce_patient_scope_for_write(
        session,
        patient_id=patient_id,
        actor_id=user.actor_id,
        roles=user.roles,
        settings=settings,
    )
    with _vital_sign_write_transaction(session):
        vital = VitalSign(patient_id=patient_id, **payload.model_dump())
        _reject_entered_in_error_status(vital.status)
        session.add(vital)
        session.flush()
        record_audit_event(
            session,
            action="vital_sign.created",
            entity_type="vital_sign",
            entity_id=vital.id,
            actor_id=user.actor_id,
            metadata=_vital_sign_audit_metadata(vital),
            after=audit_snapshot(vital, VITAL_SIGN_AUDIT_FIELDS),
        )
    session.refresh(vital)
    return vital


@router.get("/{patient_id}/vital-signs/{vital_sign_id}", response_model=VitalSignRead)
def get_vital_sign(
    patient_id: uuid.UUID,
    vital_sign_id: uuid.UUID,
    session: SessionDep,
    user: ReadAccessDep,
    settings: SettingsDep,
) -> VitalSign:
    require_patient(session, patient_id)
    enforce_patient_scope_for_read(
        session,
        patient_id=patient_id,
        actor_id=user.actor_id,
        roles=user.roles,
        settings=settings,
    )
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
        actor_id=user.actor_id,
        action="vital_sign.read",
    )
    return vital


@router.patch("/{patient_id}/vital-signs/{vital_sign_id}", response_model=VitalSignRead)
def update_vital_sign(
    patient_id: uuid.UUID,
    vital_sign_id: uuid.UUID,
    payload: VitalSignUpdate,
    session: SessionDep,
    user: VitalSignWriteAccessDep,
    settings: SettingsDep,
) -> VitalSign:
    require_patient(session, patient_id)
    enforce_patient_scope_for_write(
        session,
        patient_id=patient_id,
        actor_id=user.actor_id,
        roles=user.roles,
        settings=settings,
    )
    with _vital_sign_write_transaction(session):
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
            actor_id=user.actor_id,
            metadata=_vital_sign_audit_metadata(vital, fields),
            before=before_changed,
            after=after_changed,
        )
    session.refresh(vital)
    return vital


@router.delete("/{patient_id}/vital-signs/{vital_sign_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vital_sign(
    patient_id: uuid.UUID,
    vital_sign_id: uuid.UUID,
    session: SessionDep,
    user: VitalSignWriteAccessDep,
    settings: SettingsDep,
) -> Response:
    require_patient(session, patient_id)
    enforce_patient_scope_for_write(
        session,
        patient_id=patient_id,
        actor_id=user.actor_id,
        roles=user.roles,
        settings=settings,
    )
    with _vital_sign_write_transaction(session):
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
            actor_id=user.actor_id,
            metadata={**_vital_sign_audit_metadata(vital), "reason_code": "entered_in_error"},
            before=audit_snapshot(vital, ["status"]),
            after={"status": RecordStatus.ENTERED_IN_ERROR.value},
        )
        vital.status = RecordStatus.ENTERED_IN_ERROR
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _vital_sign_audit_fields(fields: list[str]) -> list[str]:
    return [field for field in fields if field in VITAL_SIGN_AUDIT_FIELDS]


@contextmanager
def _vital_sign_write_transaction(session: Session) -> Iterator[None]:
    if session.in_transaction():
        # Auth/session checks can leave an implicit read transaction open.
        session.rollback()
    with session.begin():
        yield


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
