from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from oneepis_api.api.deps import EncounterActorDep, PatientReadActorDep, require_patient_read_access
from oneepis_api.db.session import get_session
from oneepis_api.models.clinical_record import (
    ClinicalEncounter,
    EncounterStatus,
    EncounterType,
)
from oneepis_api.models.hospitalization import HospitalBed, HospitalBedStatus
from oneepis_api.models.patient import Patient
from oneepis_api.schemas.hospitalization import (
    HospitalBedCreate,
    HospitalBedRead,
    HospitalBedUpdate,
    HospitalizationBoardItem,
)
from oneepis_api.services.audit import (
    audit_snapshot,
    changed_field_snapshots,
    record_audit_event,
    record_read_audit_event,
)

router = APIRouter(
    prefix="/hospitalization",
    tags=["hospitalization"],
    dependencies=[Depends(require_patient_read_access)],
)
SessionDep = Annotated[Session, Depends(get_session)]
LimitQuery = Annotated[int, Query(ge=1, le=100)]

HOSPITAL_BED_AUDIT_FIELDS = [
    "encounter_id",
    "status",
]


def _bed_audit_fields(fields: list[str]) -> list[str]:
    allowed_fields = set(HOSPITAL_BED_AUDIT_FIELDS)
    return [field for field in fields if field in allowed_fields]


def _apply_update(model: object, payload: object) -> list[str]:
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(model, field, value)
    return sorted(update_data.keys())


def _require_bed(session: Session, bed_id: uuid.UUID) -> HospitalBed:
    bed = session.get(HospitalBed, bed_id)
    if bed is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hospital bed not found")
    return bed


def _validate_bed_location_unique(session: Session, bed: HospitalBed) -> None:
    duplicate_statement = select(HospitalBed).where(
        HospitalBed.ward == bed.ward,
        HospitalBed.room == bed.room,
        HospitalBed.bed_label == bed.bed_label,
        HospitalBed.id != bed.id,
    )
    if session.scalar(duplicate_statement) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Hospital bed location already exists",
        )


def _validate_bed_assignment(session: Session, bed: HospitalBed) -> None:
    if bed.encounter_id is None:
        if bed.status == HospitalBedStatus.OCCUPIED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Occupied bed requires an active hospitalization encounter",
            )
        return

    if bed.status != HospitalBedStatus.OCCUPIED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only occupied beds can have an encounter assignment",
        )

    encounter = session.get(ClinicalEncounter, bed.encounter_id)
    if (
        encounter is None
        or encounter.type != EncounterType.HOSPITALIZATION
        or encounter.status != EncounterStatus.IN_PROGRESS
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Bed assignment requires an active hospitalization encounter",
        )

    duplicate_statement = select(HospitalBed).where(
        HospitalBed.encounter_id == bed.encounter_id,
        HospitalBed.id != bed.id,
    )
    if session.scalar(duplicate_statement) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Encounter already has a hospital bed",
        )


def _validate_no_direct_reassignment(bed: HospitalBed, payload: HospitalBedUpdate) -> None:
    update_data = payload.model_dump(exclude_unset=True)
    if "encounter_id" not in update_data:
        return
    next_encounter_id = update_data["encounter_id"]
    if bed.encounter_id is not None and next_encounter_id not in (None, bed.encounter_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Release bed before assigning another encounter",
        )


def _bed_audit_metadata(
    session: Session,
    bed: HospitalBed,
    fields: list[str] | None = None,
    previous_encounter_id: str | None = None,
) -> dict[str, object]:
    metadata = {"status": bed.status.value}
    if fields is not None:
        metadata["fields"] = fields
    encounter_id = str(bed.encounter_id) if bed.encounter_id is not None else previous_encounter_id
    if encounter_id is not None:
        encounter = session.get(ClinicalEncounter, uuid.UUID(encounter_id))
        if encounter is not None:
            metadata["patient_id"] = str(encounter.patient_id)
            metadata["encounter_id"] = str(encounter.id)
    return metadata


