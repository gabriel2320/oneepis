from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class SecretManagementRequirement:
    key: str
    label: str
    criterion: str
    status: Literal["required_before_production"]


@dataclass(frozen=True)
class SecretBackedSetting:
    setting_name: str
    purpose: str
    development_default_allowed: bool


SECRET_MANAGEMENT_REQUIREMENTS: tuple[SecretManagementRequirement, ...] = (
    SecretManagementRequirement(
        key="external_secret_store",
        label="External secret store",
        criterion="Production secrets must be managed outside repository and static local files.",
        status="required_before_production",
    ),
    SecretManagementRequirement(
        key="secret_owners",
        label="Secret owners",
        criterion="Each production secret must have accountable owner and authorized maintainers.",
        status="required_before_production",
    ),
    SecretManagementRequirement(
        key="rotation_policy",
        label="Rotation policy",
        criterion=(
            "Secrets must have documented rotation cadence, emergency rotation "
            "and revocation."
        ),
        status="required_before_production",
    ),
    SecretManagementRequirement(
        key="incident_procedure",
        label="Incident procedure",
        criterion=(
            "Leaks must trigger documented containment, rotation, audit and "
            "notification steps."
        ),
        status="required_before_production",
    ),
    SecretManagementRequirement(
        key="environment_isolation",
        label="Environment isolation",
        criterion="Development, staging and production secrets must be isolated and non-reusable.",
        status="required_before_production",
    ),
)


SECRET_BACKED_SETTINGS: tuple[SecretBackedSetting, ...] = (
    SecretBackedSetting(
        setting_name="auth_secret",
        purpose="sign authentication tokens and recovery/session material",
        development_default_allowed=True,
    ),
    SecretBackedSetting(
        setting_name="database_url",
        purpose="connect to the clinical database",
        development_default_allowed=True,
    ),
)


def secret_management_requirement_keys() -> tuple[str, ...]:
    return tuple(requirement.key for requirement in SECRET_MANAGEMENT_REQUIREMENTS)


def secret_backed_setting_names() -> tuple[str, ...]:
    return tuple(setting.setting_name for setting in SECRET_BACKED_SETTINGS)
