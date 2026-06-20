from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from oneepis_api.db.session import get_session
from oneepis_api.models.clinical_record import ClinicalEntry
from oneepis_api.models.patient import Patient
from oneepis_api.repositories import patients as patient_repo
from oneepis_api.schemas.clinical_record import ClinicalEntryCreate, ClinicalEntryRead
from oneepis_api.schemas.patient import (
    PatientCreate,
    PatientRead,
    PatientRecordSnapshot,
    PatientUpdate,
)
from oneepis_api.services.audit import record_audit_event

router = APIRouter(prefix="/patients", tags=["patients"])
SessionDep = Annotated[Session, Depends(get_session)]
PatientSearch = Annotated[str | None, Query(min_length=2, max_length=80)]
LimitQuery = Annotated[int, Query(ge=1, le=100)]
OffsetQuery = Annotated[int, Query(ge=0)]


def require_patient(session: Session, patient_id: uuid.UUID) -> Patient:
    patient = patient_repo.get_patient(session, patient_id)
    if patient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    return patient


@router.get("", response_model=list[PatientRead])
def list_patients(
    session: SessionDep,
    search: PatientSearch = None,
    limit: LimitQuery = 25,
    offset: OffsetQuery = 0,
) -> list[Patient]:
    return patient_repo.list_patients(session, search=search, limit=limit, offset=offset)


@router.post("", response_model=PatientRead, status_code=status.HTTP_201_CREATED)
def create_patient(payload: PatientCreate, session: SessionDep) -> Patient:
    patient = Patient(**payload.model_dump())
    session.add(patient)
    session.flush()
    record_audit_event(
        session,
        action="patient.created",
        entity_type="patient",
        entity_id=patient.id,
        actor_id="system",
    )
    session.commit()
    session.refresh(patient)
    return patient


@router.get("/{patient_id}", response_model=PatientRead)
def get_patient(patient_id: uuid.UUID, session: SessionDep) -> Patient:
    return require_patient(session, patient_id)


@router.patch("/{patient_id}", response_model=PatientRead)
def update_patient(
    patient_id: uuid.UUID,
    payload: PatientUpdate,
    session: SessionDep,
) -> Patient:
    patient = require_patient(session, patient_id)
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(patient, field, value)

    record_audit_event(
        session,
        action="patient.updated",
        entity_type="patient",
        entity_id=patient.id,
        actor_id="system",
        metadata={"fields": sorted(update_data.keys())},
    )
    session.commit()
    session.refresh(patient)
    return patient


@router.get("/{patient_id}/record", response_model=PatientRecordSnapshot)
def get_patient_record(
    patient_id: uuid.UUID,
    session: SessionDep,
) -> PatientRecordSnapshot:
    patient = require_patient(session, patient_id)
    return PatientRecordSnapshot(
        patient=patient,
        latest_vitals=patient_repo.get_latest_vitals(session, patient_id),
        active_allergies=patient_repo.get_active_allergies(session, patient_id),
        active_medications=patient_repo.get_active_medications(session, patient_id),
        recent_entries=patient_repo.get_recent_entries(session, patient_id),
    )


@router.get("/{patient_id}/clinical-entries", response_model=list[ClinicalEntryRead])
def list_clinical_entries(
    patient_id: uuid.UUID,
    session: SessionDep,
    limit: LimitQuery = 25,
) -> list[ClinicalEntry]:
    require_patient(session, patient_id)
    return patient_repo.get_recent_entries(session, patient_id, limit=limit)


@router.post(
    "/{patient_id}/clinical-entries",
    response_model=ClinicalEntryRead,
    status_code=status.HTTP_201_CREATED,
)
def create_clinical_entry(
    patient_id: uuid.UUID,
    payload: ClinicalEntryCreate,
    session: SessionDep,
) -> ClinicalEntry:
    require_patient(session, patient_id)
    entry = ClinicalEntry(patient_id=patient_id, **payload.model_dump())
    session.add(entry)
    session.flush()
    record_audit_event(
        session,
        action="clinical_entry.created",
        entity_type="clinical_entry",
        entity_id=entry.id,
        actor_id=payload.created_by,
        metadata={"patient_id": str(patient_id), "kind": payload.kind.value},
    )
    session.commit()
    session.refresh(entry)
    return entry
