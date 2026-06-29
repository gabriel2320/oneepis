from __future__ import annotations

import uuid

from fastapi import APIRouter, status

from oneepis_api.api.deps import AiAccessDep, PatientActorDep, PatientReadActorDep
from oneepis_api.models.patient import Patient
from oneepis_api.repositories import patients as patient_repo
from oneepis_api.schemas.ai import PatientAiSuggestionRequest, PatientAiSuggestionsResponse
from oneepis_api.schemas.patient import (
    PatientCreate,
    PatientRead,
    PatientRecordSnapshot,
    PatientUpdate,
)
from oneepis_api.services.ai.provider import get_ai_provider
from oneepis_api.services.audit import (
    audit_snapshot,
    changed_field_snapshots,
    record_audit_event,
    record_read_audit_event,
)
from oneepis_api.services.historical_diagnoses import historical_diagnoses_from_events

from .patient_shared import (
    PATIENT_ROUTER_OPTIONS,
    LimitQuery,
    OffsetQuery,
    PatientSearch,
    SessionDep,
    SettingsDep,
    apply_update,
    require_patient,
    validate_development_patient_data,
)

router = APIRouter(**PATIENT_ROUTER_OPTIONS)


def _build_patient_record_snapshot(
    session: SessionDep,
    patient_id: uuid.UUID,
) -> PatientRecordSnapshot:
    patient = require_patient(session, patient_id)
    return PatientRecordSnapshot(
        patient=patient,
        latest_vitals=patient_repo.get_latest_vitals(session, patient_id),
        active_allergies=patient_repo.get_active_allergies(session, patient_id),
        active_medications=patient_repo.get_active_medications(session, patient_id),
        active_problems=patient_repo.get_active_problems(session, patient_id),
        historical_diagnoses=historical_diagnoses_from_events(
            patient_repo.get_diagnosis_events(session, patient_id)
        ),
        recent_entries=patient_repo.get_recent_entries(session, patient_id),
    )


def _record_patient_read_audit(
    session: SessionDep,
    *,
    patient_id: uuid.UUID,
    actor_id: str,
    action: str,
) -> None:
    record_read_audit_event(
        session,
        action=action,
        entity_type="patient",
        entity_id=patient_id,
        actor_id=actor_id,
    )
    session.commit()


@router.get("", response_model=list[PatientRead])
def list_patients(
    session: SessionDep,
    search: PatientSearch = None,
    limit: LimitQuery = 25,
    offset: OffsetQuery = 0,
) -> list[Patient]:
    return patient_repo.list_patients(session, search=search, limit=limit, offset=offset)


@router.post("", response_model=PatientRead, status_code=status.HTTP_201_CREATED)
def create_patient(
    payload: PatientCreate,
    session: SessionDep,
    actor: PatientActorDep,
    settings: SettingsDep,
) -> Patient:
    validate_development_patient_data(settings, payload)
    patient = Patient(**payload.model_dump())
    session.add(patient)
    session.flush()
    record_audit_event(
        session,
        action="patient.created",
        entity_type="patient",
        entity_id=patient.id,
        actor_id=actor,
        after=audit_snapshot(patient),
    )
    session.commit()
    session.refresh(patient)
    return patient


@router.get("/{patient_id}", response_model=PatientRead)
def get_patient(
    patient_id: uuid.UUID,
    session: SessionDep,
    actor: PatientReadActorDep,
) -> Patient:
    patient = require_patient(session, patient_id)
    _record_patient_read_audit(
        session,
        patient_id=patient_id,
        actor_id=actor,
        action="patient.read",
    )
    return patient


@router.patch("/{patient_id}", response_model=PatientRead)
def update_patient(
    patient_id: uuid.UUID,
    payload: PatientUpdate,
    session: SessionDep,
    actor: PatientActorDep,
    settings: SettingsDep,
) -> Patient:
    validate_development_patient_data(settings, payload)
    patient = require_patient(session, patient_id)
    update_fields = sorted(payload.model_dump(exclude_unset=True).keys())
    before = audit_snapshot(patient, update_fields)
    fields = apply_update(patient, payload)
    before_changed, after_changed = changed_field_snapshots(
        before=before,
        after_model=patient,
        fields=fields,
    )

    record_audit_event(
        session,
        action="patient.updated",
        entity_type="patient",
        entity_id=patient.id,
        actor_id=actor,
        metadata={"fields": fields},
        before=before_changed,
        after=after_changed,
    )
    session.commit()
    session.refresh(patient)
    return patient


@router.get("/{patient_id}/record", response_model=PatientRecordSnapshot)
def get_patient_record(
    patient_id: uuid.UUID,
    session: SessionDep,
    actor: PatientReadActorDep,
) -> PatientRecordSnapshot:
    snapshot = _build_patient_record_snapshot(session, patient_id)
    _record_patient_read_audit(
        session,
        patient_id=patient_id,
        actor_id=actor,
        action="record.read",
    )
    return snapshot


@router.post("/{patient_id}/ai/suggestions", response_model=PatientAiSuggestionsResponse)
def create_patient_ai_suggestions(
    patient_id: uuid.UUID,
    payload: PatientAiSuggestionRequest,
    session: SessionDep,
    settings: SettingsDep,
    _user: AiAccessDep,
) -> PatientAiSuggestionsResponse:
    snapshot = _build_patient_record_snapshot(session, patient_id)
    provider = get_ai_provider(settings)
    return provider.create_patient_suggestions(str(patient_id), snapshot, payload)
