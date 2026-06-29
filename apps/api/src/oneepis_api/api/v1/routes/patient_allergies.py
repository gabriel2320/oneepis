from __future__ import annotations

import uuid

from fastapi import APIRouter, Response, status
from sqlalchemy import select

from oneepis_api.api.deps import AllergyActorDep, PatientReadActorDep
from oneepis_api.models.clinical_record import Allergy, RecordStatus
from oneepis_api.schemas.clinical_record import AllergyCreate, AllergyRead, AllergyUpdate
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


ALLERGY_AUDIT_FIELDS = [
    "patient_id",
    "recorded_at",
    "severity",
    "status",
]


def allergy_audit_fields(fields: list[str]) -> list[str]:
    allowed_fields = set(ALLERGY_AUDIT_FIELDS)
    return [field for field in fields if field in allowed_fields]


@router.get("/{patient_id}/allergies", response_model=list[AllergyRead])
def list_allergies(
    patient_id: uuid.UUID,
    session: SessionDep,
    actor: PatientReadActorDep,
    limit: LimitQuery = 50,
    offset: OffsetQuery = 0,
) -> list[Allergy]:
    require_patient(session, patient_id)
    record_patient_scoped_read(
        session,
        patient_id=patient_id,
        actor_id=actor,
        action="allergies.read",
    )
    statement = (
        select(Allergy)
        .where(Allergy.patient_id == patient_id)
        .order_by(Allergy.recorded_at.desc())
        .offset(offset)
        .limit(limit)
    )
    return list(session.scalars(statement))


@router.post(
    "/{patient_id}/allergies",
    response_model=AllergyRead,
    status_code=status.HTTP_201_CREATED,
)
def create_allergy(
    patient_id: uuid.UUID,
    payload: AllergyCreate,
    session: SessionDep,
    actor: AllergyActorDep,
) -> Allergy:
    require_patient(session, patient_id)
    allergy = Allergy(patient_id=patient_id, **payload.model_dump())
    session.add(allergy)
    session.flush()
    record_audit_event(
        session,
        action="allergy.created",
        entity_type="allergy",
        entity_id=allergy.id,
        actor_id=actor,
        metadata={"patient_id": str(patient_id), "severity": allergy.severity.value},
        after=audit_snapshot(allergy, ALLERGY_AUDIT_FIELDS),
    )
    session.commit()
    session.refresh(allergy)
    return allergy


@router.get("/{patient_id}/allergies/{allergy_id}", response_model=AllergyRead)
def get_allergy(
    patient_id: uuid.UUID,
    allergy_id: uuid.UUID,
    session: SessionDep,
    actor: PatientReadActorDep,
) -> Allergy:
    require_patient(session, patient_id)
    allergy = require_patient_child(session, Allergy, allergy_id, patient_id, "Allergy not found")
    record_patient_scoped_read(
        session,
        patient_id=patient_id,
        actor_id=actor,
        action="allergy.read",
    )
    return allergy


@router.patch("/{patient_id}/allergies/{allergy_id}", response_model=AllergyRead)
def update_allergy(
    patient_id: uuid.UUID,
    allergy_id: uuid.UUID,
    payload: AllergyUpdate,
    session: SessionDep,
    actor: AllergyActorDep,
) -> Allergy:
    require_patient(session, patient_id)
    allergy = require_patient_child(session, Allergy, allergy_id, patient_id, "Allergy not found")
    update_fields = sorted(payload.model_dump(exclude_unset=True).keys())
    before = audit_snapshot(allergy, allergy_audit_fields(update_fields))
    fields = apply_update(allergy, payload)
    audit_fields = allergy_audit_fields(fields)
    before_changed, after_changed = changed_field_snapshots(
        before=before,
        after_model=allergy,
        fields=audit_fields,
    )
    record_audit_event(
        session,
        action="allergy.updated",
        entity_type="allergy",
        entity_id=allergy.id,
        actor_id=actor,
        metadata={"patient_id": str(patient_id), "fields": fields},
        before=before_changed,
        after=after_changed,
    )
    session.commit()
    session.refresh(allergy)
    return allergy


@router.delete("/{patient_id}/allergies/{allergy_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_allergy(
    patient_id: uuid.UUID,
    allergy_id: uuid.UUID,
    session: SessionDep,
    actor: AllergyActorDep,
) -> Response:
    require_patient(session, patient_id)
    allergy = require_patient_child(session, Allergy, allergy_id, patient_id, "Allergy not found")
    before = audit_snapshot(allergy, ["status"])
    allergy.status = RecordStatus.ENTERED_IN_ERROR
    record_audit_event(
        session,
        action="allergy.entered_in_error",
        entity_type="allergy",
        entity_id=allergy.id,
        actor_id=actor,
        metadata={"patient_id": str(patient_id)},
        before=before,
        after=audit_snapshot(allergy, ["status"]),
    )
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
