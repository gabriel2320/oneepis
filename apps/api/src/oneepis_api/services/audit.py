from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from oneepis_api.models.audit import AuditEvent


def record_audit_event(
    session: Session,
    *,
    action: str,
    entity_type: str,
    entity_id: uuid.UUID | None,
    actor_id: str = "system",
    metadata: dict[str, Any] | None = None,
) -> None:
    session.add(
        AuditEvent(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            actor_id=actor_id,
            extra_data=metadata or {},
        )
    )
