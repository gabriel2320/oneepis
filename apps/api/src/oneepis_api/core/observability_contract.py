from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class ObservabilityRequirement:
    key: str
    label: str
    criterion: str
    status: Literal["required_before_phi"]


OBSERVABILITY_REQUIREMENTS: tuple[ObservabilityRequirement, ...] = (
    ObservabilityRequirement(
        key="correlation_id_required",
        label="Correlation ID",
        criterion="Every clinical request log, trace or metric must carry a correlation_id.",
        status="required_before_phi",
    ),
    ObservabilityRequirement(
        key="json_logs_no_phi",
        label="Structured logs without PHI",
        criterion=(
            "Runtime logs must be structured and limited to an explicit "
            "non-PHI field allowlist."
        ),
        status="required_before_phi",
    ),
    ObservabilityRequirement(
        key="metric_label_allowlist",
        label="Metric label allowlist",
        criterion=(
            "Metric labels must be low-cardinality operational labels and "
            "exclude patient identifiers."
        ),
        status="required_before_phi",
    ),
    ObservabilityRequirement(
        key="trace_payload_minimization",
        label="Trace payload minimization",
        criterion=(
            "Traces must not include request bodies, clinical free text or "
            "patient identifiers."
        ),
        status="required_before_phi",
    ),
    ObservabilityRequirement(
        key="exporter_governance",
        label="Exporter governance",
        criterion=(
            "External exporters and dashboards remain disabled until PHI-safe "
            "operations are approved."
        ),
        status="required_before_phi",
    ),
)


OBSERVABILITY_ALLOWED_LOG_FIELDS: tuple[str, ...] = (
    "action",
    "actor_id",
    "correlation_id",
    "duration_ms",
    "error_type",
    "event",
    "level",
    "logger",
    "method",
    "operation",
    "outcome",
    "policy",
    "request_id",
    "route_template",
    "service",
    "status_code",
    "surface",
    "timestamp",
)


OBSERVABILITY_ALLOWED_METRIC_LABELS: tuple[str, ...] = (
    "check",
    "environment",
    "error_type",
    "job",
    "method",
    "operation",
    "outcome",
    "policy",
    "route_template",
    "service",
    "signal",
    "status_class",
    "surface",
)


OBSERVABILITY_FORBIDDEN_FIELDS: tuple[str, ...] = (
    "access_token",
    "address",
    "assessment",
    "birth_date",
    "clinical_identifier",
    "diagnosis",
    "document_number",
    "email",
    "first_name",
    "free_text",
    "full_name",
    "last_name",
    "medication_name",
    "notes",
    "objective",
    "patient_id",
    "patient_name",
    "phone",
    "plan",
    "prescription",
    "refresh_token",
    "subjective",
)


OBSERVABILITY_RUNTIME_STATUS = {
    "external_exporters_enabled": False,
    "phi_dashboard_enabled": False,
    "request_body_tracing_enabled": False,
    "patient_identifier_metric_labels_enabled": False,
    "reason": (
        "Observability is a PHI-safe contract only; product exporters, dashboards "
        "and payload tracing require separate security/clinical approval."
    ),
}


def observability_requirement_keys() -> tuple[str, ...]:
    return tuple(requirement.key for requirement in OBSERVABILITY_REQUIREMENTS)


def log_field_policy_violations(fields: list[str] | tuple[str, ...] | set[str]) -> tuple[str, ...]:
    return _policy_violations(fields, allowed=OBSERVABILITY_ALLOWED_LOG_FIELDS)


def metric_label_policy_violations(labels: Mapping[str, object] | set[str]) -> tuple[str, ...]:
    keys = labels.keys() if isinstance(labels, Mapping) else labels
    return _policy_violations(keys, allowed=OBSERVABILITY_ALLOWED_METRIC_LABELS)


def _policy_violations(fields: object, *, allowed: tuple[str, ...]) -> tuple[str, ...]:
    allowed_set = set(allowed)
    forbidden_set = set(OBSERVABILITY_FORBIDDEN_FIELDS)
    values = {str(field) for field in fields}
    return tuple(
        sorted(field for field in values if field not in allowed_set or field in forbidden_set)
    )
