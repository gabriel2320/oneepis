from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import or_, select

from oneepis_api.api.deps import require_audit_read_access
from oneepis_api.models.audit import AuditEvent
from oneepis_api.schemas.audit import AuditEventPublicRead

from .patient_shared import LimitQuery, SessionDep, require_patient

router = APIRouter(
    prefix="/patients",
    tags=["patients"],
    dependencies=[Depends(require_audit_read_access)],
)


@router.get("/{patient_id}/audit-events", response_model=list[AuditEventPublicRead])
def list_patient_audit_events(
    patient_id: uuid.UUID,
    session: SessionDep,
    limit: LimitQuery = 50,
) -> list[AuditEvent]:
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
    return list(session.scalars(statement))
