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
    extra_data: dict[str, Any]
    created_at: datetime
