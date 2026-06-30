from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class AuditIntegrityRequirement:
    key: str
    label: str
    criterion: str
    status: Literal["required_before_production"]


@dataclass(frozen=True)
class AuditIntegrityField:
    field_name: str
    included_in_digest: bool
    reason: str


AUDIT_INTEGRITY_REQUIREMENTS: tuple[AuditIntegrityRequirement, ...] = (
    AuditIntegrityRequirement(
        key="canonical_event_serialization",
        label="Canonical event serialization",
        criterion=(
            "Audit events must be serialized in a deterministic format before "
            "digest calculation."
        ),
        status="required_before_production",
    ),
    AuditIntegrityRequirement(
        key="previous_digest_link",
        label="Previous digest link",
        criterion=(
            "Each production audit event must include or reference the previous "
            "event digest for tamper-evident chaining."
        ),
        status="required_before_production",
    ),
    AuditIntegrityRequirement(
        key="digest_algorithm_version",
        label="Digest algorithm version",
        criterion=(
            "Digest algorithm and canonicalization version must be explicit and "
            "migratable."
        ),
        status="required_before_production",
    ),
    AuditIntegrityRequirement(
        key="external_anchor_or_worm",
        label="External anchor or WORM store",
        criterion=(
            "The chain must be anchored outside the mutable application database "
            "or stored in equivalent WORM infrastructure."
        ),
        status="required_before_production",
    ),
    AuditIntegrityRequirement(
        key="verification_procedure",
        label="Verification procedure",
        criterion=(
            "Operations must have a documented and tested procedure to verify the "
            "audit chain and report the first broken link."
        ),
        status="required_before_production",
    ),
)


AUDIT_INTEGRITY_DIGEST_FIELDS: tuple[AuditIntegrityField, ...] = (
    AuditIntegrityField(
        field_name="id",
        included_in_digest=True,
        reason="Binds digest to the immutable event identity.",
    ),
    AuditIntegrityField(
        field_name="action",
        included_in_digest=True,
        reason="Binds digest to the audited action.",
    ),
    AuditIntegrityField(
        field_name="entity_type",
        included_in_digest=True,
        reason="Binds digest to the audited entity domain.",
    ),
    AuditIntegrityField(
        field_name="entity_id",
        included_in_digest=True,
        reason="Binds digest to the audited entity identifier when present.",
    ),
    AuditIntegrityField(
        field_name="actor_id",
        included_in_digest=True,
        reason="Binds digest to the accountable actor.",
    ),
    AuditIntegrityField(
        field_name="correlation_id",
        included_in_digest=True,
        reason="Binds digest to request traceability.",
    ),
    AuditIntegrityField(
        field_name="request_method",
        included_in_digest=True,
        reason="Binds digest to request context.",
    ),
    AuditIntegrityField(
        field_name="request_path",
        included_in_digest=True,
        reason="Binds digest to request context.",
    ),
    AuditIntegrityField(
        field_name="created_at",
        included_in_digest=True,
        reason="Binds digest to event ordering evidence.",
    ),
    AuditIntegrityField(
        field_name="extra_data",
        included_in_digest=True,
        reason="Binds digest to minimized event metadata.",
    ),
)


AUDIT_INTEGRITY_RUNTIME_STATUS = {
    "runtime_hash_chain_enabled": False,
    "external_anchor_enabled": False,
    "worm_storage_enabled": False,
    "verification_job_enabled": False,
    "reason": (
        "Audit integrity is an executable production contract only; runtime "
        "hash-chain or WORM storage is future work."
    ),
}


def audit_integrity_requirement_keys() -> tuple[str, ...]:
    return tuple(requirement.key for requirement in AUDIT_INTEGRITY_REQUIREMENTS)


def audit_integrity_digest_field_names() -> tuple[str, ...]:
    return tuple(field.field_name for field in AUDIT_INTEGRITY_DIGEST_FIELDS)
