from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from oneepis_api.repositories import patients as patient_repo
from oneepis_api.schemas.clinical_record import (
    ClinicalIntentRequest,
    ClinicalIntentResponse,
    ClinicalIntentRouteRequest,
    ClinicalIntentRouteResponse,
)
from oneepis_api.schemas.patient import PatientRecordSnapshot
from oneepis_api.services.clinical_intent_responses import (
    active_problems_response as _active_problems_response,
)
from oneepis_api.services.clinical_intent_responses import (
    daily_changes_response as _daily_changes_response,
)
from oneepis_api.services.clinical_intent_responses import (
    draft_soap_intent_response as _draft_soap_intent_response,
)
from oneepis_api.services.clinical_intent_responses import (
    show_sources_response as _show_sources_response,
)
from oneepis_api.services.clinical_intent_responses import (
    summarize_patient_response as _summarize_patient_response,
)
from oneepis_api.services.clinical_intent_responses import (
    timeline_response as _timeline_response,
)
from oneepis_api.services.clinical_intent_review import (
    apply_review_decisions as _apply_review_decisions,
)
from oneepis_api.services.clinical_intent_review import (
    build_review_items as _review_items,
)
from oneepis_api.services.clinical_intent_router import (
    route_clinical_intent as _route_clinical_intent,
)
from oneepis_api.services.clinical_lab_context import fetch_context_lab_results
from oneepis_api.services.historical_diagnoses import historical_diagnoses_from_events


def route_clinical_intent(payload: ClinicalIntentRouteRequest) -> ClinicalIntentRouteResponse:
    return _route_clinical_intent(payload)


def resolve_clinical_intent(
    session: Session,
    patient_id: uuid.UUID,
    payload: ClinicalIntentRequest,
) -> ClinicalIntentResponse:
    patient = patient_repo.get_patient(session, patient_id)
    if patient is None:
        raise ValueError("Patient not found")

    diagnosis_events = patient_repo.get_diagnosis_events(session, patient_id)
    active_risks = patient_repo.get_active_risks(session, patient_id)
    snapshot = PatientRecordSnapshot(
        patient=patient,
        latest_vitals=patient_repo.get_latest_vitals(session, patient_id),
        active_allergies=patient_repo.get_active_allergies(session, patient_id),
        active_medications=patient_repo.get_active_medications(session, patient_id),
        active_problems=patient_repo.get_active_problems(session, patient_id),
        historical_diagnoses=historical_diagnoses_from_events(diagnosis_events),
        recent_entries=patient_repo.get_recent_entries(session, patient_id),
    )
    events = patient_repo.get_recent_events(session, patient_id, limit=payload.max_events)
    recent_vitals = patient_repo.get_recent_vitals(session, patient_id, limit=2)
    lab_results = fetch_context_lab_results(session, patient_id)
    latest_entry = snapshot.recent_entries[0] if snapshot.recent_entries else None
    review_items = _review_items(snapshot, events, latest_entry)
    review_items = _apply_review_decisions(session, patient_id, review_items)

    if payload.intent_type == "summarize_patient":
        return _summarize_patient_response(
            payload,
            snapshot,
            events,
            recent_vitals,
            lab_results,
            review_items,
            active_risks,
        )
    if payload.intent_type == "daily_changes":
        return _daily_changes_response(
            payload,
            snapshot,
            events,
            recent_vitals,
            lab_results,
            review_items,
            active_risks,
        )
    if payload.intent_type == "active_problems":
        return _active_problems_response(
            payload,
            snapshot,
            recent_vitals,
            lab_results,
            review_items,
            active_risks,
        )
    if payload.intent_type == "timeline":
        return _timeline_response(
            payload,
            snapshot,
            events,
            recent_vitals,
            lab_results,
            review_items,
            active_risks,
        )
    if payload.intent_type == "draft_soap":
        return _draft_soap_intent_response(
            payload,
            snapshot,
            events,
            recent_vitals,
            lab_results,
            review_items,
            active_risks,
        )
    return _show_sources_response(
        payload,
        snapshot,
        events,
        recent_vitals,
        lab_results,
        review_items,
        active_risks,
    )
