from __future__ import annotations

import uuid
from typing import Literal

from sqlalchemy.orm import Session

from oneepis_api.core.access_context_contract import access_context_requirement_keys
from oneepis_api.core.access_context_runtime import (
    AccessContext,
    attach_patient_scope_dry_run_metadata,
    evaluate_access_context,
)
from oneepis_api.services.audit import record_audit_event
from oneepis_api.services.patient_access_relationship import (
    resolve_patient_access_relationship_dry_run,
)

PASSIVE_ACCESS_CONTEXT_DECISION_ACTION = "access_context.passive_decision"
DENIED_ACCESS_CONTEXT_DECISION_ACTION = "access_context.denied"


def record_passive_patient_access_context_decision(
    session: Session,
    *,
    patient_id: uuid.UUID,
    actor_id: str,
    source_action: str,
) -> None:
    patient_scope = resolve_patient_access_relationship_dry_run(
        session,
        actor_id=actor_id,
        patient_id=patient_id,
    )
    context = AccessContext(
        actor_id=actor_id,
        role_names=(),
        source="rbac_only",
        missing_abac_requirements=access_context_requirement_keys(),
    )
    context = attach_patient_scope_dry_run_metadata(context, patient_scope.as_metadata())
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
            "patient_scope": context.patient_scope_dry_run_metadata,
            "metadata_retention": decision.metadata_retention,
        },
    )


def denied_patient_access_context_metadata(
    *,
    decision_policy: str,
    denial_reasons: tuple[str, ...],
    runtime_enforced: bool,
) -> dict[str, object]:
    return {
        "policy": decision_policy,
        "runtime_enforced": runtime_enforced,
        "reason_keys": _denial_reason_keys(denial_reasons),
        "metadata_retention": "requirement_keys_only",
    }


def record_denied_patient_access_context_decision(
    session: Session,
    *,
    patient_id: uuid.UUID,
    actor_id: str,
    denial_reasons: tuple[str, ...],
    runtime_enforced: bool,
) -> None:
    record_audit_event(
        session,
        action=DENIED_ACCESS_CONTEXT_DECISION_ACTION,
        entity_type="patient",
        entity_id=patient_id,
        actor_id=actor_id,
        metadata=denied_patient_access_context_metadata(
            decision_policy="contextual_abac",
            denial_reasons=denial_reasons,
            runtime_enforced=runtime_enforced,
        ),
    )


def _denial_reason_keys(denial_reasons: tuple[str, ...]) -> tuple[str, ...]:
    prefix: Literal["missing_abac_requirement:"] = "missing_abac_requirement:"
    return tuple(
        reason.removeprefix(prefix)
        for reason in denial_reasons
        if reason.startswith(prefix)
    )
