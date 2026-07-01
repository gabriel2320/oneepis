from __future__ import annotations

from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from oneepis_api.models.clinical_record import Medication
from oneepis_api.schemas.clinical_record import (
    MedicationCreate,
    MedicationDraftValidationRequest,
    MedicationUpdate,
)
from oneepis_api.services.medication_catalog import (
    get_catalog_item,
    medication_dose_snapshot,
)


def validated_dose_snapshot(session: Session, payload: MedicationCreate) -> dict[str, Any]:
    if payload.catalog_item_id and get_catalog_item(session, payload.catalog_item_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medication catalog item not found",
        )
    validation_payload = MedicationDraftValidationRequest(
        catalog_item_id=payload.catalog_item_id,
        name=payload.name,
        dose=payload.dose,
        route=payload.route,
        frequency=payload.frequency,
    )
    snapshot = medication_dose_snapshot(session, validation_payload)
    if snapshot.get("blocking") and not payload.dose_override_reason:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=snapshot)
    return snapshot


def updated_dose_snapshot(
    session: Session,
    medication: Medication,
    payload: MedicationUpdate,
) -> dict[str, Any] | None:
    update_data = payload.model_dump(exclude_unset=True)
    relevant_fields = {"catalog_item_id", "name", "dose", "route", "frequency"}
    if not relevant_fields.intersection(update_data):
        return None
    validation_payload = MedicationDraftValidationRequest(
        catalog_item_id=update_data.get("catalog_item_id", medication.catalog_item_id),
        name=update_data.get("name", medication.name),
        dose=update_data.get("dose", medication.dose),
        route=update_data.get("route", medication.route),
        frequency=update_data.get("frequency", medication.frequency),
    )
    if (
        validation_payload.catalog_item_id
        and get_catalog_item(session, validation_payload.catalog_item_id) is None
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medication catalog item not found",
        )
    snapshot = medication_dose_snapshot(session, validation_payload)
    override_reason = update_data.get("dose_override_reason", medication.dose_override_reason)
    if snapshot.get("blocking") and not override_reason:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=snapshot)
    return snapshot
