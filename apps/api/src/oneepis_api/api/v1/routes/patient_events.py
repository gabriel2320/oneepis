from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from oneepis_api.api.deps import AiAccessDep, ClinicalEventActorDep
from oneepis_api.models.clinical_record import ClinicalEntry, ClinicalEvent
from oneepis_api.schemas.clinical_record import (
    ClinicalEventCreate,
    ClinicalEventRead,
    ClinicalEventUpdate,
    ClinicalIntentActionDecisionRequest,
    ClinicalIntentActionDecisionResponse,
    ClinicalIntentRequest,
    ClinicalIntentResponse,
    ClinicalIntentRouteRequest,
    ClinicalIntentRouteResponse,
    ClinicalReviewItemDecisionRequest,
    ClinicalReviewItemDecisionResponse,
    ClinicalTimelineRead,
    DraftSoapFromEventsRequest,
    DraftSoapFromEventsResponse,
)
from oneepis_api.services.ai.provider import get_ai_provider
from oneepis_api.services.audit import audit_snapshot, changed_field_snapshots, record_audit_event
from oneepis_api.services.clinical_context import build_event_context
from oneepis_api.services.clinical_intent import resolve_clinical_intent, route_clinical_intent
from oneepis_api.services.document_drafter import draft_soap_from_events

from .patient_shared import (
    PATIENT_ROUTER_OPTIONS,
    LimitQuery,
    OffsetQuery,
    SessionDep,
    SettingsDep,
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


@router.post(
    "/{patient_id}/ai/draft-soap-from-events",
    response_model=DraftSoapFromEventsResponse,
)
def create_draft_soap_from_events(
    patient_id: uuid.UUID,
    payload: DraftSoapFromEventsRequest,
    session: SessionDep,
    settings: SettingsDep,
    user: AiAccessDep,
) -> DraftSoapFromEventsResponse:
    require_patient(session, patient_id)
    validate_encounter_for_patient(session, patient_id, payload.encounter_id)
    context = build_event_context(session, patient_id, payload.clinical_event_ids)
    found_ids = {event.id for event in context.events}
    missing_ids = set(payload.clinical_event_ids) - found_ids
    if missing_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or more clinical events were not found for this patient",
        )

    provider = get_ai_provider(settings)
    provider_status = provider.status()
    response = draft_soap_from_events(
        context,
        provider=provider_status.provider,
        ai_available=provider_status.available,
    )
    record_audit_event(
        session,
        action="ai.soap_draft.created",
        entity_type="clinical_event",
        entity_id=context.events[0].id if context.events else None,
        actor_id=user.actor_id,
        metadata={
            "patient_id": str(patient_id),
            "clinical_event_ids": [str(event_id) for event_id in payload.clinical_event_ids],
            "provider": response.provider,
            "ai_available": response.ai_available,
            "requires_human_confirmation": response.requires_human_confirmation,
            "section_sources": [
                source.model_dump(mode="json") for source in response.section_sources
            ],
        },
    )
    session.commit()
    return response


@router.post(
    "/{patient_id}/ai/clinical-intent",
    response_model=ClinicalIntentResponse,
)
def create_clinical_intent(
    patient_id: uuid.UUID,
    payload: ClinicalIntentRequest,
    session: SessionDep,
    user: AiAccessDep,
) -> ClinicalIntentResponse:
    require_patient(session, patient_id)
    response = resolve_clinical_intent(session, patient_id, payload)
    record_audit_event(
        session,
        action="ai.clinical_intent.created",
        entity_type="patient",
        entity_id=patient_id,
        actor_id=user.actor_id,
        metadata={
            "patient_id": str(patient_id),
            "intent_type": payload.intent_type,
            "mode": response.mode,
            "source_count": len(response.sources),
            "requires_human_confirmation": response.requires_human_confirmation,
        },
    )
    session.commit()
    return response


@router.post(
    "/{patient_id}/ai/clinical-intent-route",
    response_model=ClinicalIntentRouteResponse,
)
def route_patient_clinical_intent(
    patient_id: uuid.UUID,
    payload: ClinicalIntentRouteRequest,
    session: SessionDep,
    user: AiAccessDep,
) -> ClinicalIntentRouteResponse:
    require_patient(session, patient_id)
    response = route_clinical_intent(payload)
    record_audit_event(
        session,
        action="ai.clinical_intent.routed",
        entity_type="patient",
        entity_id=patient_id,
        actor_id=user.actor_id,
        metadata={
            "patient_id": str(patient_id),
            "recognized": response.recognized,
            "intent_type": response.intent_type,
            "mode": response.mode,
            "confidence": response.confidence,
        },
    )
    session.commit()
    return response


@router.post(
    "/{patient_id}/ai/action-decision",
    response_model=ClinicalIntentActionDecisionResponse,
)
def decide_clinical_intent_action(
    patient_id: uuid.UUID,
    payload: ClinicalIntentActionDecisionRequest,
    session: SessionDep,
    user: AiAccessDep,
) -> ClinicalIntentActionDecisionResponse:
    require_patient(session, patient_id)
    record_audit_event(
        session,
        action="ai.clinical_action.decided",
        entity_type="patient",
        entity_id=patient_id,
        actor_id=user.actor_id,
        metadata={
            "patient_id": str(patient_id),
            "decision": payload.decision,
            "action_type": payload.action_type,
            "action_id": payload.action_id,
            "label": payload.label,
            "description": payload.description,
            "requires_confirmation": payload.requires_confirmation,
            "note": payload.note,
            "applies_changes": False,
        },
    )
    session.commit()
    return ClinicalIntentActionDecisionResponse(
        decision=payload.decision,
        message="Accion propuesta auditada. No se aplicaron cambios automaticos a la ficha.",
    )


@router.post(
    "/{patient_id}/ai/review-item-decision",
    response_model=ClinicalReviewItemDecisionResponse,
)
def decide_clinical_review_item(
    patient_id: uuid.UUID,
    payload: ClinicalReviewItemDecisionRequest,
    session: SessionDep,
    user: AiAccessDep,
) -> ClinicalReviewItemDecisionResponse:
    require_patient(session, patient_id)
    record_audit_event(
        session,
        action="ai.review_item.decided",
        entity_type="patient",
        entity_id=patient_id,
        actor_id=user.actor_id,
        metadata={
            "patient_id": str(patient_id),
            "decision": payload.decision,
            "item_type": payload.item_type,
            "label": payload.label,
            "detail": payload.detail,
            "source_type": payload.source_type,
            "source_id": str(payload.source_id) if payload.source_id else None,
            "note": payload.note,
            "applies_changes": False,
        },
    )
    session.commit()
    return ClinicalReviewItemDecisionResponse(
        decision=payload.decision,
        message="Decision auditada. No se aplicaron cambios automaticos a la ficha.",
    )
