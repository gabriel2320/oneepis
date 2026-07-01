from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, status

from oneepis_api.api.deps import AiAccessDep
from oneepis_api.models.clinical_record import ClinicalEntry
from oneepis_api.schemas.clinical_record import (
    ClinicalIntentActionDecisionRequest,
    ClinicalIntentActionDecisionResponse,
    ClinicalIntentRequest,
    ClinicalIntentResponse,
    ClinicalIntentRouteRequest,
    ClinicalIntentRouteResponse,
    ClinicalReviewItemDecisionRequest,
    ClinicalReviewItemDecisionResponse,
    ConfirmClinicalPatchRequest,
    ConfirmClinicalPatchResponse,
    DraftSoapFromEventsRequest,
    DraftSoapFromEventsResponse,
    EventProposalFromEntryRequest,
    EventProposalsFromEntryResponse,
)
from oneepis_api.services.ai.provider import get_ai_provider
from oneepis_api.services.audit import record_audit_event
from oneepis_api.services.clinical_context import build_event_context
from oneepis_api.services.clinical_intent import resolve_clinical_intent
from oneepis_api.services.clinical_intent_decision_metadata import (
    clinical_action_decision_metadata,
    review_item_decision_metadata,
)
from oneepis_api.services.clinical_intent_router import route_clinical_intent
from oneepis_api.services.clinical_patch import confirm_clinical_patch as confirm_patch_service
from oneepis_api.services.document_drafter import draft_soap_from_events
from oneepis_api.services.event_proposals import propose_events_from_entry

from .patient_shared import (
    PATIENT_ROUTER_OPTIONS,
    SessionDep,
    SettingsDep,
    require_patient,
    require_patient_child,
    validate_encounter_for_patient,
)

router = APIRouter(**PATIENT_ROUTER_OPTIONS)


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
    "/{patient_id}/ai/event-proposals-from-entry",
    response_model=EventProposalsFromEntryResponse,
)
def create_event_proposals_from_entry(
    patient_id: uuid.UUID,
    payload: EventProposalFromEntryRequest,
    session: SessionDep,
    user: AiAccessDep,
) -> EventProposalsFromEntryResponse:
    require_patient(session, patient_id)
    entry = require_patient_child(
        session,
        ClinicalEntry,
        payload.entry_id,
        patient_id,
        "Clinical entry not found",
    )
    response = propose_events_from_entry(entry, max_proposals=payload.max_proposals)
    record_audit_event(
        session,
        action="ai.entry_event_proposals.created",
        entity_type="clinical_entry",
        entity_id=entry.id,
        actor_id=user.actor_id,
        metadata={
            "patient_id": str(patient_id),
            "entry_id": str(entry.id),
            "proposal_count": len(response.proposals),
            "applies_changes": response.applies_changes,
            "requires_human_confirmation": response.requires_human_confirmation,
        },
    )
    session.commit()
    return response


@router.post(
    "/{patient_id}/ai/confirm-clinical-patch",
    response_model=ConfirmClinicalPatchResponse,
)
def confirm_clinical_patch(
    patient_id: uuid.UUID,
    payload: ConfirmClinicalPatchRequest,
    session: SessionDep,
    user: AiAccessDep,
) -> ConfirmClinicalPatchResponse:
    require_patient(session, patient_id)
    return confirm_patch_service(
        session=session,
        patient_id=patient_id,
        payload=payload,
        actor=user.actor_id,
        validate_encounter=lambda encounter_id: validate_encounter_for_patient(
            session,
            patient_id,
            encounter_id,
        ),
    )


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
        metadata=clinical_action_decision_metadata(patient_id, payload),
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
        metadata=review_item_decision_metadata(patient_id, payload),
    )
    session.commit()
    return ClinicalReviewItemDecisionResponse(
        decision=payload.decision,
        message="Decision auditada. No se aplicaron cambios automaticos a la ficha.",
    )
