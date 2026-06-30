from __future__ import annotations

import uuid

from fastapi import APIRouter
from sqlalchemy import or_, select

from oneepis_api.api.deps import AuditReadAccessDep
from oneepis_api.models.audit import AuditEvent
from oneepis_api.schemas.audit import AuditEventPublicRead
from oneepis_api.services.audit import record_audit_event

from .patient_shared import LimitQuery, SessionDep, require_patient

router = APIRouter(
    prefix="/patients",
    tags=["patients"],
)


@router.get("/{patient_id}/audit-events", response_model=list[AuditEventPublicRead])
def list_patient_audit_events(
    patient_id: uuid.UUID,
    session: SessionDep,
    user: AuditReadAccessDep,
    limit: LimitQuery = 50,
) -> list[AuditEventPublicRead]:
    require_patient(session, patient_id)
    patient_id_text = str(patient_id)
    statement = (
        select(AuditEvent)
        .where(
            or_(
                (AuditEvent.entity_type == "patient") & (AuditEvent.entity_id == patient_id),
                AuditEvent.extra_data["patient_id"].as_string() == patient_id_text,
            )
        )
        .order_by(AuditEvent.created_at.desc())
        .limit(limit)
    )
    events = [AuditEventPublicRead.model_validate(event) for event in session.scalars(statement)]
    record_audit_event(
        session,
        action="patient_audit.read",
        entity_type="patient",
        entity_id=patient_id,
        actor_id=user.actor_id,
        metadata={"patient_id": patient_id_text},
    )
    session.commit()
    return events
