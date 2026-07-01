from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Response, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from oneepis_api.api.deps import MedicationActorDep, ReadAccessDep
from oneepis_api.models.clinical_record import Medication, RecordStatus
from oneepis_api.models.hospitalization import HospitalIndication
from oneepis_api.schemas.clinical_record import (
    MedicationCreate,
    MedicationDraftingContext,
    MedicationDraftValidationRequest,
    MedicationDraftValidationResponse,
    MedicationRead,
    MedicationUpdate,
)
from oneepis_api.services.audit import audit_snapshot, changed_field_snapshots, record_audit_event
from oneepis_api.services.medication_audit import (
    MEDICATION_CREATE_AUDIT_FIELDS,
    medication_dose_audit_metadata,
    medication_update_audit_fields,
    sanitize_override_reason_audit,
)
from oneepis_api.services.medication_catalog import (
    list_catalog_items,
    patient_medication_suggestions,
    validate_medication_draft,
)
from oneepis_api.services.medication_draft_validation import (
    updated_dose_snapshot,
    validated_dose_snapshot,
)
from oneepis_api.services.patient_scope_enforcement import enforce_patient_scope_for_read

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
)

router = APIRouter(**PATIENT_ROUTER_OPTIONS)


def _enforce_read(session, patient_id, user, settings) -> None:
    enforce_patient_scope_for_read(
        session,
        patient_id=patient_id,
        actor_id=user.actor_id,
        roles=user.roles,
        settings=settings,
    )


def _audit_read(session, patient_id, user, action: str) -> None:
    record_patient_scoped_read(
        session,
        patient_id=patient_id,
        actor_id=user.actor_id,
        action=action,
    )


