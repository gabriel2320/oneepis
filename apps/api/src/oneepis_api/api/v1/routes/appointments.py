from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select

from oneepis_api.api.deps import (
    PatientWriteAccessDep,
    ReadAccessDep,
    require_patient_read_access,
)
from oneepis_api.api.global_index_deps import GlobalClinicalIndexAccessDep
from oneepis_api.models.clinical_record import ClinicalAppointment
from oneepis_api.schemas.clinical_record import (
    ClinicalAppointmentCreate,
    ClinicalAppointmentRead,
    ClinicalAppointmentUpdate,
)
from oneepis_api.services.audit import (
    audit_snapshot,
    changed_field_snapshots,
    record_audit_event,
    record_read_audit_event,
)
from oneepis_api.services.patient_scope_enforcement import (
    enforce_patient_scope_for_read,
    enforce_patient_scope_for_write,
)

from .patient_shared import (
    LimitQuery,
    OffsetQuery,
    SessionDep,
    SettingsDep,
    apply_update,
    record_patient_scoped_read,
    require_patient,
    require_patient_child,
)

router = APIRouter(tags=["appointments"], dependencies=[Depends(require_patient_read_access)])

DateFromQuery = Annotated[datetime | None, Query()]
DateToQuery = Annotated[datetime | None, Query()]

APPOINTMENT_AUDIT_FIELDS = [
    "ends_at",
    "patient_id",
    "starts_at",
    "status",
]


def appointment_audit_fields(fields: list[str]) -> list[str]:
    allowed_fields = set(APPOINTMENT_AUDIT_FIELDS)
    return [field for field in fields if field in allowed_fields]


@router.get("/appointments", response_model=list[ClinicalAppointmentRead])
def list_appointments(
    session: SessionDep,
    user: GlobalClinicalIndexAccessDep,
    date_from: DateFromQuery = None,
    date_to: DateToQuery = None,
    limit: LimitQuery = 100,
    offset: OffsetQuery = 0,
) -> list[ClinicalAppointment]:
    statement = select(ClinicalAppointment)
    if date_from is not None:
        statement = statement.where(ClinicalAppointment.starts_at >= date_from)
    if date_to is not None:
        statement = statement.where(ClinicalAppointment.starts_at < date_to)
    statement = statement.order_by(ClinicalAppointment.starts_at.asc()).offset(offset).limit(limit)
    appointments = list(session.scalars(statement))
    record_read_audit_event(
        session,
        action="appointments_index.read",
        entity_type="appointment_index",
        entity_id=None,
        actor_id=user.actor_id,
        metadata={
            "date_from_present": date_from is not None,
            "date_to_present": date_to is not None,
            "limit": limit,
            "offset": offset,
            "result_count": len(appointments),
        },
    )
    session.commit()
    return appointments


@router.get(
    "/patients/{patient_id}/appointments",
    response_model=list[ClinicalAppointmentRead],
)
def list_patient_appointments(
    patient_id: uuid.UUID,
    session: SessionDep,
    user: ReadAccessDep,
    settings: SettingsDep,
    limit: LimitQuery = 50,
    offset: OffsetQuery = 0,
) -> list[ClinicalAppointment]:
    require_patient(session, patient_id)
    enforce_patient_scope_for_read(
        session,
        patient_id=patient_id,
        actor_id=user.actor_id,
        roles=user.roles,
        settings=settings,
    )
    statement = (
        select(ClinicalAppointment)
        .where(ClinicalAppointment.patient_id == patient_id)
        .order_by(ClinicalAppointment.starts_at.desc())
        .offset(offset)
        .limit(limit)
    )
    appointments = list(session.scalars(statement))
    record_patient_scoped_read(
        session,
        patient_id=patient_id,
        actor_id=user.actor_id,
        action="appointments.read",
    )
    return appointments


@router.post(
    "/patients/{patient_id}/appointments",
    response_model=ClinicalAppointmentRead,
    status_code=status.HTTP_201_CREATED,
)
def create_patient_appointment(
    patient_id: uuid.UUID,
    payload: ClinicalAppointmentCreate,
    session: SessionDep,
    user: PatientWriteAccessDep,
    settings: SettingsDep,
) -> ClinicalAppointment:
    require_patient(session, patient_id)
    enforce_patient_scope_for_write(
        session,
        patient_id=patient_id,
        actor_id=user.actor_id,
        roles=user.roles,
        settings=settings,
    )
    appointment = ClinicalAppointment(
        patient_id=patient_id,
        created_by=user.actor_id,
        **payload.model_dump(),
    )
    session.add(appointment)
    session.flush()
    record_audit_event(
        session,
        action="appointment.created",
        entity_type="appointment",
        entity_id=appointment.id,
        actor_id=user.actor_id,
        metadata={"patient_id": str(patient_id), "status": appointment.status.value},
        after=audit_snapshot(appointment, APPOINTMENT_AUDIT_FIELDS),
    )
    session.commit()
    session.refresh(appointment)
    return appointment


@router.get(
    "/patients/{patient_id}/appointments/{appointment_id}",
    response_model=ClinicalAppointmentRead,
)
def get_patient_appointment(
    patient_id: uuid.UUID,
    appointment_id: uuid.UUID,
    session: SessionDep,
    user: ReadAccessDep,
    settings: SettingsDep,
) -> ClinicalAppointment:
    require_patient(session, patient_id)
    enforce_patient_scope_for_read(
        session,
        patient_id=patient_id,
        actor_id=user.actor_id,
        roles=user.roles,
        settings=settings,
    )
    appointment = require_patient_child(
        session,
        ClinicalAppointment,
        appointment_id,
        patient_id,
        "Appointment not found",
    )
    record_patient_scoped_read(
        session,
        patient_id=patient_id,
        actor_id=user.actor_id,
        action="appointment.read",
    )
    return appointment


@router.patch(
    "/patients/{patient_id}/appointments/{appointment_id}",
    response_model=ClinicalAppointmentRead,
)
def update_patient_appointment(
    patient_id: uuid.UUID,
    appointment_id: uuid.UUID,
    payload: ClinicalAppointmentUpdate,
    session: SessionDep,
    user: PatientWriteAccessDep,
    settings: SettingsDep,
) -> ClinicalAppointment:
    require_patient(session, patient_id)
    enforce_patient_scope_for_write(
        session,
        patient_id=patient_id,
        actor_id=user.actor_id,
        roles=user.roles,
        settings=settings,
    )
    appointment = require_patient_child(
        session,
        ClinicalAppointment,
        appointment_id,
        patient_id,
        "Appointment not found",
    )
    update_data = payload.model_dump(exclude_unset=True)
    starts_at = update_data.get("starts_at", appointment.starts_at)
    ends_at = update_data.get("ends_at", appointment.ends_at)
    if ends_at is not None and comparable_datetime(ends_at) <= comparable_datetime(starts_at):
        raise HTTPException(status_code=422, detail="ends_at must be after starts_at")
    update_fields = sorted(update_data.keys())
    before = audit_snapshot(appointment, appointment_audit_fields(update_fields))
    fields = apply_update(appointment, payload)
    audit_fields = appointment_audit_fields(fields)
    before_changed, after_changed = changed_field_snapshots(
        before=before,
        after_model=appointment,
        fields=audit_fields,
    )
    record_audit_event(
        session,
        action="appointment.updated",
        entity_type="appointment",
        entity_id=appointment.id,
        actor_id=user.actor_id,
        metadata={"patient_id": str(patient_id), "fields": fields},
        before=before_changed,
        after=after_changed,
    )
    session.commit()
    session.refresh(appointment)
    return appointment


def comparable_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value
