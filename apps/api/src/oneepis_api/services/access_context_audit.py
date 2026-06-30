from __future__ import annotations

import uuid
from collections.abc import Iterable
from typing import Literal

from sqlalchemy.orm import Session

from oneepis_api.core.access_context_contract import access_context_requirement_keys
from oneepis_api.core.access_context_runtime import (
    AccessContext,
    attach_patient_scope_dry_run_metadata,
    evaluate_access_context,
)
from oneepis_api.models.audit import AuditEvent
from oneepis_api.services.audit import record_audit_event
from oneepis_api.services.patient_access_relationship import (
    resolve_patient_access_relationship_dry_run,
)

PASSIVE_ACCESS_CONTEXT_DECISION_ACTION = "access_context.passive_decision"
DENIED_ACCESS_CONTEXT_DECISION_ACTION = "access_context.denied"
ACCESS_CONTEXT_OBSERVABILITY_METADATA_RETENTION = "aggregate_counts_only"


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


def build_access_context_observability_report(
    events: Iterable[AuditEvent],
) -> dict[str, object]:
    passive_decision_count = 0
    passive_would_deny_if_enforced_count = 0
    denied_count = 0
    runtime_enforced_denied_count = 0
    source_actions: set[str] = set()
    reason_keys: set[str] = set()

    for event in events:
        metadata = event.extra_data or {}
        if event.action == PASSIVE_ACCESS_CONTEXT_DECISION_ACTION:
            passive_decision_count += 1
            source_action = _string_metadata_value(metadata.get("source_action"))
            if source_action:
                source_actions.add(source_action)
            if metadata.get("would_deny_if_enforced") is True:
                passive_would_deny_if_enforced_count += 1
            reason_keys.update(_metadata_string_sequence(metadata.get("denial_reason_keys")))
        elif event.action == DENIED_ACCESS_CONTEXT_DECISION_ACTION:
            denied_count += 1
            if metadata.get("runtime_enforced") is True:
                runtime_enforced_denied_count += 1
            reason_keys.update(_metadata_string_sequence(metadata.get("reason_keys")))

    return {
        "passive_decision_count": passive_decision_count,
        "passive_would_deny_if_enforced_count": passive_would_deny_if_enforced_count,
        "denied_count": denied_count,
        "runtime_enforced_denied_count": runtime_enforced_denied_count,
        "source_actions": tuple(sorted(source_actions)),
        "reason_keys": tuple(sorted(reason_keys)),
        "metadata_retention": ACCESS_CONTEXT_OBSERVABILITY_METADATA_RETENTION,
    }


def _denial_reason_keys(denial_reasons: tuple[str, ...]) -> tuple[str, ...]:
    prefix: Literal["missing_abac_requirement:"] = "missing_abac_requirement:"
    return tuple(
        reason.removeprefix(prefix)
        for reason in denial_reasons
        if reason.startswith(prefix)
    )


def _string_metadata_value(value: object) -> str | None:
    if isinstance(value, str) and value:
        return value
    return None


def _metadata_string_sequence(value: object) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(item for item in value if isinstance(item, str) and item)
