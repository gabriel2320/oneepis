from __future__ import annotations

from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

CLINICAL_TIME_ZONE = ZoneInfo("America/Santiago")


def clinical_local_date(value: datetime) -> date:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(CLINICAL_TIME_ZONE).date()
