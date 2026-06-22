from __future__ import annotations

import uuid

from fastapi import APIRouter, status
from sqlalchemy import select

from oneepis_api.api.deps import ClinicalEventActorDep
from oneepis_api.models.clinical_record import ClinicalEntry, ClinicalEvent
from oneepis_api.schemas.clinical_record import (
    ClinicalEventCreate,
    ClinicalEventRead,
    ClinicalEventUpdate,
    ClinicalTimelineRead,
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
    validate_encounter_for_patient,
)

router = APIRouter(**PATIENT_ROUTER_OPTIONS)


@router.get("/{patient_id}/clinical-events", response_model=list[ClinicalEventRead])
def list_clinical_events(
    patient_id: uuid.UUID,
    session: SessionDep,
    limit: LimitQuery = 50,
    offset: OffsetQuery = 0,
) -> list[ClinicalEvent]:
    require_patient(session, patient_id)
    statement = (
        select(ClinicalEvent)
        .where(ClinicalEvent.patient_id == patient_id)
        .order_by(ClinicalEvent.occurred_at.desc())
        .offset(offset)
        .limit(limit)
    )
    return list(session.scalars(statement))


@router.post(
    "/{patient_id}/clinical-events",
    response_model=ClinicalEventRead,
    status_code=status.HTTP_201_CREATED,
)
def create_clinical_event(
    patient_id: uuid.UUID,
    payload: ClinicalEventCreate,
    session: SessionDep,
    actor: ClinicalEventActorDep,
) -> ClinicalEvent:
    require_patient(session, patient_id)
    validate_encounter_for_patient(session, patient_id, payload.encounter_id)
    event_data = payload.model_dump()
    event_data["created_by"] = actor
    event = ClinicalEvent(patient_id=patient_id, **event_data)
    session.add(event)
    session.flush()
    record_audit_event(
        session,
        action="clinical_event.created",
        entity_type="clinical_event",
        entity_id=event.id,
        actor_id=actor,
        metadata={"patient_id": str(patient_id), "event_type": payload.event_type.value},
        after=audit_snapshot(event),
    )
    session.commit()
    session.refresh(event)
    return event


@router.patch("/{patient_id}/clinical-events/{event_id}", response_model=ClinicalEventRead)
def update_clinical_event(
    patient_id: uuid.UUID,
    event_id: uuid.UUID,
    payload: ClinicalEventUpdate,
    session: SessionDep,
    actor: ClinicalEventActorDep,
) -> ClinicalEvent:
    require_patient(session, patient_id)
    event = require_patient_child(
        session,
        ClinicalEvent,
        event_id,
        patient_id,
        "Clinical event not found",
    )
    if "encounter_id" in payload.model_dump(exclude_unset=True):
        validate_encounter_for_patient(session, patient_id, payload.encounter_id)
    update_fields = sorted(payload.model_dump(exclude_unset=True).keys())
    before = audit_snapshot(event, update_fields)
    fields = apply_update(event, payload)
    before_changed, after_changed = changed_field_snapshots(
        before=before,
        after_model=event,
        fields=fields,
    )
    record_audit_event(
        session,
        action="clinical_event.updated",
        entity_type="clinical_event",
        entity_id=event.id,
        actor_id=actor,
        metadata={"patient_id": str(patient_id), "fields": fields},
        before=before_changed,
        after=after_changed,
    )
    session.commit()
    session.refresh(event)
    return event


@router.get("/{patient_id}/timeline", response_model=ClinicalTimelineRead)
def get_clinical_timeline(
    patient_id: uuid.UUID,
    session: SessionDep,
    limit: LimitQuery = 50,
) -> ClinicalTimelineRead:
    require_patient(session, patient_id)
    return ClinicalTimelineRead(
        events=list(
            session.scalars(
                select(ClinicalEvent)
                .where(ClinicalEvent.patient_id == patient_id)
                .order_by(ClinicalEvent.occurred_at.desc())
                .limit(limit)
            )
        ),
        entries=list(
            session.scalars(
                select(ClinicalEntry)
                .where(ClinicalEntry.patient_id == patient_id)
                .order_by(ClinicalEntry.occurred_at.desc())
                .limit(limit)
            )
        ),
    )
