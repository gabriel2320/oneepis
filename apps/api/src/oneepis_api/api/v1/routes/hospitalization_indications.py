from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from oneepis_api.api.deps import HospitalIndicationActorDep, require_patient_read_access
from oneepis_api.api.v1.routes.patient_shared import apply_update, require_patient
from oneepis_api.db.session import get_session
from oneepis_api.models.clinical_record import (
    ClinicalEncounter,
    EncounterStatus,
    EncounterType,
)
from oneepis_api.models.hospitalization import HospitalIndication, HospitalIndicationStatus
from oneepis_api.schemas.hospitalization import (
    HospitalIndicationCreate,
    HospitalIndicationRead,
    HospitalIndicationUpdate,
)
from oneepis_api.services.audit import (
    audit_snapshot,
    changed_field_snapshots,
    record_audit_event,
)

router = APIRouter(
    prefix="/hospitalization",
    tags=["hospitalization"],
    dependencies=[Depends(require_patient_read_access)],
)
SessionDep = Annotated[Session, Depends(get_session)]
LimitQuery = Annotated[int, Query(ge=1, le=100)]
HOSPITAL_INDICATION_AUDIT_FIELDS = [
    "created_by",
    "encounter_id",
    "indicated_at",
    "patient_id",
    "status",
]


@router.get("/patients/{patient_id}/indications", response_model=list[HospitalIndicationRead])
def list_hospital_indications(
    patient_id: uuid.UUID,
    session: SessionDep,
    limit: LimitQuery = 50,
) -> list[HospitalIndication]:
    require_patient(session, patient_id)
    statement = (
        select(HospitalIndication)
        .where(HospitalIndication.patient_id == patient_id)
        .order_by(HospitalIndication.indicated_at.desc(), HospitalIndication.created_at.desc())
        .limit(limit)
    )
    return list(session.scalars(statement))


@router.post(
    "/patients/{patient_id}/indications",
    response_model=HospitalIndicationRead,
    status_code=status.HTTP_201_CREATED,
)
def create_hospital_indication(
    patient_id: uuid.UUID,
    payload: HospitalIndicationCreate,
    session: SessionDep,
    actor: HospitalIndicationActorDep,
) -> HospitalIndication:
    encounter = _require_active_hospitalization(session, patient_id)
    indication = HospitalIndication(
        **payload.model_dump(),
        patient_id=patient_id,
        encounter_id=encounter.id,
        created_by=actor,
    )
    session.add(indication)
    session.flush()
    record_audit_event(
        session,
        action="hospital_indication.created",
        entity_type="hospital_indication",
        entity_id=indication.id,
        actor_id=actor,
        metadata=_indication_audit_metadata(indication),
        after=audit_snapshot(indication, HOSPITAL_INDICATION_AUDIT_FIELDS),
    )
    session.commit()
    session.refresh(indication)
    return indication


@router.patch(
    "/patients/{patient_id}/indications/{indication_id}",
    response_model=HospitalIndicationRead,
)
def update_hospital_indication(
    patient_id: uuid.UUID,
    indication_id: uuid.UUID,
    payload: HospitalIndicationUpdate,
    session: SessionDep,
    actor: HospitalIndicationActorDep,
) -> HospitalIndication:
    indication = _require_indication(session, patient_id, indication_id)
    _validate_indication_editable(indication)
    fields = sorted(payload.model_dump(exclude_unset=True).keys())
    audit_fields = _indication_audit_fields(fields)
    before = audit_snapshot(indication, audit_fields) if audit_fields else {}
    changed_fields = apply_update(indication, payload)
    audit_changed_fields = _indication_audit_fields(changed_fields)
    if audit_changed_fields:
        before_changed, after_changed = changed_field_snapshots(
            before=before,
            after_model=indication,
            fields=audit_changed_fields,
        )
    else:
        before_changed, after_changed = {}, {}
    record_audit_event(
        session,
        action="hospital_indication.updated",
        entity_type="hospital_indication",
        entity_id=indication.id,
        actor_id=actor,
        metadata=_indication_audit_metadata(indication, changed_fields),
        before=before_changed,
        after=after_changed,
    )
    session.commit()
    session.refresh(indication)
    return indication


def _require_active_hospitalization(
    session: Session,
    patient_id: uuid.UUID,
) -> ClinicalEncounter:
    require_patient(session, patient_id)
    statement = (
        select(ClinicalEncounter)
        .where(
            ClinicalEncounter.patient_id == patient_id,
            ClinicalEncounter.type == EncounterType.HOSPITALIZATION,
            ClinicalEncounter.status == EncounterStatus.IN_PROGRESS,
        )
        .order_by(ClinicalEncounter.started_at.desc())
        .limit(1)
    )
    encounter = session.scalar(statement)
    if encounter is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Hospital indication requires an active hospitalization encounter",
        )
    return encounter


def _require_indication(
    session: Session,
    patient_id: uuid.UUID,
    indication_id: uuid.UUID,
) -> HospitalIndication:
    indication = session.get(HospitalIndication, indication_id)
    if indication is None or indication.patient_id != patient_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hospital indication not found",
        )
    return indication


def _validate_indication_editable(indication: HospitalIndication) -> None:
    if indication.status == HospitalIndicationStatus.CLOSED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Closed hospital indications cannot be edited",
        )


def _indication_audit_metadata(
    indication: HospitalIndication,
    fields: list[str] | None = None,
) -> dict[str, object]:
    metadata: dict[str, object] = {
        "patient_id": str(indication.patient_id),
        "encounter_id": str(indication.encounter_id),
        "status": indication.status.value,
    }
    if fields is not None:
        metadata["fields"] = fields
    return metadata


def _indication_audit_fields(fields: list[str]) -> list[str]:
    return [field for field in fields if field in HOSPITAL_INDICATION_AUDIT_FIELDS]