@router.get("/{patient_id}/medications", response_model=list[MedicationRead])
def list_medications(
    patient_id: uuid.UUID,
    session: SessionDep,
    user: ReadAccessDep,
    settings: SettingsDep,
    limit: LimitQuery = 50,
    offset: OffsetQuery = 0,
) -> list[Medication]:
    require_patient(session, patient_id)
    _enforce_read(session, patient_id, user, settings)
    _audit_read(session, patient_id, user, "medications.read")
    statement = (
        select(Medication)
        .options(selectinload(Medication.catalog_item))
        .where(Medication.patient_id == patient_id)
        .order_by(Medication.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    return list(session.scalars(statement))


@router.post(
    "/{patient_id}/medications",
    response_model=MedicationRead,
    status_code=status.HTTP_201_CREATED,
)
def create_medication(
    patient_id: uuid.UUID,
    payload: MedicationCreate,
    session: SessionDep,
    actor: MedicationActorDep,
) -> Medication:
    require_patient(session, patient_id)
    dose_check_snapshot = validated_dose_snapshot(session, payload)
    medication = Medication(
        patient_id=patient_id,
        **payload.model_dump(),
        dose_check_snapshot=dose_check_snapshot,
    )
    session.add(medication)
    session.flush()
    record_audit_event(
        session,
        action="medication.created",
        entity_type="medication",
        entity_id=medication.id,
        actor_id=actor,
        metadata={
            "patient_id": str(patient_id),
            "status": medication.status.value,
            **medication_dose_audit_metadata(dose_check_snapshot, payload.dose_override_reason),
        },
        after=audit_snapshot(medication, MEDICATION_CREATE_AUDIT_FIELDS),
    )
    session.commit()
    session.refresh(medication)
    return medication


@router.get("/{patient_id}/medication-drafting-context", response_model=MedicationDraftingContext)
def get_medication_drafting_context(
    patient_id: uuid.UUID,
    session: SessionDep,
    user: ReadAccessDep,
    settings: SettingsDep,
) -> MedicationDraftingContext:
    require_patient(session, patient_id)
    _enforce_read(session, patient_id, user, settings)
    _audit_read(session, patient_id, user, "medication_drafting_context.read")
    medication_statement = (
        select(Medication)
        .options(selectinload(Medication.catalog_item))
        .where(Medication.patient_id == patient_id)
        .order_by(Medication.created_at.desc())
        .limit(20)
    )
    recent_medications = list(session.scalars(medication_statement))
    active_medications = [
        medication for medication in recent_medications if medication.status == RecordStatus.ACTIVE
    ]
    indication_statement = (
        select(HospitalIndication)
        .where(HospitalIndication.patient_id == patient_id)
        .order_by(HospitalIndication.indicated_at.desc())
        .limit(3)
    )
    indication_texts = [
        f"{indication.title}: {indication.indication_text}"
        for indication in session.scalars(indication_statement)
    ]
    catalog_items = list_catalog_items(session, query=None, limit=20)
    return MedicationDraftingContext(
        active_medications=active_medications,
        recent_medications=recent_medications,
        previous_day_indication_texts=indication_texts,
        suggested_catalog_items=patient_medication_suggestions(catalog_items, recent_medications),
        limitations=[
            "Contexto de borrador: no crea receta valida, orden ejecutable, firma ni folio.",
            "Textos previos se copian completos para revision humana; no se parsean.",
        ],
    )


@router.post(
    "/{patient_id}/medications/validate-draft",
    response_model=MedicationDraftValidationResponse,
)
def validate_medication_draft_route(
    patient_id: uuid.UUID,
    payload: MedicationDraftValidationRequest,
    session: SessionDep,
) -> MedicationDraftValidationResponse:
    require_patient(session, patient_id)
    return validate_medication_draft(session, payload)


@router.get("/{patient_id}/medications/{medication_id}", response_model=MedicationRead)
def get_medication(
    patient_id: uuid.UUID,
    medication_id: uuid.UUID,
    session: SessionDep,
    user: ReadAccessDep,
    settings: SettingsDep,
) -> Medication:
    require_patient(session, patient_id)
    _enforce_read(session, patient_id, user, settings)
    medication = require_patient_child(
        session,
        Medication,
        medication_id,
        patient_id,
        "Medication not found",
    )
    _audit_read(session, patient_id, user, "medication.read")
    return medication


@router.patch("/{patient_id}/medications/{medication_id}", response_model=MedicationRead)
def update_medication(
    patient_id: uuid.UUID,
    medication_id: uuid.UUID,
    payload: MedicationUpdate,
    session: SessionDep,
    actor: MedicationActorDep,
) -> Medication:
    require_patient(session, patient_id)
    medication = require_patient_child(
        session,
        Medication,
        medication_id,
        patient_id,
        "Medication not found",
    )
    dose_check_snapshot = updated_dose_snapshot(session, medication, payload)
    update_fields = set(payload.model_dump(exclude_unset=True).keys())
    if dose_check_snapshot is not None:
        update_fields.add("dose_check_snapshot")
    update_fields = sorted(update_fields)
    audit_fields = medication_update_audit_fields(update_fields)
    before = audit_snapshot(medication, audit_fields)
    fields = apply_update(medication, payload)
    if dose_check_snapshot is not None:
        medication.dose_check_snapshot = dose_check_snapshot
        fields = sorted(set(fields) | {"dose_check_snapshot"})
    audit_fields = medication_update_audit_fields(fields)
    before_changed, after_changed = changed_field_snapshots(
        before=before,
        after_model=medication,
        fields=audit_fields,
    )
    sanitize_override_reason_audit(before_changed)
    sanitize_override_reason_audit(after_changed)
    metadata: dict[str, Any] = {"patient_id": str(patient_id), "fields": fields}
    if dose_check_snapshot is not None:
        override_reason = payload.model_dump(exclude_unset=True).get(
            "dose_override_reason",
            medication.dose_override_reason,
        )
        metadata.update(medication_dose_audit_metadata(dose_check_snapshot, override_reason))
    record_audit_event(
        session,
        action="medication.updated",
        entity_type="medication",
        entity_id=medication.id,
        actor_id=actor,
        metadata=metadata,
        before=before_changed,
        after=after_changed,
    )
    session.commit()
    session.refresh(medication)
    return medication


@router.delete("/{patient_id}/medications/{medication_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_medication(
    patient_id: uuid.UUID,
    medication_id: uuid.UUID,
    session: SessionDep,
    actor: MedicationActorDep,
) -> Response:
    require_patient(session, patient_id)
    medication = require_patient_child(
        session,
        Medication,
        medication_id,
        patient_id,
        "Medication not found",
    )
    before = audit_snapshot(medication, ["status"])
    medication.status = RecordStatus.ENTERED_IN_ERROR
    record_audit_event(
        session,
        action="medication.entered_in_error",
        entity_type="medication",
        entity_id=medication.id,
        actor_id=actor,
        metadata={"patient_id": str(patient_id)},
        before=before,
        after=audit_snapshot(medication, ["status"]),
    )
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
