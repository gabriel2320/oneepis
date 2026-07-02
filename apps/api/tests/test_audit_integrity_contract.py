from oneepis_api.core.audit_integrity_contract import (
    AUDIT_INTEGRITY_DIGEST_FIELDS,
    AUDIT_INTEGRITY_REQUIREMENTS,
    AUDIT_INTEGRITY_RUNTIME_STATUS,
    AUDIT_MEDICO_LEGAL_CONTROLS,
    audit_integrity_digest_field_names,
    audit_integrity_requirement_keys,
    audit_medico_legal_control_keys,
)
from oneepis_api.core.audit_retention_contract import audit_retention_requirement_keys
from oneepis_api.models.audit import AuditEvent


def test_audit_integrity_contract_tracks_minimum_requirements() -> None:
    assert audit_integrity_requirement_keys() == (
        "canonical_event_serialization",
        "previous_digest_link",
        "digest_algorithm_version",
        "external_anchor_or_worm",
        "verification_procedure",
    )

    assert all(requirement.label for requirement in AUDIT_INTEGRITY_REQUIREMENTS)
    assert all(requirement.criterion for requirement in AUDIT_INTEGRITY_REQUIREMENTS)
    assert {requirement.status for requirement in AUDIT_INTEGRITY_REQUIREMENTS} == {
        "required_before_production"
    }
    assert "immutability_control" in audit_retention_requirement_keys()


def test_audit_integrity_digest_fields_match_audit_event_columns() -> None:
    digest_fields = audit_integrity_digest_field_names()
    assert digest_fields == (
        "id",
        "action",
        "entity_type",
        "entity_id",
        "actor_id",
        "correlation_id",
        "request_method",
        "request_path",
        "created_at",
        "extra_data",
    )

    audit_event_attributes = set(AuditEvent.__mapper__.attrs.keys())
    assert set(digest_fields).issubset(audit_event_attributes)
    assert all(field.included_in_digest for field in AUDIT_INTEGRITY_DIGEST_FIELDS)
    assert all(field.reason for field in AUDIT_INTEGRITY_DIGEST_FIELDS)


def test_audit_medico_legal_controls_link_integrity_and_retention() -> None:
    assert audit_medico_legal_control_keys() == (
        "hash_chain",
        "algorithm_version",
        "verification_job",
        "retention_policy_link",
        "legal_hold",
        "controlled_export",
    )
    linked_requirements = {control.linked_requirement for control in AUDIT_MEDICO_LEGAL_CONTROLS}
    assert {
        "previous_digest_link",
        "digest_algorithm_version",
        "verification_procedure",
    }.issubset(linked_requirements)
    assert {"versioned_retention_policy", "legal_hold", "exportable_audit_log"}.issubset(
        linked_requirements
    )
    assert {control.runtime_enabled for control in AUDIT_MEDICO_LEGAL_CONTROLS} == {False}


def test_audit_integrity_contract_does_not_claim_runtime_hash_chain() -> None:
    assert AUDIT_INTEGRITY_RUNTIME_STATUS == {
        "runtime_hash_chain_enabled": False,
        "external_anchor_enabled": False,
        "worm_storage_enabled": False,
        "verification_job_enabled": False,
        "legal_hold_enabled": False,
        "controlled_export_enabled": False,
        "reason": (
            "Audit integrity is an executable production contract only; runtime "
            "hash-chain, WORM storage, legal hold and controlled export are future work."
        ),
    }
