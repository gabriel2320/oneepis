from oneepis_api.core.observability_contract import (
    OBSERVABILITY_ALLOWED_LOG_FIELDS,
    OBSERVABILITY_ALLOWED_METRIC_LABELS,
    OBSERVABILITY_FORBIDDEN_FIELDS,
    OBSERVABILITY_REQUIREMENTS,
    OBSERVABILITY_RUNTIME_STATUS,
    log_field_policy_violations,
    metric_label_policy_violations,
    observability_requirement_keys,
)
from oneepis_api.services.phi_logging import PHI_SENSITIVE_KEYS


def test_observability_contract_tracks_required_phi_safe_gates() -> None:
    assert observability_requirement_keys() == (
        "correlation_id_required",
        "json_logs_no_phi",
        "metric_label_allowlist",
        "trace_payload_minimization",
        "exporter_governance",
    )
    assert all(requirement.label for requirement in OBSERVABILITY_REQUIREMENTS)
    assert all(requirement.criterion for requirement in OBSERVABILITY_REQUIREMENTS)
    assert {requirement.status for requirement in OBSERVABILITY_REQUIREMENTS} == {
        "required_before_phi"
    }


def test_observability_log_field_allowlist_requires_traceability_without_phi() -> None:
    assert "correlation_id" in OBSERVABILITY_ALLOWED_LOG_FIELDS
    assert "route_template" in OBSERVABILITY_ALLOWED_LOG_FIELDS
    assert "method" in OBSERVABILITY_ALLOWED_LOG_FIELDS
    assert "patient_id" not in OBSERVABILITY_ALLOWED_LOG_FIELDS

    assert log_field_policy_violations(("correlation_id", "route_template", "status_code")) == ()
    assert log_field_policy_violations(("correlation_id", "patient_id", "notes", "unknown")) == (
        "notes",
        "patient_id",
        "unknown",
    )


def test_observability_metric_labels_are_low_cardinality_and_phi_safe() -> None:
    assert "route_template" in OBSERVABILITY_ALLOWED_METRIC_LABELS
    assert "status_class" in OBSERVABILITY_ALLOWED_METRIC_LABELS
    assert "patient_id" not in OBSERVABILITY_ALLOWED_METRIC_LABELS

    safe_labels = {"service": "api", "route_template": "/api/v1/patients/{patient_id}"}
    assert metric_label_policy_violations(safe_labels) == ()

    unsafe_labels = {"patient_id": "uuid", "free_text": "dolor", "custom": "value"}
    assert metric_label_policy_violations(unsafe_labels) == (
        "custom",
        "free_text",
        "patient_id",
    )


def test_observability_forbidden_fields_cover_phi_logging_sensitive_keys() -> None:
    required_overlap = {
        "access_token",
        "birth_date",
        "clinical_identifier",
        "email",
        "first_name",
        "last_name",
        "notes",
        "objective",
        "plan",
        "refresh_token",
        "subjective",
    }

    assert required_overlap.issubset(PHI_SENSITIVE_KEYS)
    assert required_overlap.issubset(set(OBSERVABILITY_FORBIDDEN_FIELDS))


def test_observability_runtime_status_keeps_product_exporters_disabled() -> None:
    assert OBSERVABILITY_RUNTIME_STATUS == {
        "external_exporters_enabled": False,
        "phi_dashboard_enabled": False,
        "request_body_tracing_enabled": False,
        "patient_identifier_metric_labels_enabled": False,
        "reason": (
            "Observability is a PHI-safe contract only; product exporters, dashboards "
            "and payload tracing require separate security/clinical approval."
        ),
    }
