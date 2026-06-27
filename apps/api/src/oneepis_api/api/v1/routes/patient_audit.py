from __future__ import annotations

import uuid

from fastapi import APIRouter
from sqlalchemy import select

from oneepis_api.models.audit import AuditEvent
from oneepis_api.schemas.audit import AuditEventRead

from .patient_shared import PATIENT_ROUTER_OPTIONS, LimitQuery, SessionDep, require_patient

router = APIRouter(**PATIENT_ROUTER_OPTIONS)


@router.get("/{patient_id}/audit-events", response_model=list[AuditEventRead])
def list_patient_audit_events(
    patient_id: uuid.UUID,
    session: SessionDep,
    limit: LimitQuery = 50,
) -> list[AuditEvent]:
    require_patient(session, patient_id)
    statement = select(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(limit * 4)
    events = list(session.scalars(statement))
    patient_id_text = str(patient_id)
    matched = [
        event
        for event in events
        if (
            event.entity_type in {"patient", "patient_access"}
            and event.entity_id == patient_id
        )
        or str(event.extra_data.get("patient_id")) == patient_id_text
    ]
    return matched[:limit]
