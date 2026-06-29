from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from oneepis_api.api.deps import ClinicalEventActorDep, PatientReadActorDep
from oneepis_api.models.clinical_record import (
    ClinicalEntry,
    ClinicalEvent,
    ClinicalEventSourceType,
    ClinicalEventType,
)
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
    record_patient_scoped_read,
    require_patient,
    require_patient_child,
    validate_encounter_for_patient,
)

router = APIRouter(**PATIENT_ROUTER_OPTIONS)

CURATED_ANTECEDENT_CATEGORIES = {
    "diagnostico_historico",
    "procedimiento",
    "familiar_social",
    "plan_longitudinal",
}
CURATED_ANTECEDENT_EVENT_TYPES = {
    "diagnostico_historico": ClinicalEventType.DIAGNOSIS,
    "procedimiento": ClinicalEventType.PROCEDURE,
    "familiar_social": ClinicalEventType.CLINICAL_NOTE,
    "plan_longitudinal": ClinicalEventType.CARE_PLAN,
}
CLINICAL_EVENT_AUDIT_FIELDS = [
    "created_by",
    "encounter_id",
    "event_type",
    "occurred_at",
    "patient_id",
    "source_ref",
    "source_type",
]


def validate_clinical_event_source(
    source_type: ClinicalEventSourceType,
    source_ref: str | None,
) -> None:
    if source_type == ClinicalEventSourceType.MANUAL or source_ref:
        return
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail="source_ref is required when source_type is not manual",
    )


def validate_curated_antecedent_payload(
    payload: dict,
    event_type: ClinicalEventType,
) -> None:
    if "antecedent" not in payload:
        return
    antecedent = payload["antecedent"]
    if not isinstance(antecedent, dict):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="payload.antecedent must be an object",
        )

    category = antecedent.get("category")
    source_label = antecedent.get("source_label")
    limit = antecedent.get("limit")
    required_values = (category, source_label, limit)
    if not all(isinstance(value, str) and value.strip() for value in required_values):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="payload.antecedent requires category, source_label and limit",
        )
    if category not in CURATED_ANTECEDENT_CATEGORIES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="payload.antecedent.category is not allowed",
        )
    expected_event_type = CURATED_ANTECEDENT_EVENT_TYPES[category]
    if event_type != expected_event_type:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=(
                "payload.antecedent.category requires event_type "
                f"{expected_event_type.value}"
            ),
        )


def clinical_event_audit_fields(fields: list[str]) -> list[str]:
    allowed_fields = set(CLINICAL_EVENT_AUDIT_FIELDS)
    return [field for field in fields if field in allowed_fields]


@router.get("/{patient_id}/clinical-events", response_model=list[ClinicalEventRead])
def list_clinical_events(
    patient_id: uuid.UUID,
    session: SessionDep,
    actor: PatientReadActorDep,
    limit: LimitQuery = 50,
    offset: OffsetQuery = 0,
) -> list[ClinicalEvent]:
    require_patient(session, patient_id)
    record_patient_scoped_read(
        session,
        patient_id=patient_id,
        actor_id=actor,
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
    actor: ClinicalEventActorDep,
) -> ClinicalEvent:
    require_patient(session, patient_id)
    validate_encounter_for_patient(session, patient_id, payload.encounter_id)
    validate_clinical_event_source(payload.source_type, payload.source_ref)
    validate_curated_antecedent_payload(payload.payload, payload.event_type)
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
    actor: PatientReadActorDep,
) -> ClinicalEvent:
    require_patient(session, patient_id)
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
        actor_id=actor,
        action="clinical_event.read",
    )
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
    payload_data = payload.model_dump(exclude_unset=True)
    validate_clinical_event_source(
        payload_data.get("source_type", event.source_type),
        payload_data.get("source_ref", event.source_ref),
    )
    final_event_type = payload_data.get("event_type", event.event_type)
    if "payload" in payload_data and payload_data["payload"] is not None:
        validate_curated_antecedent_payload(payload_data["payload"], final_event_type)
    elif "event_type" in payload_data:
        validate_curated_antecedent_payload(event.payload, final_event_type)
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
    actor: PatientReadActorDep,
    limit: LimitQuery = 50,
) -> ClinicalTimelineRead:
    require_patient(session, patient_id)
    record_patient_scoped_read(
        session,
        patient_id=patient_id,
        actor_id=actor,
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
                .where(ClinicalEntry.patient_id == patient_id)
                .order_by(ClinicalEntry.occurred_at.desc())
                .limit(limit)
            )
        ),
    )
