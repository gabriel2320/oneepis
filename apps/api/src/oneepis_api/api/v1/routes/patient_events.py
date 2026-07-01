from __future__ import annotations

import uuid

from fastapi import APIRouter, status
from sqlalchemy import select

from oneepis_api.api.deps import ClinicalEventWriteAccessDep, ReadAccessDep
from oneepis_api.models.clinical_record import (
    ClinicalEntry,
    ClinicalEntryStatus,
    ClinicalEvent,
)
from oneepis_api.schemas.clinical_record import (
    ClinicalEventCreate,
    ClinicalEventRead,
    ClinicalEventUpdate,
    ClinicalTimelineRead,
)
from oneepis_api.services.audit import audit_snapshot, changed_field_snapshots, record_audit_event
from oneepis_api.services.clinical_event_permissions import (
    validate_clinical_event_semantic_write_access,
)
from oneepis_api.services.clinical_event_validation import (
    CLINICAL_EVENT_AUDIT_FIELDS,
    clinical_event_audit_fields,
    validate_clinical_event_source,
    validate_curated_antecedent_payload,
    validate_diagnostic_coding_payload,
)
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
    validate_encounter_for_patient,
)

router = APIRouter(**PATIENT_ROUTER_OPTIONS)


@router.get("/{patient_id}/clinical-events", response_model=list[ClinicalEventRead])
def list_clinical_events(
    patient_id: uuid.UUID,
    session: SessionDep,
    user: ReadAccessDep,
    settings: SettingsDep,
    limit: LimitQuery = 50,
    offset: OffsetQuery = 0,
) -> list[ClinicalEvent]:
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
        action="clinical_events.read",
    )
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
    user: ClinicalEventWriteAccessDep,
    settings: SettingsDep,
) -> ClinicalEvent:
    require_patient(session, patient_id)
    enforce_patient_scope_for_write(
        session,
        patient_id=patient_id,
        actor_id=user.actor_id,
        roles=user.roles,
        settings=settings,
    )
    validate_encounter_for_patient(session, patient_id, payload.encounter_id)
    validate_clinical_event_semantic_write_access(
        user=user,
        current_event_type=None,
        final_event_type=payload.event_type,
        payload=payload.payload,
    )
    validate_clinical_event_source(payload.source_type, payload.source_ref)
    validate_curated_antecedent_payload(payload.payload, payload.event_type)
    validate_diagnostic_coding_payload(payload.payload, payload.summary)
    event_data = payload.model_dump()
    actor = user.actor_id
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
        after=audit_snapshot(event, CLINICAL_EVENT_AUDIT_FIELDS),
    )
    session.commit()
    session.refresh(event)
    return event


@router.get("/{patient_id}/clinical-events/{event_id}", response_model=ClinicalEventRead)
def get_clinical_event(
    patient_id: uuid.UUID,
    event_id: uuid.UUID,
    session: SessionDep,
    user: ReadAccessDep,
    settings: SettingsDep,
) -> ClinicalEvent:
    require_patient(session, patient_id)
    enforce_patient_scope_for_read(
        session,
        patient_id=patient_id,
        actor_id=user.actor_id,
        roles=user.roles,
        settings=settings,
    )
    event = require_patient_child(
        session,
        ClinicalEvent,
        event_id,
        patient_id,
        "Clinical event not found",
    )
    record_patient_scoped_read(
        session,
        patient_id=patient_id,
        actor_id=user.actor_id,
        action="clinical_event.read",
    )
    return event


@router.patch("/{patient_id}/clinical-events/{event_id}", response_model=ClinicalEventRead)
def update_clinical_event(
    patient_id: uuid.UUID,
    event_id: uuid.UUID,
    payload: ClinicalEventUpdate,
    session: SessionDep,
    user: ClinicalEventWriteAccessDep,
    settings: SettingsDep,
) -> ClinicalEvent:
    require_patient(session, patient_id)
    enforce_patient_scope_for_write(
        session,
        patient_id=patient_id,
        actor_id=user.actor_id,
        roles=user.roles,
        settings=settings,
    )
    event = require_patient_child(
        session,
        ClinicalEvent,
        event_id,
        patient_id,
        "Clinical event not found",
    )
    if "encounter_id" in payload.model_dump(exclude_unset=True):
        validate_encounter_for_patient(session, patient_id, payload.encounter_id)
    payload_data = payload.model_dump(exclude_unset=True)
    actor = user.actor_id
    validate_clinical_event_source(
        payload_data.get("source_type", event.source_type),
        payload_data.get("source_ref", event.source_ref),
    )
    final_event_type = payload_data.get("event_type", event.event_type)
    final_payload = payload_data.get("payload", event.payload)
    validate_clinical_event_semantic_write_access(
        user=user,
        current_event_type=event.event_type,
        final_event_type=final_event_type,
        payload=final_payload,
    )
    if "payload" in payload_data and payload_data["payload"] is not None:
        validate_curated_antecedent_payload(payload_data["payload"], final_event_type)
        validate_diagnostic_coding_payload(
            payload_data["payload"],
            payload_data.get("summary", event.summary),
        )
    elif "event_type" in payload_data:
        validate_curated_antecedent_payload(event.payload, final_event_type)
        validate_diagnostic_coding_payload(event.payload, event.summary)
    update_fields = sorted(payload_data.keys())
    before = audit_snapshot(event, clinical_event_audit_fields(update_fields))
    fields = apply_update(event, payload)
    audit_fields = clinical_event_audit_fields(fields)
    before_changed, after_changed = changed_field_snapshots(
        before=before,
        after_model=event,
        fields=audit_fields,
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
    user: ReadAccessDep,
    settings: SettingsDep,
    limit: LimitQuery = 50,
) -> ClinicalTimelineRead:
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
        action="timeline.read",
    )
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
                .where(
                    ClinicalEntry.patient_id == patient_id,
                    ClinicalEntry.status != ClinicalEntryStatus.ENTERED_IN_ERROR,
                )
                .order_by(ClinicalEntry.occurred_at.desc())
                .limit(limit)
            )
        ),
    )
