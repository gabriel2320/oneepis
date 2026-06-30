from __future__ import annotations

import uuid
from typing import Literal

from sqlalchemy.orm import Session

from oneepis_api.core.access_context_contract import access_context_requirement_keys
from oneepis_api.core.access_context_runtime import AccessContext, evaluate_access_context
from oneepis_api.services.audit import record_audit_event

PASSIVE_ACCESS_CONTEXT_DECISION_ACTION = "access_context.passive_decision"


def record_passive_patient_access_context_decision(
    session: Session,
    *,
    patient_id: uuid.UUID,
    actor_id: str,
    source_action: str,
) -> None:
    context = AccessContext(
        actor_id=actor_id,
        role_names=(),
        source="rbac_only",
        missing_abac_requirements=access_context_requirement_keys(),
    )
    decision = evaluate_access_context(context)
    record_audit_event(
        session,
        action=PASSIVE_ACCESS_CONTEXT_DECISION_ACTION,
        entity_type="patient",
        entity_id=patient_id,
        actor_id=actor_id,
        metadata={
            "mode": "passive",
            "source_action": source_action,
            "policy": decision.policy,
            "runtime_enforced": decision.runtime_enforced,
            "allowed": decision.allowed,
            "would_deny_if_enforced": decision.would_deny_if_enforced,
            "denial_reason_count": len(decision.denial_reasons),
            "denial_reason_keys": _denial_reason_keys(decision.denial_reasons),
            "metadata_retention": decision.metadata_retention,
        },
    )


def _denial_reason_keys(denial_reasons: tuple[str, ...]) -> tuple[str, ...]:
    prefix: Literal["missing_abac_requirement:"] = "missing_abac_requirement:"
    return tuple(
        reason.removeprefix(prefix)
        for reason in denial_reasons
        if reason.startswith(prefix)
    )
