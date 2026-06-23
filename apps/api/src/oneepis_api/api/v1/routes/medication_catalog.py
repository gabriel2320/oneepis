from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from oneepis_api.api.deps import ReadAccessDep
from oneepis_api.models.medication_catalog import MedicationCatalogItem
from oneepis_api.schemas.clinical_record import MedicationCatalogItemRead
from oneepis_api.services.medication_catalog import get_catalog_item, list_catalog_items

from .patient_shared import SessionDep

router = APIRouter(prefix="/medication-catalog", tags=["medication-catalog"])
CatalogQuery = Annotated[str | None, Query(min_length=2, max_length=80)]
CatalogLimit = Annotated[int, Query(ge=1, le=100)]


@router.get("", response_model=list[MedicationCatalogItemRead])
def list_medication_catalog(
    session: SessionDep,
    _user: ReadAccessDep,
    q: CatalogQuery = None,
    limit: CatalogLimit = 50,
) -> list[MedicationCatalogItem]:
    return list_catalog_items(session, query=q, limit=limit)


@router.get("/{catalog_item_id}", response_model=MedicationCatalogItemRead)
def get_medication_catalog_item(
    catalog_item_id: uuid.UUID,
    session: SessionDep,
    _user: ReadAccessDep,
) -> MedicationCatalogItem:
    item = get_catalog_item(session, catalog_item_id)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medication catalog item not found",
        )
    return item
