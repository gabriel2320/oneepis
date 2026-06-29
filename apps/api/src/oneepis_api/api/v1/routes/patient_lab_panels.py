from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from oneepis_api.api.deps import LabResultActorDep, PatientReadActorDep
from oneepis_api.models.lab import LabPanel, LabResult
from oneepis_api.schemas.clinical_record import (
    LabPanelCreate,
    LabPanelRead,
    LabPanelUpdate,
    LabResultRead,
    LabResultUpdate,
)
from oneepis_api.services.audit import audit_snapshot, changed_field_snapshots, record_audit_event
from oneepis_api.services.lab_result_source import serialize_lab_panel, serialize_lab_result

from .patient_shared import (
    PATIENT_ROUTER_OPTIONS,
    LimitQuery,
    OffsetQuery,
    SessionDep,
    apply_update,
    record_patient_scoped_read,
    require_patient,
    require_patient_child,
    validate_encounter_for_patient,
)

router = APIRouter(**PATIENT_ROUTER_OPTIONS)


@router.get("/{patient_id}/lab-panels", response_model=list[LabPanelRead])
def list_lab_panels(
    patient_id: uuid.UUID,
    session: SessionDep,
    actor: PatientReadActorDep,
    limit: LimitQuery = 50,
    offset: OffsetQuery = 0,
) -> list[LabPanel]:
    require_patient(session, patient_id)
    record_patient_scoped_read(
        session,
        patient_id=patient_id,
        actor_id=actor,
        action="lab_panels.read",
    )
    statement = (
        select(LabPanel)
        .options(selectinload(LabPanel.results))
        .where(LabPanel.patient_id == patient_id)
        .order_by(LabPanel.occurred_at.desc())
        .offset(offset)
        .limit(limit)
    )
    return [serialize_lab_panel(panel) for panel in session.scalars(statement)]


@router.post(
    "/{patient_id}/lab-panels",
    response_model=LabPanelRead,
    status_code=status.HTTP_201_CREATED,
)
def create_lab_panel(
    patient_id: uuid.UUID,
    payload: LabPanelCreate,
    session: SessionDep,
    actor: LabResultActorDep,
) -> LabPanel:
    require_patient(session, patient_id)
    validate_encounter_for_patient(session, patient_id, payload.encounter_id)
    panel_data = payload.model_dump(exclude={"results"})
    panel_data["created_by"] = actor
    panel = LabPanel(patient_id=patient_id, **panel_data)
    panel.results = [
        LabResult(patient_id=patient_id, **result.model_dump()) for result in payload.results
    ]
    session.add(panel)
    session.flush()
    record_audit_event(
        session,
        action="lab_panel.created",
        entity_type="lab_panel",
        entity_id=panel.id,
        actor_id=actor,
        metadata={"patient_id": str(patient_id), "result_count": len(panel.results)},
        after=audit_snapshot(panel),
    )
    session.commit()
    session.refresh(panel)
    return serialize_lab_panel(panel)


@router.get("/{patient_id}/lab-panels/{panel_id}", response_model=LabPanelRead)
def get_lab_panel(
    patient_id: uuid.UUID,
    panel_id: uuid.UUID,
    session: SessionDep,
    actor: PatientReadActorDep,
) -> LabPanelRead:
    require_patient(session, patient_id)
    panel = _require_lab_panel(session, patient_id, panel_id)
    record_patient_scoped_read(
        session,
        patient_id=patient_id,
        actor_id=actor,
        action="lab_panel.read",
    )
    return serialize_lab_panel(panel)


@router.patch("/{patient_id}/lab-panels/{panel_id}", response_model=LabPanelRead)
def update_lab_panel(
    patient_id: uuid.UUID,
    panel_id: uuid.UUID,
    payload: LabPanelUpdate,
    session: SessionDep,
    actor: LabResultActorDep,
) -> LabPanel:
    require_patient(session, patient_id)
    panel = _require_lab_panel(session, patient_id, panel_id)
    if "encounter_id" in payload.model_dump(exclude_unset=True):
        validate_encounter_for_patient(session, patient_id, payload.encounter_id)
    update_fields = sorted(payload.model_dump(exclude_unset=True).keys())
    before = audit_snapshot(panel, update_fields)
    fields = apply_update(panel, payload)
    before_changed, after_changed = changed_field_snapshots(
        before=before,
        after_model=panel,
        fields=fields,
    )
    record_audit_event(
        session,
        action="lab_panel.updated",
        entity_type="lab_panel",
        entity_id=panel.id,
        actor_id=actor,
        metadata={"patient_id": str(patient_id), "panel_id": str(panel.id), "fields": fields},
        before=before_changed,
        after=after_changed,
    )
    session.commit()
    session.refresh(panel)
    return serialize_lab_panel(panel)


@router.get(
    "/{patient_id}/lab-panels/{panel_id}/results/{result_id}",
    response_model=LabResultRead,
)
def get_lab_result(
    patient_id: uuid.UUID,
    panel_id: uuid.UUID,
    result_id: uuid.UUID,
    session: SessionDep,
    actor: PatientReadActorDep,
) -> LabResultRead:
    require_patient(session, patient_id)
    panel = _require_lab_panel(session, patient_id, panel_id)
    result = _require_lab_result(session, patient_id, panel_id, result_id)
    record_patient_scoped_read(
        session,
        patient_id=patient_id,
        actor_id=actor,
        action="lab_result.read",
    )
    return serialize_lab_result(panel, result)


@router.patch(
    "/{patient_id}/lab-panels/{panel_id}/results/{result_id}",
    response_model=LabResultRead,
)
def update_lab_result(
    patient_id: uuid.UUID,
    panel_id: uuid.UUID,
    result_id: uuid.UUID,
    payload: LabResultUpdate,
    session: SessionDep,
    actor: LabResultActorDep,
) -> LabResult:
    require_patient(session, patient_id)
    _require_lab_panel(session, patient_id, panel_id)
    result = _require_lab_result(session, patient_id, panel_id, result_id)
    update_fields = sorted(payload.model_dump(exclude_unset=True).keys())
    before = audit_snapshot(result, update_fields)
    fields = apply_update(result, payload)
    before_changed, after_changed = changed_field_snapshots(
        before=before,
        after_model=result,
        fields=fields,
    )
    record_audit_event(
        session,
        action="lab_result.updated",
        entity_type="lab_result",
        entity_id=result.id,
        actor_id=actor,
        metadata={
            "patient_id": str(patient_id),
            "panel_id": str(panel_id),
            "result_id": str(result.id),
            "fields": fields,
        },
        before=before_changed,
        after=after_changed,
    )
    session.commit()
    session.refresh(result)
    panel = _require_lab_panel(session, patient_id, panel_id)
    return serialize_lab_result(panel, result)


def _require_lab_panel(
    session: Session,
    patient_id: uuid.UUID,
    panel_id: uuid.UUID,
) -> LabPanel:
    statement = (
        select(LabPanel)
        .options(selectinload(LabPanel.results))
        .where(LabPanel.id == panel_id)
    )
    panel = session.scalar(statement)
    if panel is None or panel.patient_id != patient_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lab panel not found")
    return panel


def _require_lab_result(
    session: Session,
    patient_id: uuid.UUID,
    panel_id: uuid.UUID,
    result_id: uuid.UUID,
) -> LabResult:
    result = require_patient_child(
        session,
        LabResult,
        result_id,
        patient_id,
        "Lab result not found",
    )
    if result.panel_id != panel_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lab result not found")
    return result
