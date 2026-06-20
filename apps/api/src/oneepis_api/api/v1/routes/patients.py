from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from oneepis_api.api.deps import (
    AiAccessDep,
    AllergyActorDep,
    ClinicalEntryActorDep,
    MedicationActorDep,
    PatientActorDep,
    VitalSignActorDep,
    require_patient_read_access,
)
from oneepis_api.core.config import Settings, get_settings
from oneepis_api.db.session import get_session
from oneepis_api.models.audit import AuditEvent
from oneepis_api.models.clinical_record import (
    Allergy,
    ClinicalEntry,
    ClinicalEntryStatus,
    Medication,
    RecordStatus,
    VitalSign,
)
from oneepis_api.models.patient import Patient
from oneepis_api.repositories import patients as patient_repo
from oneepis_api.schemas.ai import PatientAiSuggestionRequest, PatientAiSuggestionsResponse
from oneepis_api.schemas.audit import AuditEventRead
from oneepis_api.schemas.clinical_record import (
    AllergyCreate,
    AllergyRead,
    AllergyUpdate,
    ClinicalEntryCreate,
    ClinicalEntryRead,
    ClinicalEntryUpdate,
    MedicationCreate,
    MedicationRead,
    MedicationUpdate,
    VitalSignCreate,
    VitalSignRead,
    VitalSignUpdate,
)
from oneepis_api.schemas.patient import (
    PatientCreate,
    PatientRead,
    PatientRecordSnapshot,
    PatientUpdate,
)
from oneepis_api.services.ai.provider import get_ai_provider
from oneepis_api.services.audit import record_audit_event

router = APIRouter(
    prefix="/patients",
    tags=["patients"],
    dependencies=[Depends(require_patient_read_access)],
)
SessionDep = Annotated[Session, Depends(get_session)]
SettingsDep = Annotated[Settings, Depends(get_settings)]
PatientSearch = Annotated[str | None, Query(min_length=2, max_length=80)]
LimitQuery = Annotated[int, Query(ge=1, le=100)]
OffsetQuery = Annotated[int, Query(ge=0)]


def require_patient(session: Session, patient_id: uuid.UUID) -> Patient:
    patient = patient_repo.get_patient(session, patient_id)
    if patient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    return patient


def require_patient_child[T](
    session: Session,
    model: type[T],
    entity_id: uuid.UUID,
    patient_id: uuid.UUID,
    detail: str,
) -> T:
    entity = session.get(model, entity_id)
    if entity is None or getattr(entity, "patient_id", None) != patient_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)
    return entity


def apply_update(model: object, payload: object) -> list[str]:
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(model, field, value)
    return sorted(update_data.keys())


@router.get("", response_model=list[PatientRead])
def list_patients(
    session: SessionDep,
    search: PatientSearch = None,
    limit: LimitQuery = 25,
    offset: OffsetQuery = 0,
) -> list[Patient]:
    return patient_repo.list_patients(session, search=search, limit=limit, offset=offset)


