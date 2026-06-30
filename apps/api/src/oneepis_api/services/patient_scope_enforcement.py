from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from oneepis_api.core.config import Settings
from oneepis_api.services.access_context_audit import (
    record_denied_patient_access_context_decision,
)
from oneepis_api.services.auth import UserRole
from oneepis_api.services.patient_access_relationship import (
    resolve_patient_access_relationship_dry_run,
)

PATIENT_SCOPE_DENIAL_DETAIL = "Patient access is outside the active care relationship."
PATIENT_SCOPE_DENIAL_REASON = (
    "missing_abac_requirement:active_care_relationship_or_access_reason"
)
PATIENT_SCOPE_BREAKOUT_ROLES = frozenset({UserRole.ADMIN, UserRole.DEV})


def enforce_patient_scope_for_read(
    session: Session,
    *,
    patient_id: uuid.UUID,
    actor_id: str,
    roles: frozenset[UserRole],
    settings: Settings,
) -> None:
    if not settings.abac_enforcement_enabled:
        return
    if roles.intersection(PATIENT_SCOPE_BREAKOUT_ROLES):
        return

    patient_scope = resolve_patient_access_relationship_dry_run(
        session,
        actor_id=actor_id,
        patient_id=patient_id,
    )
    if patient_scope.resolved:
        return

    record_denied_patient_access_context_decision(
        session,
        patient_id=patient_id,
        actor_id=actor_id,
        denial_reasons=(PATIENT_SCOPE_DENIAL_REASON,),
        runtime_enforced=True,
    )
    session.commit()
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=PATIENT_SCOPE_DENIAL_DETAIL,
    )
