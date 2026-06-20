from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from oneepis_api.api.deps import require_patient_read_access
from oneepis_api.db.session import get_session
from oneepis_api.models.clinical_record import (
    ClinicalEncounter,
    EncounterStatus,
    EncounterType,
)
from oneepis_api.models.patient import Patient
from oneepis_api.schemas.hospitalization import HospitalizationBoardItem

router = APIRouter(
    prefix="/hospitalization",
    tags=["hospitalization"],
    dependencies=[Depends(require_patient_read_access)],
)
SessionDep = Annotated[Session, Depends(get_session)]
LimitQuery = Annotated[int, Query(ge=1, le=100)]


@router.get("/active", response_model=list[HospitalizationBoardItem])
def list_active_hospitalizations(
    session: SessionDep,
    limit: LimitQuery = 50,
) -> list[HospitalizationBoardItem]:
    statement = (
        select(Patient, ClinicalEncounter)
        .join(ClinicalEncounter, ClinicalEncounter.patient_id == Patient.id)
        .where(
            ClinicalEncounter.type == EncounterType.HOSPITALIZATION,
            ClinicalEncounter.status == EncounterStatus.IN_PROGRESS,
        )
        .order_by(ClinicalEncounter.started_at.desc())
        .limit(limit)
    )
    return [
        HospitalizationBoardItem(patient=patient, encounter=encounter)
        for patient, encounter in session.execute(statement).all()
    ]
