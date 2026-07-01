from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from oneepis_api.api.deps import ClinicalRiskActorDep, ReadAccessDep
from oneepis_api.models.clinical_record import ClinicalEntry, ClinicalEvent, RecordStatus, VitalSign
from oneepis_api.models.clinical_risk import (
    ClinicalRisk,
    ClinicalRiskSourceKind,
)
from oneepis_api.models.lab import LabResult
from oneepis_api.schemas.clinical_record import (
    ClinicalRiskCreate,
    ClinicalRiskRead,
    ClinicalRiskUpdate,
)
from oneepis_api.services.audit import audit_snapshot, changed_field_snapshots, record_audit_event
from oneepis_api.services.patient_scope_enforcement import enforce_patient_scope_for_read

from .patient_shared import (
    PATIENT_ROUTER_OPTIONS,
    LimitQuery,
    OffsetQuery,
    SessionDep,
    SettingsDep,
    apply_update,
    record_patient_scoped_read,
    require_patient,
    require_patient_child,
    validate_encounter_for_patient,
)

router = APIRouter(**PATIENT_ROUTER_OPTIONS)
RiskStatusQuery = Annotated[RecordStatus | None, Query(alias="status")]
CLINICAL_RISK_AUDIT_FIELDS = [
    "created_by",
    "encounter_id",
    "patient_id",
    "reviewed_at",
    "risk_type",
    "severity",
    "source_kind",
    "source_ref",
    "status",
]


def clinical_risk_audit_fields(fields: list[str]) -> list[str]:
    allowed_fields = set(CLINICAL_RISK_AUDIT_FIELDS)
    return [field for field in fields if field in allowed_fields]


@router.get("/{patient_id}/clinical-risks", response_model=list[ClinicalRiskRead])
def list_clinical_risks(
    patient_id: uuid.UUID,
    session: SessionDep,
    user: ReadAccessDep,
    settings: SettingsDep,
    limit: LimitQuery = 50,
    offset: OffsetQuery = 0,
    risk_status: RiskStatusQuery = None,
) -> list[ClinicalRisk]:
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
        action="clinical_risks.read",
    )
    filters = [ClinicalRisk.patient_id == patient_id]
    if risk_status is not None:
        filters.append(ClinicalRisk.status == risk_status)
    statement = (
        select(ClinicalRisk)
        .where(*filters)
        .order_by(ClinicalRisk.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    return list(session.scalars(statement))


@router.post(
    "/{patient_id}/clinical-risks",
    response_model=ClinicalRiskRead,
    status_code=status.HTTP_201_CREATED,
)
def create_clinical_risk(
    patient_id: uuid.UUID,
    payload: ClinicalRiskCreate,
    session: SessionDep,
    actor: ClinicalRiskActorDep,
) -> ClinicalRisk:
    require_patient(session, patient_id)
    validate_encounter_for_patient(session, patient_id, payload.encounter_id)
    _validate_risk_source(session, patient_id, payload.source_kind, payload.source_ref)
    risk = ClinicalRisk(patient_id=patient_id, created_by=actor, **payload.model_dump())
    session.add(risk)
    session.flush()
    record_audit_event(
        session,
        action="clinical_risk.created",
        entity_type="clinical_risk",
        entity_id=risk.id,
        actor_id=actor,
        metadata=_risk_metadata(patient_id, risk),
        after=audit_snapshot(risk, CLINICAL_RISK_AUDIT_FIELDS),
    )
    session.commit()
    session.refresh(risk)
    return risk


@router.get("/{patient_id}/clinical-risks/{risk_id}", response_model=ClinicalRiskRead)
def get_clinical_risk(
    patient_id: uuid.UUID,
    risk_id: uuid.UUID,
    session: SessionDep,
    user: ReadAccessDep,
    settings: SettingsDep,
) -> ClinicalRisk:
    require_patient(session, patient_id)
    enforce_patient_scope_for_read(
        session,
        patient_id=patient_id,
        actor_id=user.actor_id,
        roles=user.roles,
        settings=settings,
    )
    risk = _require_clinical_risk(session, patient_id, risk_id)
    record_patient_scoped_read(
        session,
        patient_id=patient_id,
        actor_id=user.actor_id,
        action="clinical_risk.read",
    )
    return risk


@router.patch("/{patient_id}/clinical-risks/{risk_id}", response_model=ClinicalRiskRead)
def update_clinical_risk(
    patient_id: uuid.UUID,
    risk_id: uuid.UUID,
    payload: ClinicalRiskUpdate,
    session: SessionDep,
    actor: ClinicalRiskActorDep,
) -> ClinicalRisk:
    require_patient(session, patient_id)
    risk = _require_clinical_risk(session, patient_id, risk_id)
    update_data = payload.model_dump(exclude_unset=True)
    if "encounter_id" in update_data:
        validate_encounter_for_patient(session, patient_id, payload.encounter_id)
    source_kind = update_data.get("source_kind", risk.source_kind)
    source_ref = update_data.get("source_ref", risk.source_ref)
    if "source_kind" in update_data or "source_ref" in update_data:
        _validate_risk_source(session, patient_id, source_kind, source_ref)
    update_fields = sorted(update_data.keys())
    before = audit_snapshot(risk, clinical_risk_audit_fields(update_fields))
    fields = apply_update(risk, payload)
    audit_fields = clinical_risk_audit_fields(fields)
    before_changed, after_changed = changed_field_snapshots(
        before=before,
        after_model=risk,
        fields=audit_fields,
    )
    record_audit_event(
        session,
        action="clinical_risk.updated",
        entity_type="clinical_risk",
        entity_id=risk.id,
        actor_id=actor,
        metadata=_risk_metadata(patient_id, risk) | {"fields": fields},
        before=before_changed,
        after=after_changed,
    )
    session.commit()
    session.refresh(risk)
    return risk


def _require_clinical_risk(
    session: Session,
    patient_id: uuid.UUID,
    risk_id: uuid.UUID,
) -> ClinicalRisk:
    return require_patient_child(
        session,
        ClinicalRisk,
        risk_id,
        patient_id,
        "Clinical risk not found",
    )


def _validate_risk_source(
    session: Session,
    patient_id: uuid.UUID,
    source_kind: ClinicalRiskSourceKind,
    source_ref: str | None,
) -> None:
    if source_kind == ClinicalRiskSourceKind.MANUAL:
        return
    if not source_ref:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Source required",
        )
    try:
        source_id = uuid.UUID(source_ref)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Source reference must be a UUID",
        ) from exc
    source_models: dict[ClinicalRiskSourceKind, type] = {
        ClinicalRiskSourceKind.VITAL_SIGN: VitalSign,
        ClinicalRiskSourceKind.CLINICAL_EVENT: ClinicalEvent,
        ClinicalRiskSourceKind.CLINICAL_ENTRY: ClinicalEntry,
        ClinicalRiskSourceKind.LAB_RESULT: LabResult,
    }
    source_model = source_models[source_kind]
    require_patient_child(session, source_model, source_id, patient_id, "Risk source not found")


def _risk_metadata(patient_id: uuid.UUID, risk: ClinicalRisk) -> dict[str, str]:
    return {
        "patient_id": str(patient_id),
        "risk_id": str(risk.id),
        "risk_type": risk.risk_type.value,
        "severity": risk.severity.value,
        "status": risk.status.value,
        "source_kind": risk.source_kind.value,
    }
