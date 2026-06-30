from oneepis_api.core.audit_integrity_contract import (
    AUDIT_INTEGRITY_DIGEST_FIELDS,
    AUDIT_INTEGRITY_REQUIREMENTS,
    AUDIT_INTEGRITY_RUNTIME_STATUS,
    audit_integrity_digest_field_names,
    audit_integrity_requirement_keys,
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


def test_audit_integrity_contract_does_not_claim_runtime_hash_chain() -> None:
    assert AUDIT_INTEGRITY_RUNTIME_STATUS == {
        "runtime_hash_chain_enabled": False,
        "external_anchor_enabled": False,
        "worm_storage_enabled": False,
        "verification_job_enabled": False,
        "reason": (
            "Audit integrity is an executable production contract only; runtime "
            "hash-chain or WORM storage is future work."
        ),
    }
