from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from oneepis_api.api.deps import (
    HospitalDailySheetActorDep,
    ReadAccessDep,
    require_patient_read_access,
)
from oneepis_api.api.v1.routes.patient_shared import (
    apply_update,
    record_patient_scoped_read,
    require_patient,
)
from oneepis_api.core.config import Settings, get_settings
from oneepis_api.db.session import get_session
from oneepis_api.models.clinical_record import (
    ClinicalEncounter,
    EncounterStatus,
    EncounterType,
)
from oneepis_api.models.hospitalization import HospitalDailySheet, HospitalDailySheetStatus
from oneepis_api.schemas.hospitalization import (
    HospitalDailySheetCreate,
    HospitalDailySheetRead,
    HospitalDailySheetUpdate,
)
from oneepis_api.services.audit import (
    audit_snapshot,
    changed_field_snapshots,
    record_audit_event,
)
from oneepis_api.services.clinical_dates import clinical_local_date
from oneepis_api.services.patient_scope_enforcement import enforce_patient_scope_for_read

router = APIRouter(
    prefix="/hospitalization",
    tags=["hospitalization"],
    dependencies=[Depends(require_patient_read_access)],
)
SessionDep = Annotated[Session, Depends(get_session)]
SettingsDep = Annotated[Settings, Depends(get_settings)]
LimitQuery = Annotated[int, Query(ge=1, le=100)]
HOSPITAL_DAILY_SHEET_AUDIT_FIELDS = [
    "created_by",
    "encounter_id",
    "patient_id",
    "sheet_date",
    "status",
]


@router.get("/patients/{patient_id}/daily-sheets", response_model=list[HospitalDailySheetRead])
def list_hospital_daily_sheets(
    patient_id: uuid.UUID,
    session: SessionDep,
    user: ReadAccessDep,
    settings: SettingsDep,
    limit: LimitQuery = 30,
) -> list[HospitalDailySheet]:
    require_patient(session, patient_id)
    enforce_patient_scope_for_read(
        session,
        patient_id=patient_id,
        actor_id=user.actor_id,
        roles=user.roles,
        settings=settings,
    )
    record_patient_scoped_read(
        session,
        patient_id=patient_id,
        actor_id=user.actor_id,
        action="hospital_daily_sheets.read",
    )
    statement = (
        select(HospitalDailySheet)
        .where(HospitalDailySheet.patient_id == patient_id)
        .order_by(HospitalDailySheet.sheet_date.desc(), HospitalDailySheet.created_at.desc())
        .limit(limit)
    )
    return list(session.scalars(statement))


@router.post(
    "/patients/{patient_id}/daily-sheets",
    response_model=HospitalDailySheetRead,
    status_code=status.HTTP_201_CREATED,
)
def create_hospital_daily_sheet(
    patient_id: uuid.UUID,
    payload: HospitalDailySheetCreate,
    session: SessionDep,
    actor: HospitalDailySheetActorDep,
) -> HospitalDailySheet:
    encounter = _require_active_hospitalization(session, patient_id)
    sheet = HospitalDailySheet(
        **payload.model_dump(),
        patient_id=patient_id,
        encounter_id=encounter.id,
        created_by=actor,
    )
    _validate_daily_sheet_date_for_encounter(sheet, encounter)
    _validate_daily_sheet_unique(session, sheet)
    session.add(sheet)
    session.flush()
    record_audit_event(
        session,
        action="hospital_daily_sheet.created",
        entity_type="hospital_daily_sheet",
        entity_id=sheet.id,
        actor_id=actor,
        metadata=_daily_sheet_audit_metadata(sheet),
        after=audit_snapshot(sheet, HOSPITAL_DAILY_SHEET_AUDIT_FIELDS),
    )
    session.commit()
    session.refresh(sheet)
    return sheet


@router.patch(
    "/patients/{patient_id}/daily-sheets/{sheet_id}",
    response_model=HospitalDailySheetRead,
)
def update_hospital_daily_sheet(
    patient_id: uuid.UUID,
    sheet_id: uuid.UUID,
    payload: HospitalDailySheetUpdate,
    session: SessionDep,
    actor: HospitalDailySheetActorDep,
) -> HospitalDailySheet:
    sheet = _require_daily_sheet(session, patient_id, sheet_id)
    _validate_daily_sheet_editable(sheet)
    fields = sorted(payload.model_dump(exclude_unset=True).keys())
    audit_fields = _daily_sheet_audit_fields(fields)
    before = audit_snapshot(sheet, audit_fields) if audit_fields else {}
    changed_fields = apply_update(sheet, payload)
    _validate_daily_sheet_date_for_encounter(sheet, sheet.encounter)
    _validate_daily_sheet_unique(session, sheet)
    audit_changed_fields = _daily_sheet_audit_fields(changed_fields)
    if audit_changed_fields:
        before_changed, after_changed = changed_field_snapshots(
            before=before,
            after_model=sheet,
            fields=audit_changed_fields,
        )
    else:
        before_changed, after_changed = {}, {}
    record_audit_event(
        session,
        action="hospital_daily_sheet.updated",
        entity_type="hospital_daily_sheet",
        entity_id=sheet.id,
        actor_id=actor,
        metadata=_daily_sheet_audit_metadata(sheet, changed_fields),
        before=before_changed,
        after=after_changed,
    )
    session.commit()
    session.refresh(sheet)
    return sheet


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
            detail="Daily sheet requires an active hospitalization encounter",
        )
    return encounter


def _require_daily_sheet(
    session: Session,
    patient_id: uuid.UUID,
    sheet_id: uuid.UUID,
) -> HospitalDailySheet:
    sheet = session.get(HospitalDailySheet, sheet_id)
    if sheet is None or sheet.patient_id != patient_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hospital daily sheet not found",
        )
    return sheet


def _validate_daily_sheet_unique(session: Session, sheet: HospitalDailySheet) -> None:
    duplicate_statement = select(HospitalDailySheet).where(
        HospitalDailySheet.encounter_id == sheet.encounter_id,
        HospitalDailySheet.sheet_date == sheet.sheet_date,
        HospitalDailySheet.id != sheet.id,
    )
    if session.scalar(duplicate_statement) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Daily sheet already exists for this hospitalization date",
        )


def _validate_daily_sheet_date_for_encounter(
    sheet: HospitalDailySheet,
    encounter: ClinicalEncounter,
) -> None:
    encounter_started_on = clinical_local_date(encounter.started_at)
    if sheet.sheet_date < encounter_started_on:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Daily sheet date cannot be before hospitalization start",
        )
    if encounter.ended_at is None:
        return
    encounter_ended_on = clinical_local_date(encounter.ended_at)
    if sheet.sheet_date > encounter_ended_on:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Daily sheet date cannot be after hospitalization end",
        )


def _validate_daily_sheet_editable(sheet: HospitalDailySheet) -> None:
    if sheet.status == HospitalDailySheetStatus.CLOSED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Closed daily sheets cannot be edited",
        )


def _daily_sheet_audit_metadata(
    sheet: HospitalDailySheet,
    fields: list[str] | None = None,
) -> dict[str, object]:
    metadata: dict[str, object] = {
        "patient_id": str(sheet.patient_id),
        "encounter_id": str(sheet.encounter_id),
        "sheet_date": sheet.sheet_date.isoformat(),
        "status": sheet.status.value,
    }
    if fields is not None:
        metadata["fields"] = fields
    return metadata


def _daily_sheet_audit_fields(fields: list[str]) -> list[str]:
    return [field for field in fields if field in HOSPITAL_DAILY_SHEET_AUDIT_FIELDS]
