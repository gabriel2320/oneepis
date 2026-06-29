from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from oneepis_api.api.deps import EncounterActorDep
from oneepis_api.models.clinical_order import ClinicalOrder, ClinicalOrderStatus
from oneepis_api.models.clinical_record import ClinicalEncounter
from oneepis_api.schemas.clinical_order import (
    ClinicalOrderCreate,
    ClinicalOrderRead,
    ClinicalOrderUpdate,
)
from oneepis_api.services.audit import (
    audit_snapshot,
    changed_field_snapshots,
    record_audit_event,
)

from .patient_shared import (
    PATIENT_ROUTER_OPTIONS,
    LimitQuery,
    SessionDep,
    apply_update,
    require_patient,
)

router = APIRouter(**PATIENT_ROUTER_OPTIONS)
CLINICAL_ORDER_AUDIT_FIELDS = [
    "created_by",
    "encounter_id",
    "kind",
    "ordered_at",
    "patient_id",
    "status",
]


def clinical_order_audit_fields(fields: list[str]) -> list[str]:
    allowed_fields = set(CLINICAL_ORDER_AUDIT_FIELDS)
    return [field for field in fields if field in allowed_fields]


@router.get("/{patient_id}/clinical-orders", response_model=list[ClinicalOrderRead])
def list_clinical_orders(
    patient_id: uuid.UUID,
    session: SessionDep,
    limit: LimitQuery = 50,
) -> list[ClinicalOrder]:
    require_patient(session, patient_id)
    statement = (
        select(ClinicalOrder)
        .where(ClinicalOrder.patient_id == patient_id)
        .order_by(ClinicalOrder.ordered_at.desc(), ClinicalOrder.created_at.desc())
        .limit(limit)
    )
    return list(session.scalars(statement))


@router.post(
    "/{patient_id}/clinical-orders",
    response_model=ClinicalOrderRead,
    status_code=status.HTTP_201_CREATED,
)
def create_clinical_order(
    patient_id: uuid.UUID,
    payload: ClinicalOrderCreate,
    session: SessionDep,
    actor: EncounterActorDep,
) -> ClinicalOrder:
    encounter = _require_patient_encounter(session, patient_id, payload.encounter_id)
    order = ClinicalOrder(
        patient_id=patient_id,
        encounter_id=encounter.id,
        kind=payload.kind,
        ordered_at=payload.ordered_at,
        title=payload.title,
        order_text=payload.order_text,
        rationale=payload.rationale,
        created_by=actor,
    )
    session.add(order)
    session.flush()
    record_audit_event(
        session,
        action="clinical_order.created",
        entity_type="clinical_order",
        entity_id=order.id,
        actor_id=actor,
        metadata=_clinical_order_audit_metadata(order),
        after=audit_snapshot(order, CLINICAL_ORDER_AUDIT_FIELDS),
    )
    session.commit()
    session.refresh(order)
    return order


@router.patch(
    "/{patient_id}/clinical-orders/{order_id}",
    response_model=ClinicalOrderRead,
)
def update_clinical_order(
    patient_id: uuid.UUID,
    order_id: uuid.UUID,
    payload: ClinicalOrderUpdate,
    session: SessionDep,
    actor: EncounterActorDep,
) -> ClinicalOrder:
    order = _require_clinical_order(session, patient_id, order_id)
    _validate_clinical_order_editable(order, payload)
    fields = sorted(payload.model_dump(exclude_unset=True).keys())
    before = audit_snapshot(order, clinical_order_audit_fields(fields))
    changed_fields = apply_update(order, payload)
    audit_fields = clinical_order_audit_fields(changed_fields)
    before_changed, after_changed = changed_field_snapshots(
        before=before,
        after_model=order,
        fields=audit_fields,
    )
    record_audit_event(
        session,
        action="clinical_order.updated",
        entity_type="clinical_order",
        entity_id=order.id,
        actor_id=actor,
        metadata=_clinical_order_audit_metadata(order, changed_fields),
        before=before_changed,
        after=after_changed,
    )
    session.commit()
    session.refresh(order)
    return order


def _require_patient_encounter(
    session: SessionDep,
    patient_id: uuid.UUID,
    encounter_id: uuid.UUID,
) -> ClinicalEncounter:
    require_patient(session, patient_id)
    encounter = session.get(ClinicalEncounter, encounter_id)
    if encounter is None or encounter.patient_id != patient_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Encounter not found",
        )
    return encounter


def _require_clinical_order(
    session: SessionDep,
    patient_id: uuid.UUID,
    order_id: uuid.UUID,
) -> ClinicalOrder:
    order = session.get(ClinicalOrder, order_id)
    if order is None or order.patient_id != patient_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clinical order not found",
        )
    return order


def _validate_clinical_order_editable(
    order: ClinicalOrder,
    payload: ClinicalOrderUpdate,
) -> None:
    if order.status != ClinicalOrderStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only draft clinical orders can be edited",
        )
    update_fields = payload.model_dump(exclude_unset=True)
    content_fields = set(update_fields) - {"status"}
    if content_fields and payload.status in {
        ClinicalOrderStatus.CANCELLED,
        ClinicalOrderStatus.ENTERED_IN_ERROR,
    }:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Clinical order content and terminal status cannot be updated together",
        )


def _clinical_order_audit_metadata(
    order: ClinicalOrder,
    fields: list[str] | None = None,
) -> dict[str, object]:
    metadata: dict[str, object] = {
        "patient_id": str(order.patient_id),
        "encounter_id": str(order.encounter_id),
        "status": order.status.value,
        "kind": order.kind.value,
    }
    if fields is not None:
        metadata["fields"] = fields
    return metadata
