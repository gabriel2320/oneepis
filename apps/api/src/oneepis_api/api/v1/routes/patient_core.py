from __future__ import annotations

import uuid

from fastapi import APIRouter, status

from oneepis_api.api.deps import AiAccessDep, PatientActorDep, PatientReadActorDep, ReadAccessDep
from oneepis_api.models.patient import Patient
from oneepis_api.repositories import patients as patient_repo
from oneepis_api.schemas.ai import PatientAiSuggestionRequest, PatientAiSuggestionsResponse
from oneepis_api.schemas.patient import (
    PatientCreate,
    PatientRead,
    PatientRecordSnapshot,
    PatientUpdate,
)
from oneepis_api.services.access_context_audit import record_passive_patient_access_context_decision
from oneepis_api.services.ai.provider import get_ai_provider
from oneepis_api.services.audit import (
    audit_snapshot,
    changed_field_snapshots,
    record_audit_event,
    record_read_audit_event,
)
from oneepis_api.services.historical_diagnoses import historical_diagnoses_from_events
from oneepis_api.services.patient_scope_enforcement import enforce_patient_scope_for_read

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

PATIENT_AUDIT_FIELDS = [
    "clinical_status",
    "current_care_context",
]


def patient_audit_fields(fields: list[str]) -> list[str]:
    allowed_fields = set(PATIENT_AUDIT_FIELDS)
    return [field for field in fields if field in allowed_fields]


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
    record_passive_patient_access_context_decision(
        session,
        patient_id=patient_id,
        actor_id=actor_id,
        source_action=action,
    )
    session.commit()


@router.get("", response_model=list[PatientRead])
def list_patients(
    session: SessionDep,
    actor: PatientReadActorDep,
    search: PatientSearch = None,
    limit: LimitQuery = 25,
    offset: OffsetQuery = 0,
) -> list[Patient]:
    patients = patient_repo.list_patients(session, search=search, limit=limit, offset=offset)
    record_read_audit_event(
        session,
        action="patient_index.read",
        entity_type="patient_index",
        entity_id=None,
        actor_id=actor,
        metadata={
            "search_present": search is not None,
            "limit": limit,
            "offset": offset,
            "result_count": len(patients),
        },
    )
    session.commit()
    return patients


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
        after=audit_snapshot(patient, PATIENT_AUDIT_FIELDS),
    )
    session.commit()
    session.refresh(patient)
    return patient


@router.get("/{patient_id}", response_model=PatientRead)
def get_patient(
    patient_id: uuid.UUID,
    session: SessionDep,
    user: ReadAccessDep,
    settings: SettingsDep,
) -> Patient:
    patient = require_patient(session, patient_id)
    enforce_patient_scope_for_read(
        session,
        patient_id=patient_id,
        actor_id=user.actor_id,
        roles=user.roles,
        settings=settings,
    )
    _record_patient_read_audit(
        session,
        patient_id=patient_id,
        actor_id=user.actor_id,
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
    before = audit_snapshot(patient, patient_audit_fields(update_fields))
    fields = apply_update(patient, payload)
    audit_fields = patient_audit_fields(fields)
    before_changed, after_changed = changed_field_snapshots(
        before=before,
        after_model=patient,
        fields=audit_fields,
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
