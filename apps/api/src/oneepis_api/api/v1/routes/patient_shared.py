from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from oneepis_api.api.deps import require_patient_read_access
from oneepis_api.core.config import Settings, get_settings
from oneepis_api.db.session import get_session
from oneepis_api.models.clinical_record import ClinicalEncounter, EncounterType
from oneepis_api.models.patient import Patient
from oneepis_api.repositories import patients as patient_repo

SessionDep = Annotated[Session, Depends(get_session)]
SettingsDep = Annotated[Settings, Depends(get_settings)]
PatientSearch = Annotated[str | None, Query(min_length=2, max_length=80)]
LimitQuery = Annotated[int, Query(ge=1, le=100)]
OffsetQuery = Annotated[int, Query(ge=0)]
PATIENT_ROUTER_OPTIONS = {
    "prefix": "/patients",
    "tags": ["patients"],
    "dependencies": [Depends(require_patient_read_access)],
}
FOREIGN_PROJECT_PATIENT_TERMS = ("evolab", "pacmed")


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


def validate_encounter_for_patient(
    session: Session,
    patient_id: uuid.UUID,
    encounter_id: uuid.UUID | None,
) -> None:
    if encounter_id is None:
        return
    require_patient_child(
        session,
        ClinicalEncounter,
        encounter_id,
        patient_id,
        "Encounter not found",
    )


def require_encounter_for_patient(
    session: Session,
    patient_id: uuid.UUID,
    encounter_id: uuid.UUID,
    *,
    expected_type: EncounterType | None = None,
    detail: str = "Encounter not found",
) -> ClinicalEncounter:
    encounter = require_patient_child(
        session,
        ClinicalEncounter,
        encounter_id,
        patient_id,
        detail,
    )
    if expected_type is not None and encounter.type != expected_type:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Encounter must be {expected_type.value}",
        )
    return encounter


def apply_update(model: object, payload: object) -> list[str]:
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(model, field, value)
    return sorted(update_data.keys())


def validate_development_patient_data(settings: Settings, payload: object) -> None:
    if settings.environment.strip().lower() != "development":
        return

    data = payload.model_dump(exclude_unset=True)
    values = [
        str(data.get(field) or "")
        for field in ("first_name", "last_name", "preferred_name", "clinical_identifier")
    ]
    normalized = " ".join(values).lower()
    matches = [term for term in FOREIGN_PROJECT_PATIENT_TERMS if term in normalized]
    if not matches:
        return

    raise HTTPException(
        status_code=422,
        detail=(
            "Local development patient data appears to contain foreign project "
            f"fixture terms: {', '.join(matches)}"
        ),
    )