@router.get("/beds", response_model=list[HospitalBedRead])
def list_hospital_beds(
    session: SessionDep,
    actor: PatientReadActorDep,
    limit: LimitQuery = 100,
) -> list[HospitalBed]:
    statement = (
        select(HospitalBed)
        .order_by(HospitalBed.ward.asc(), HospitalBed.room.asc(), HospitalBed.bed_label.asc())
        .limit(limit)
    )
    beds = list(session.scalars(statement))
    record_read_audit_event(
        session,
        action="hospital_beds.read",
        entity_type="hospital_bed_index",
        entity_id=None,
        actor_id=actor,
        metadata={"limit": limit, "result_count": len(beds)},
    )
    session.commit()
    return beds


@router.post("/beds", response_model=HospitalBedRead, status_code=status.HTTP_201_CREATED)
def create_hospital_bed(
    payload: HospitalBedCreate,
    session: SessionDep,
    actor: EncounterActorDep,
) -> HospitalBed:
    bed = HospitalBed(**payload.model_dump())
    _validate_bed_location_unique(session, bed)
    _validate_bed_assignment(session, bed)
    session.add(bed)
    session.flush()
    record_audit_event(
        session,
        action="hospital_bed.created",
        entity_type="hospital_bed",
        entity_id=bed.id,
        actor_id=actor,
        metadata=_bed_audit_metadata(session, bed),
        after=audit_snapshot(bed, HOSPITAL_BED_AUDIT_FIELDS),
    )
    session.commit()
    session.refresh(bed)
    return bed


@router.patch("/beds/{bed_id}", response_model=HospitalBedRead)
def update_hospital_bed(
    bed_id: uuid.UUID,
    payload: HospitalBedUpdate,
    session: SessionDep,
    actor: EncounterActorDep,
) -> HospitalBed:
    bed = _require_bed(session, bed_id)
    update_fields = sorted(payload.model_dump(exclude_unset=True).keys())
    before = audit_snapshot(bed, _bed_audit_fields(update_fields))
    previous_encounter_id = (
        before.get("encounter_id") if isinstance(before.get("encounter_id"), str) else None
    )
    _validate_no_direct_reassignment(bed, payload)
    fields = _apply_update(bed, payload)
    _validate_bed_location_unique(session, bed)
    _validate_bed_assignment(session, bed)
    audit_fields = _bed_audit_fields(fields)
    before_changed, after_changed = changed_field_snapshots(
        before=before,
        after_model=bed,
        fields=audit_fields,
    )
    record_audit_event(
        session,
        action="hospital_bed.updated",
        entity_type="hospital_bed",
        entity_id=bed.id,
        actor_id=actor,
        metadata=_bed_audit_metadata(session, bed, fields, previous_encounter_id),
        before=before_changed,
        after=after_changed,
    )
    session.commit()
    session.refresh(bed)
    return bed


@router.get("/active", response_model=list[HospitalizationBoardItem])
def list_active_hospitalizations(
    session: SessionDep,
    actor: PatientReadActorDep,
    limit: LimitQuery = 50,
) -> list[HospitalizationBoardItem]:
    statement = (
        select(Patient, ClinicalEncounter, HospitalBed)
        .join(ClinicalEncounter, ClinicalEncounter.patient_id == Patient.id)
        .outerjoin(HospitalBed, HospitalBed.encounter_id == ClinicalEncounter.id)
        .where(
            ClinicalEncounter.type == EncounterType.HOSPITALIZATION,
            ClinicalEncounter.status == EncounterStatus.IN_PROGRESS,
        )
        .order_by(ClinicalEncounter.started_at.desc())
        .limit(limit)
    )
    board_items = [
        HospitalizationBoardItem(patient=patient, encounter=encounter, bed=bed)
        for patient, encounter, bed in session.execute(statement).all()
    ]
    record_read_audit_event(
        session,
        action="hospitalization_board.read",
        entity_type="hospitalization_board",
        entity_id=None,
        actor_id=actor,
        metadata={"limit": limit, "result_count": len(board_items)},
    )
    session.commit()
    return board_items
