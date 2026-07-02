from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class ProductiveAuthRequirement:
    key: str
    label: str
    criterion: str
    status: Literal["required_before_production"] = "required_before_production"


@dataclass(frozen=True)
class LocalAuthDevelopmentLimit:
    key: str
    setting_name: str
    reason: str
    status: Literal["development_only", "not_productive_auth"]


@dataclass(frozen=True)
class LocalRoleProductionBoundary:
    key: str
    role: str
    rule: str
    status: Literal["development_only", "not_productive_phi_access"]


@dataclass(frozen=True)
class ProductiveAuthProviderControl:
    key: str
    label: str
    protocol_layer: Literal["identity_provider", "assurance", "session", "audit"]
    criterion: str
    runtime_enabled: bool


PRODUCTIVE_AUTH_REQUIREMENTS: tuple[ProductiveAuthRequirement, ...] = (
    ProductiveAuthRequirement(
        key="persistent_user_store",
        label="Persistent user store",
        criterion="Users must be managed in a durable institutional store, not static config.",
    ),
    ProductiveAuthRequirement(
        key="persistent_role_store",
        label="Persistent role store",
        criterion=(
            "Roles must have audited lifecycle, assignment and revocation "
            "outside static config."
        ),
    ),
    ProductiveAuthRequirement(
        key="institutional_identity_provider",
        label="Institutional identity provider",
        criterion=(
            "Production identity must be backed by an approved institutional "
            "provider such as OIDC, SAML or equivalent managed identity."
        ),
    ),
    ProductiveAuthRequirement(
        key="multi_factor_authentication",
        label="Multi-factor authentication",
        criterion=(
            "Privileged and clinical accounts must require MFA or an equivalent "
            "institutional assurance control."
        ),
    ),
    ProductiveAuthRequirement(
        key="institution_membership_lifecycle",
        label="Institution membership lifecycle",
        criterion=(
            "User access must track institution, care team or service membership "
            "with join, change and termination lifecycle."
        ),
    ),
    ProductiveAuthRequirement(
        key="admin_session_revocation",
        label="Administrative session revocation",
        criterion="Institutional admins must be able to revoke active sessions centrally.",
    ),
    ProductiveAuthRequirement(
        key="institutional_recovery",
        label="Institutional account recovery",
        criterion=(
            "Recovery must follow an institutional identity lifecycle and "
            "notification channel."
        ),
    ),
    ProductiveAuthRequirement(
        key="strong_session_lifecycle",
        label="Strong session lifecycle",
        criterion=(
            "Sessions need enforced expiry, rotation, persistence and "
            "server-side invalidation."
        ),
    ),
    ProductiveAuthRequirement(
        key="identity_role_audit",
        label="Identity and role audit",
        criterion=(
            "Identity changes, role assignments, role revocations and recovery "
            "actions must emit minimized audit events."
        ),
    ),
)


PRODUCTIVE_AUTH_PROVIDER_CONTROLS: tuple[ProductiveAuthProviderControl, ...] = (
    ProductiveAuthProviderControl(
        key="oidc_saml_adapter",
        label="OIDC/SAML adapter",
        protocol_layer="identity_provider",
        criterion="Production auth must validate issuer, audience, expiry and signature.",
        runtime_enabled=False,
    ),
    ProductiveAuthProviderControl(
        key="mfa_assurance_claims",
        label="MFA assurance claims",
        protocol_layer="assurance",
        criterion="Clinical access must map institutional MFA or equivalent assurance claims.",
        runtime_enabled=False,
    ),
    ProductiveAuthProviderControl(
        key="persistent_subject_link",
        label="Persistent subject link",
        protocol_layer="identity_provider",
        criterion="External subject identifiers must link to a durable local user record.",
        runtime_enabled=False,
    ),
    ProductiveAuthProviderControl(
        key="role_group_sync",
        label="Role and group sync",
        protocol_layer="identity_provider",
        criterion="Institutional groups must map to auditable role and membership records.",
        runtime_enabled=False,
    ),
    ProductiveAuthProviderControl(
        key="central_session_revocation",
        label="Central session revocation",
        protocol_layer="session",
        criterion="Sessions must be revocable by institutional lifecycle or admin action.",
        runtime_enabled=False,
    ),
    ProductiveAuthProviderControl(
        key="identity_event_audit",
        label="Identity event audit",
        protocol_layer="audit",
        criterion="Login, logout, recovery, role sync and revocation must emit minimized audit.",
        runtime_enabled=False,
    ),
)


PRODUCTIVE_AUTH_RUNTIME_STATUS = {
    "oidc_saml_adapter_enabled": False,
    "institutional_identity_provider_enabled": False,
    "mfa_enforced": False,
    "persistent_user_store_enabled": False,
    "persistent_role_store_enabled": False,
    "dev_role_available_in_production": False,
    "technical_admin_phi_access_grant_enabled": False,
    "reason": (
        "Productive auth is an executable contract only; local auth remains "
        "development-oriented."
    ),
}


LOCAL_AUTH_DEVELOPMENT_LIMITS: tuple[LocalAuthDevelopmentLimit, ...] = (
    LocalAuthDevelopmentLimit(
        key="static_local_users",
        setting_name="auth_local_users",
        reason=(
            "Local users come from configuration and cannot provide audited "
            "institutional lifecycle."
        ),
        status="not_productive_auth",
    ),
    LocalAuthDevelopmentLimit(
        key="dev_actor_header",
        setting_name="auth_allow_dev_actor_header",
        reason="Actor override headers bypass institutional identity and are development-only.",
        status="development_only",
    ),
    LocalAuthDevelopmentLimit(
        key="auth_disabled",
        setting_name="auth_enabled",
        reason="Disabling auth is permitted only as a development/testing control.",
        status="development_only",
    ),
    LocalAuthDevelopmentLimit(
        key="development_notifications",
        setting_name="auth_notification_provider",
        reason="Development log notifications are not an institutional recovery channel.",
        status="development_only",
    ),
)


DEVELOPMENT_ONLY_LOCAL_ROLE_VALUES = ("dev",)


LOCAL_ROLE_PRODUCTION_BOUNDARIES: tuple[LocalRoleProductionBoundary, ...] = (
    LocalRoleProductionBoundary(
        key="dev_role",
        role="dev",
        rule=(
            "The dev role is a local development/test breakout and must not be "
            "accepted outside development."
        ),
        status="development_only",
    ),
    LocalRoleProductionBoundary(
        key="technical_admin",
        role="admin",
        rule=(
            "The local admin role is a technical control until institutional "
            "identity, ABAC and audited membership exist; it does not grant "
            "productive PHI access by itself."
        ),
        status="not_productive_phi_access",
    ),
)


def productive_auth_requirement_keys() -> tuple[str, ...]:
    return tuple(requirement.key for requirement in PRODUCTIVE_AUTH_REQUIREMENTS)


def productive_auth_provider_control_keys() -> tuple[str, ...]:
    return tuple(control.key for control in PRODUCTIVE_AUTH_PROVIDER_CONTROLS)


def local_auth_development_setting_names() -> tuple[str, ...]:
    return tuple(limit.setting_name for limit in LOCAL_AUTH_DEVELOPMENT_LIMITS)


def local_role_boundary_keys() -> tuple[str, ...]:
    return tuple(boundary.key for boundary in LOCAL_ROLE_PRODUCTION_BOUNDARIES)
