from __future__ import annotations

import uuid

from fastapi import APIRouter, Response, status
from sqlalchemy import select

from oneepis_api.api.deps import EncounterActorDep
from oneepis_api.models.clinical_record import ClinicalEncounter, EncounterStatus
from oneepis_api.schemas.clinical_record import (
    ClinicalEncounterCreate,
    ClinicalEncounterRead,
    ClinicalEncounterUpdate,
)
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

@router.get("/{patient_id}/encounters", response_model=list[ClinicalEncounterRead])
def list_clinical_encounters(
    patient_id: uuid.UUID,
    session: SessionDep,
    limit: LimitQuery = 50,
    offset: OffsetQuery = 0,
) -> list[ClinicalEncounter]:
    require_patient(session, patient_id)
    statement = (
        select(ClinicalEncounter)
        .where(ClinicalEncounter.patient_id == patient_id)
        .order_by(ClinicalEncounter.started_at.desc())
        .offset(offset)
        .limit(limit)
    )
    return list(session.scalars(statement))


@router.post(
    "/{patient_id}/encounters",
    response_model=ClinicalEncounterRead,
    status_code=status.HTTP_201_CREATED,
)
def create_clinical_encounter(
    patient_id: uuid.UUID,
    payload: ClinicalEncounterCreate,
    session: SessionDep,
    actor: EncounterActorDep,
) -> ClinicalEncounter:
    require_patient(session, patient_id)
    encounter = ClinicalEncounter(patient_id=patient_id, **payload.model_dump())
    session.add(encounter)
    session.flush()
    record_audit_event(
        session,
        action="encounter.created",
        entity_type="encounter",
        entity_id=encounter.id,
        actor_id=actor,
        metadata={
            "patient_id": str(patient_id),
            "type": encounter.type.value,
            "status": encounter.status.value,
        },
        after=audit_snapshot(encounter),
    )
    session.commit()
    session.refresh(encounter)
    return encounter


@router.get("/{patient_id}/encounters/{encounter_id}", response_model=ClinicalEncounterRead)
def get_clinical_encounter(
    patient_id: uuid.UUID,
    encounter_id: uuid.UUID,
    session: SessionDep,
) -> ClinicalEncounter:
    require_patient(session, patient_id)
    return require_patient_child(
        session,
        ClinicalEncounter,
        encounter_id,
        patient_id,
        "Encounter not found",
    )


@router.patch("/{patient_id}/encounters/{encounter_id}", response_model=ClinicalEncounterRead)
def update_clinical_encounter(
    patient_id: uuid.UUID,
    encounter_id: uuid.UUID,
    payload: ClinicalEncounterUpdate,
    session: SessionDep,
    actor: EncounterActorDep,
) -> ClinicalEncounter:
    require_patient(session, patient_id)
    encounter = require_patient_child(
        session,
        ClinicalEncounter,
        encounter_id,
        patient_id,
        "Encounter not found",
    )
    update_fields = sorted(payload.model_dump(exclude_unset=True).keys())
    before = audit_snapshot(encounter, update_fields)
    fields = apply_update(encounter, payload)
    before_changed, after_changed = changed_field_snapshots(
        before=before,
        after_model=encounter,
        fields=fields,
    )
    record_audit_event(
        session,
        action="encounter.updated",
        entity_type="encounter",
        entity_id=encounter.id,
        actor_id=actor,
        metadata={"patient_id": str(patient_id), "fields": fields},
        before=before_changed,
        after=after_changed,
    )
    session.commit()
    session.refresh(encounter)
    return encounter


@router.delete("/{patient_id}/encounters/{encounter_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_clinical_encounter(
    patient_id: uuid.UUID,
    encounter_id: uuid.UUID,
    session: SessionDep,
    actor: EncounterActorDep,
) -> Response:
    require_patient(session, patient_id)
    encounter = require_patient_child(
        session,
        ClinicalEncounter,
        encounter_id,
        patient_id,
        "Encounter not found",
    )
    before = audit_snapshot(encounter, ["status"])
    encounter.status = EncounterStatus.CANCELLED
    record_audit_event(
        session,
        action="encounter.cancelled",
        entity_type="encounter",
        entity_id=encounter.id,
        actor_id=actor,
        metadata={"patient_id": str(patient_id)},
        before=before,
        after=audit_snapshot(encounter, ["status"]),
    )
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
