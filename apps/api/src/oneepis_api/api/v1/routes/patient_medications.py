from __future__ import annotations

import uuid

from fastapi import APIRouter, Response, status
from sqlalchemy import select

from oneepis_api.api.deps import MedicationActorDep
from oneepis_api.models.clinical_record import Medication, RecordStatus
from oneepis_api.schemas.clinical_record import MedicationCreate, MedicationRead, MedicationUpdate
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

@router.get("/{patient_id}/medications", response_model=list[MedicationRead])
def list_medications(
    patient_id: uuid.UUID,
    session: SessionDep,
    limit: LimitQuery = 50,
    offset: OffsetQuery = 0,
) -> list[Medication]:
    require_patient(session, patient_id)
    statement = (
        select(Medication)
        .where(Medication.patient_id == patient_id)
        .order_by(Medication.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    return list(session.scalars(statement))


@router.post(
    "/{patient_id}/medications",
    response_model=MedicationRead,
    status_code=status.HTTP_201_CREATED,
)
def create_medication(
    patient_id: uuid.UUID,
    payload: MedicationCreate,
    session: SessionDep,
    actor: MedicationActorDep,
) -> Medication:
    require_patient(session, patient_id)
    medication = Medication(patient_id=patient_id, **payload.model_dump())
    session.add(medication)
    session.flush()
    record_audit_event(
        session,
        action="medication.created",
        entity_type="medication",
        entity_id=medication.id,
        actor_id=actor,
        metadata={"patient_id": str(patient_id), "status": medication.status.value},
        after=audit_snapshot(medication),
    )
    session.commit()
    session.refresh(medication)
    return medication


@router.get("/{patient_id}/medications/{medication_id}", response_model=MedicationRead)
def get_medication(
    patient_id: uuid.UUID,
    medication_id: uuid.UUID,
    session: SessionDep,
) -> Medication:
    require_patient(session, patient_id)
    return require_patient_child(
        session,
        Medication,
        medication_id,
        patient_id,
        "Medication not found",
    )


@router.patch("/{patient_id}/medications/{medication_id}", response_model=MedicationRead)
def update_medication(
    patient_id: uuid.UUID,
    medication_id: uuid.UUID,
    payload: MedicationUpdate,
    session: SessionDep,
    actor: MedicationActorDep,
) -> Medication:
    require_patient(session, patient_id)
    medication = require_patient_child(
        session,
        Medication,
        medication_id,
        patient_id,
        "Medication not found",
    )
    update_fields = sorted(payload.model_dump(exclude_unset=True).keys())
    before = audit_snapshot(medication, update_fields)
    fields = apply_update(medication, payload)
    before_changed, after_changed = changed_field_snapshots(
        before=before,
        after_model=medication,
        fields=fields,
    )
    record_audit_event(
        session,
        action="medication.updated",
        entity_type="medication",
        entity_id=medication.id,
        actor_id=actor,
        metadata={"patient_id": str(patient_id), "fields": fields},
        before=before_changed,
        after=after_changed,
    )
    session.commit()
    session.refresh(medication)
    return medication


@router.delete("/{patient_id}/medications/{medication_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_medication(
    patient_id: uuid.UUID,
    medication_id: uuid.UUID,
    session: SessionDep,
    actor: MedicationActorDep,
) -> Response:
    require_patient(session, patient_id)
    medication = require_patient_child(
        session,
        Medication,
        medication_id,
        patient_id,
        "Medication not found",
    )
    before = audit_snapshot(medication, ["status"])
    medication.status = RecordStatus.ENTERED_IN_ERROR
    record_audit_event(
        session,
        action="medication.entered_in_error",
        entity_type="medication",
        entity_id=medication.id,
        actor_id=actor,
        metadata={"patient_id": str(patient_id)},
        before=before,
        after=audit_snapshot(medication, ["status"]),
    )
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
