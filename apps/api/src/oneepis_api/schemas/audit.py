from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from oneepis_api.schemas.common import APIModel


class AuditEventRead(APIModel):
    id: uuid.UUID
    action: str
    entity_type: str
    entity_id: uuid.UUID | None
    actor_id: str
    correlation_id: str | None = None
    request_method: str | None = None
    request_path: str | None = None
    extra_data: dict[str, Any]
    created_at: datetime
