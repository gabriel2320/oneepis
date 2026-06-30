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


PRODUCTIVE_AUTH_RUNTIME_STATUS = {
    "institutional_identity_provider_enabled": False,
    "mfa_enforced": False,
    "persistent_user_store_enabled": False,
    "persistent_role_store_enabled": False,
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


def productive_auth_requirement_keys() -> tuple[str, ...]:
    return tuple(requirement.key for requirement in PRODUCTIVE_AUTH_REQUIREMENTS)


def local_auth_development_setting_names() -> tuple[str, ...]:
    return tuple(limit.setting_name for limit in LOCAL_AUTH_DEVELOPMENT_LIMITS)
