from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from oneepis_api.core.config import Settings
from oneepis_api.services.auth import AuthenticatedUser
from oneepis_api.services.patient_scope_enforcement import enforce_patient_scope_for_read

from .patient_shared import record_patient_scoped_read


def enforce_and_record_assistant_read(
    session: Session,
    *,
    patient_id: uuid.UUID,
    user: AuthenticatedUser,
    settings: Settings,
    action: str,
) -> None:
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
        action=action,
    )
