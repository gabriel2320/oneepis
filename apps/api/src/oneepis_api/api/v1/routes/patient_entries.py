from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import select

from oneepis_api.api.deps import ClinicalEntryActorDep, PatientReadActorDep
from oneepis_api.models.clinical_record import (
    ClinicalEntry,
    ClinicalEntryKind,
    ClinicalEntryStatus,
    EncounterType,
)
from oneepis_api.schemas.clinical_record import (
    ClinicalEntryCreate,
    ClinicalEntryRead,
    ClinicalEntryUpdate,
)
from oneepis_api.services.audit import audit_snapshot, changed_field_snapshots, record_audit_event

from .patient_shared import (
    PATIENT_ROUTER_OPTIONS,
    LimitQuery,
    OffsetQuery,
    SessionDep,
    apply_update,
    record_patient_scoped_read,
    require_encounter_for_patient,
    require_patient,
    require_patient_child,
    validate_encounter_for_patient,
)

router = APIRouter(**PATIENT_ROUTER_OPTIONS)

HOSPITAL_DOCUMENT_KINDS = {
    ClinicalEntryKind.INTAKE,
    ClinicalEntryKind.DISCHARGE_SUMMARY,
}
CLINICAL_ENTRY_AUDIT_FIELDS = [
    "created_by",
    "encounter_id",
    "kind",
    "occurred_at",
    "patient_id",
    "status",
]


def clinical_entry_audit_fields(fields: list[str]) -> list[str]:
    allowed_fields = set(CLINICAL_ENTRY_AUDIT_FIELDS)
    return [field for field in fields if field in allowed_fields]


@router.get("/{patient_id}/clinical-entries", response_model=list[ClinicalEntryRead])
def list_clinical_entries(
    patient_id: uuid.UUID,
    session: SessionDep,
    actor: PatientReadActorDep,
    limit: LimitQuery = 25,
    offset: OffsetQuery = 0,
) -> list[ClinicalEntry]:
    require_patient(session, patient_id)
    record_patient_scoped_read(
        session,
        patient_id=patient_id,
        actor_id=actor,
        action="clinical_entries.read",
    )
    statement = (
        select(ClinicalEntry)
        .where(ClinicalEntry.patient_id == patient_id)
        .order_by(ClinicalEntry.occurred_at.desc())
        .offset(offset)
        .limit(limit)
    )
    return list(session.scalars(statement))


@router.get("/{patient_id}/clinical-entries/{entry_id}", response_model=ClinicalEntryRead)
def get_clinical_entry(
    patient_id: uuid.UUID,
    entry_id: uuid.UUID,
    session: SessionDep,
    actor: PatientReadActorDep,
) -> ClinicalEntry:
    require_patient(session, patient_id)
    entry = require_patient_child(
        session,
        ClinicalEntry,
        entry_id,
        patient_id,
        "Clinical entry not found",
    )
    record_patient_scoped_read(
        session,
        patient_id=patient_id,
        actor_id=actor,
        action="clinical_entry.read",
    )
    return entry


@router.post(
    "/{patient_id}/clinical-entries",
    response_model=ClinicalEntryRead,
    status_code=status.HTTP_201_CREATED,
)
def create_clinical_entry(
    patient_id: uuid.UUID,
    payload: ClinicalEntryCreate,
    session: SessionDep,
    actor: ClinicalEntryActorDep,
) -> ClinicalEntry:
    require_patient(session, patient_id)
    entry_data = payload.model_dump()
    validate_entry_encounter(session, patient_id, payload.kind, payload.encounter_id)
    entry_data["created_by"] = actor
    entry = ClinicalEntry(patient_id=patient_id, **entry_data)
    session.add(entry)
    session.flush()
    record_audit_event(
        session,
        action="clinical_entry.created",
        entity_type="clinical_entry",
        entity_id=entry.id,
        actor_id=actor,
        metadata={"patient_id": str(patient_id), "kind": payload.kind.value},
        after=audit_snapshot(entry, CLINICAL_ENTRY_AUDIT_FIELDS),
    )
    session.commit()
    session.refresh(entry)
    return entry


@router.patch("/{patient_id}/clinical-entries/{entry_id}", response_model=ClinicalEntryRead)
def update_clinical_entry(
    patient_id: uuid.UUID,
    entry_id: uuid.UUID,
    payload: ClinicalEntryUpdate,
    session: SessionDep,
    actor: ClinicalEntryActorDep,
) -> ClinicalEntry:
    require_patient(session, patient_id)
    entry = require_patient_child(
        session,
        ClinicalEntry,
        entry_id,
        patient_id,
        "Clinical entry not found",
    )
    if "encounter_id" in payload.model_dump(exclude_unset=True):
        validate_entry_encounter(session, patient_id, entry.kind, payload.encounter_id)
    update_fields = sorted(payload.model_dump(exclude_unset=True).keys())
    before = audit_snapshot(entry, clinical_entry_audit_fields(update_fields))
    fields = apply_update(entry, payload)
    audit_fields = clinical_entry_audit_fields(fields)
    before_changed, after_changed = changed_field_snapshots(
        before=before,
        after_model=entry,
        fields=audit_fields,
    )
    record_audit_event(
        session,
        action="clinical_entry.updated",
        entity_type="clinical_entry",
        entity_id=entry.id,
        actor_id=actor,
        metadata={"patient_id": str(patient_id), "fields": fields},
        before=before_changed,
        after=after_changed,
    )
    session.commit()
    session.refresh(entry)
    return entry


@router.delete("/{patient_id}/clinical-entries/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_draft_clinical_entry(
    patient_id: uuid.UUID,
    entry_id: uuid.UUID,
    session: SessionDep,
    actor: ClinicalEntryActorDep,
) -> Response:
    require_patient(session, patient_id)
    entry = require_patient_child(
        session,
        ClinicalEntry,
        entry_id,
        patient_id,
        "Clinical entry not found",
    )
    if entry.status != ClinicalEntryStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only draft clinical entries can be deleted",
        )
    before = audit_snapshot(entry, CLINICAL_ENTRY_AUDIT_FIELDS)
    record_audit_event(
        session,
        action="clinical_entry.deleted",
        entity_type="clinical_entry",
        entity_id=entry.id,
        actor_id=actor,
        metadata={"patient_id": str(patient_id), "status": entry.status.value},
        before=before,
    )
    session.delete(entry)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def validate_entry_encounter(
    session: SessionDep,
    patient_id: uuid.UUID,
    kind: ClinicalEntryKind,
    encounter_id: uuid.UUID | None,
) -> None:
    if kind not in HOSPITAL_DOCUMENT_KINDS:
        validate_encounter_for_patient(session, patient_id, encounter_id)
        return
    if encounter_id is None:
        raise HTTPException(
            status_code=422,
            detail="Hospital clinical documents require a hospitalization encounter",
        )
    require_encounter_for_patient(
        session,
        patient_id,
        encounter_id,
        expected_type=EncounterType.HOSPITALIZATION,
        detail="Encounter not found",
    )