@router.post("", response_model=PatientRead, status_code=status.HTTP_201_CREATED)
def create_patient(payload: PatientCreate, session: SessionDep, actor: PatientActorDep) -> Patient:
    patient = Patient(**payload.model_dump())
    session.add(patient)
    session.flush()
    record_audit_event(
        session,
        action="patient.created",
        entity_type="patient",
        entity_id=patient.id,
        actor_id=actor,
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
    actor: PatientActorDep,
) -> Patient:
    patient = require_patient(session, patient_id)
    fields = apply_update(patient, payload)

    record_audit_event(
        session,
        action="patient.updated",
        entity_type="patient",
        entity_id=patient.id,
        actor_id=actor,
        metadata={"fields": fields},
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


@router.post("/{patient_id}/ai/suggestions", response_model=PatientAiSuggestionsResponse)
def create_patient_ai_suggestions(
    patient_id: uuid.UUID,
    payload: PatientAiSuggestionRequest,
    session: SessionDep,
    settings: SettingsDep,
    _user: AiAccessDep,
) -> PatientAiSuggestionsResponse:
    snapshot = get_patient_record(patient_id, session)
    provider = get_ai_provider(settings)
    return provider.create_patient_suggestions(str(patient_id), snapshot, payload)


@router.get("/{patient_id}/clinical-entries", response_model=list[ClinicalEntryRead])
def list_clinical_entries(
    patient_id: uuid.UUID,
    session: SessionDep,
    limit: LimitQuery = 25,
    offset: OffsetQuery = 0,
) -> list[ClinicalEntry]:
    require_patient(session, patient_id)
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
) -> ClinicalEntry:
    require_patient(session, patient_id)
    return require_patient_child(
        session,
        ClinicalEntry,
        entry_id,
        patient_id,
        "Clinical entry not found",
    )


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
    fields = apply_update(entry, payload)
    record_audit_event(
        session,
        action="clinical_entry.updated",
        entity_type="clinical_entry",
        entity_id=entry.id,
        actor_id=actor,
        metadata={"patient_id": str(patient_id), "fields": fields},
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
    record_audit_event(
        session,
        action="clinical_entry.deleted",
        entity_type="clinical_entry",
        entity_id=entry.id,
        actor_id=actor,
        metadata={"patient_id": str(patient_id), "status": entry.status.value},
    )
    session.delete(entry)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{patient_id}/allergies", response_model=list[AllergyRead])
def list_allergies(
    patient_id: uuid.UUID,
    session: SessionDep,
    limit: LimitQuery = 50,
    offset: OffsetQuery = 0,
) -> list[Allergy]:
    require_patient(session, patient_id)
    statement = (
        select(Allergy)
        .where(Allergy.patient_id == patient_id)
        .order_by(Allergy.recorded_at.desc())
        .offset(offset)
        .limit(limit)
    )
    return list(session.scalars(statement))


@router.post(
    "/{patient_id}/allergies",
    response_model=AllergyRead,
    status_code=status.HTTP_201_CREATED,
)
def create_allergy(
    patient_id: uuid.UUID,
    payload: AllergyCreate,
    session: SessionDep,
    actor: AllergyActorDep,
) -> Allergy:
    require_patient(session, patient_id)
    allergy = Allergy(patient_id=patient_id, **payload.model_dump())
    session.add(allergy)
    session.flush()
    record_audit_event(
        session,
        action="allergy.created",
        entity_type="allergy",
        entity_id=allergy.id,
        actor_id=actor,
        metadata={"patient_id": str(patient_id), "severity": allergy.severity.value},
    )
    session.commit()
    session.refresh(allergy)
    return allergy


@router.get("/{patient_id}/allergies/{allergy_id}", response_model=AllergyRead)
def get_allergy(
    patient_id: uuid.UUID,
    allergy_id: uuid.UUID,
    session: SessionDep,
) -> Allergy:
    require_patient(session, patient_id)
    return require_patient_child(session, Allergy, allergy_id, patient_id, "Allergy not found")


@router.patch("/{patient_id}/allergies/{allergy_id}", response_model=AllergyRead)
def update_allergy(
    patient_id: uuid.UUID,
    allergy_id: uuid.UUID,
    payload: AllergyUpdate,
    session: SessionDep,
    actor: AllergyActorDep,
) -> Allergy:
    require_patient(session, patient_id)
    allergy = require_patient_child(session, Allergy, allergy_id, patient_id, "Allergy not found")
    fields = apply_update(allergy, payload)
    record_audit_event(
        session,
        action="allergy.updated",
        entity_type="allergy",
        entity_id=allergy.id,
        actor_id=actor,
        metadata={"patient_id": str(patient_id), "fields": fields},
    )
    session.commit()
    session.refresh(allergy)
    return allergy


@router.delete("/{patient_id}/allergies/{allergy_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_allergy(
    patient_id: uuid.UUID,
    allergy_id: uuid.UUID,
    session: SessionDep,
    actor: AllergyActorDep,
) -> Response:
    require_patient(session, patient_id)
    allergy = require_patient_child(session, Allergy, allergy_id, patient_id, "Allergy not found")
    allergy.status = RecordStatus.ENTERED_IN_ERROR
    record_audit_event(
        session,
        action="allergy.entered_in_error",
        entity_type="allergy",
        entity_id=allergy.id,
        actor_id=actor,
        metadata={"patient_id": str(patient_id)},
    )
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{patient_id}/medications", response_model=list[MedicationRead])
def list_medications(
    patient_id: uuid.UUID,
    session: SessionDep,
    limit: LimitQuery = 50,
    offset: OffsetQuery = 0,
) -> list[Medication]:
    require_patient(session, patient_id)
    statement = (
        select(Medication)
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
    medication = Medication(patient_id=patient_id, **payload.model_dump())
    session.add(medication)
    session.flush()
    record_audit_event(
        session,
        action="medication.created",
        entity_type="medication",
        entity_id=medication.id,
        actor_id=actor,
        metadata={"patient_id": str(patient_id), "status": medication.status.value},
    )
    session.commit()
    session.refresh(medication)
    return medication


@router.get("/{patient_id}/medications/{medication_id}", response_model=MedicationRead)
def get_medication(
    patient_id: uuid.UUID,
    medication_id: uuid.UUID,
    session: SessionDep,
) -> Medication:
    require_patient(session, patient_id)
    return require_patient_child(
        session,
        Medication,
        medication_id,
        patient_id,
        "Medication not found",
    )


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
    fields = apply_update(medication, payload)
    record_audit_event(
        session,
        action="medication.updated",
        entity_type="medication",
        entity_id=medication.id,
        actor_id=actor,
        metadata={"patient_id": str(patient_id), "fields": fields},
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
    medication.status = RecordStatus.ENTERED_IN_ERROR
    record_audit_event(
        session,
        action="medication.entered_in_error",
        entity_type="medication",
        entity_id=medication.id,
        actor_id=actor,
        metadata={"patient_id": str(patient_id)},
    )
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{patient_id}/vital-signs", response_model=list[VitalSignRead])
def list_vital_signs(
    patient_id: uuid.UUID,
    session: SessionDep,
    limit: LimitQuery = 50,
    offset: OffsetQuery = 0,
) -> list[VitalSign]:
    require_patient(session, patient_id)
    statement = (
        select(VitalSign)
        .where(VitalSign.patient_id == patient_id)
        .order_by(VitalSign.measured_at.desc())
        .offset(offset)
        .limit(limit)
    )
    return list(session.scalars(statement))


@router.post(
    "/{patient_id}/vital-signs",
    response_model=VitalSignRead,
    status_code=status.HTTP_201_CREATED,
)
def create_vital_sign(
    patient_id: uuid.UUID,
    payload: VitalSignCreate,
    session: SessionDep,
    actor: VitalSignActorDep,
) -> VitalSign:
    require_patient(session, patient_id)
    vital = VitalSign(patient_id=patient_id, **payload.model_dump())
    session.add(vital)
    session.flush()
    record_audit_event(
        session,
        action="vital_sign.created",
        entity_type="vital_sign",
        entity_id=vital.id,
        actor_id=actor,
        metadata={"patient_id": str(patient_id), "measured_at": vital.measured_at.isoformat()},
    )
    session.commit()
    session.refresh(vital)
    return vital


@router.get("/{patient_id}/vital-signs/{vital_sign_id}", response_model=VitalSignRead)
def get_vital_sign(
    patient_id: uuid.UUID,
    vital_sign_id: uuid.UUID,
    session: SessionDep,
) -> VitalSign:
    require_patient(session, patient_id)
    return require_patient_child(
        session,
        VitalSign,
        vital_sign_id,
        patient_id,
        "Vital sign not found",
    )


@router.patch("/{patient_id}/vital-signs/{vital_sign_id}", response_model=VitalSignRead)
def update_vital_sign(
    patient_id: uuid.UUID,
    vital_sign_id: uuid.UUID,
    payload: VitalSignUpdate,
    session: SessionDep,
    actor: VitalSignActorDep,
) -> VitalSign:
    require_patient(session, patient_id)
    vital = require_patient_child(
        session,
        VitalSign,
        vital_sign_id,
        patient_id,
        "Vital sign not found",
    )
    fields = apply_update(vital, payload)
    record_audit_event(
        session,
        action="vital_sign.updated",
        entity_type="vital_sign",
        entity_id=vital.id,
        actor_id=actor,
        metadata={"patient_id": str(patient_id), "fields": fields},
    )
    session.commit()
    session.refresh(vital)
    return vital


@router.delete("/{patient_id}/vital-signs/{vital_sign_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vital_sign(
    patient_id: uuid.UUID,
    vital_sign_id: uuid.UUID,
    session: SessionDep,
    actor: VitalSignActorDep,
) -> Response:
    require_patient(session, patient_id)
    vital = require_patient_child(
        session,
        VitalSign,
        vital_sign_id,
        patient_id,
        "Vital sign not found",
    )
    record_audit_event(
        session,
        action="vital_sign.deleted",
        entity_type="vital_sign",
        entity_id=vital.id,
        actor_id=actor,
        metadata={"patient_id": str(patient_id), "measured_at": vital.measured_at.isoformat()},
    )
    session.delete(vital)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{patient_id}/audit-events", response_model=list[AuditEventRead])
def list_patient_audit_events(
    patient_id: uuid.UUID,
    session: SessionDep,
    limit: LimitQuery = 50,
) -> list[AuditEvent]:
    require_patient(session, patient_id)
    statement = select(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(limit * 4)
    events = list(session.scalars(statement))
    patient_id_text = str(patient_id)
    matched = [
        event
        for event in events
        if (event.entity_type == "patient" and event.entity_id == patient_id)
        or str(event.extra_data.get("patient_id")) == patient_id_text
    ]
    return matched[:limit]
