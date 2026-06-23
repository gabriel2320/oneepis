from __future__ import annotations

import uuid
from contextvars import ContextVar
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from sqlalchemy import inspect
from sqlalchemy.orm import Session

from oneepis_api.models.audit import AuditEvent


@dataclass(frozen=True)
class AuditRequestContext:
    correlation_id: str
    request_method: str
    request_path: str


_audit_request_context: ContextVar[AuditRequestContext | None] = ContextVar(
    "audit_request_context",
    default=None,
)


def set_audit_request_context(context: AuditRequestContext) -> None:
    _audit_request_context.set(context)


def clear_audit_request_context() -> None:
    _audit_request_context.set(None)


def get_audit_request_context() -> AuditRequestContext | None:
    return _audit_request_context.get()


def record_audit_event(
    session: Session,
    *,
    action: str,
    entity_type: str,
    entity_id: uuid.UUID | None,
    actor_id: str = "system",
    metadata: dict[str, Any] | None = None,
    before: dict[str, Any] | None = None,
    after: dict[str, Any] | None = None,
) -> None:
    context = _audit_request_context.get()
    extra_data = metadata.copy() if metadata else {}
    if before is not None:
        extra_data["before"] = before
    if after is not None:
        extra_data["after"] = after

    session.add(
        AuditEvent(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            actor_id=actor_id,
            correlation_id=context.correlation_id if context else None,
            request_method=context.request_method if context else None,
            request_path=context.request_path if context else None,
            extra_data=extra_data,
        )
    )


def audit_snapshot(model: object, fields: list[str] | None = None) -> dict[str, Any]:
    mapper = inspect(model).mapper
    allowed_fields = set(fields) if fields else None
    snapshot: dict[str, Any] = {}
    for attr in mapper.column_attrs:
        field = attr.key
        if allowed_fields is not None and field not in allowed_fields:
            continue
        snapshot[field] = _jsonable(getattr(model, field))
    return snapshot


def changed_field_snapshots(
    *,
    before: dict[str, Any],
    after_model: object,
    fields: list[str],
) -> tuple[dict[str, Any], dict[str, Any]]:
    after = audit_snapshot(after_model, fields)
    return (
        {field: before.get(field) for field in fields},
        {field: after.get(field) for field in fields},
    )


def _jsonable(value: Any) -> Any:
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, datetime | date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    return value
