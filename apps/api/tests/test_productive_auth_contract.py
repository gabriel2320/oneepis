from oneepis_api.core.config import Settings
from oneepis_api.core.productive_auth_contract import (
    LOCAL_AUTH_DEVELOPMENT_LIMITS,
    PRODUCTIVE_AUTH_REQUIREMENTS,
    PRODUCTIVE_AUTH_RUNTIME_STATUS,
    local_auth_development_setting_names,
    productive_auth_requirement_keys,
)


def test_productive_auth_contract_tracks_minimum_required_capabilities() -> None:
    assert productive_auth_requirement_keys() == (
        "persistent_user_store",
        "persistent_role_store",
        "institutional_identity_provider",
        "multi_factor_authentication",
        "institution_membership_lifecycle",
        "admin_session_revocation",
        "institutional_recovery",
        "strong_session_lifecycle",
        "identity_role_audit",
    )

    assert all(requirement.label for requirement in PRODUCTIVE_AUTH_REQUIREMENTS)
    assert all(requirement.criterion for requirement in PRODUCTIVE_AUTH_REQUIREMENTS)
    assert {requirement.status for requirement in PRODUCTIVE_AUTH_REQUIREMENTS} == {
        "required_before_production"
    }


def test_local_auth_limits_are_bound_to_existing_settings() -> None:
    assert local_auth_development_setting_names() == (
        "auth_local_users",
        "auth_allow_dev_actor_header",
        "auth_enabled",
        "auth_notification_provider",
    )

    for setting_name in local_auth_development_setting_names():
        assert setting_name in Settings.model_fields


def test_local_auth_contract_does_not_claim_productive_auth() -> None:
    assert {limit.status for limit in LOCAL_AUTH_DEVELOPMENT_LIMITS} == {
        "development_only",
        "not_productive_auth",
    }
    assert all(
        "institutional" in limit.reason or "development" in limit.reason
        for limit in LOCAL_AUTH_DEVELOPMENT_LIMITS
    )


def test_productive_auth_contract_does_not_claim_runtime_identity_provider() -> None:
    assert PRODUCTIVE_AUTH_RUNTIME_STATUS == {
        "institutional_identity_provider_enabled": False,
        "mfa_enforced": False,
        "persistent_user_store_enabled": False,
        "persistent_role_store_enabled": False,
        "reason": (
            "Productive auth is an executable contract only; local auth remains "
            "development-oriented."
        ),
    }
