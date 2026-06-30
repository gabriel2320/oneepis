from oneepis_api.core.config import Settings
from oneepis_api.core.productive_auth_contract import (
    LOCAL_AUTH_DEVELOPMENT_LIMITS,
    PRODUCTIVE_AUTH_REQUIREMENTS,
    local_auth_development_setting_names,
    productive_auth_requirement_keys,
)


def test_productive_auth_contract_tracks_minimum_required_capabilities() -> None:
    assert productive_auth_requirement_keys() == (
        "persistent_user_store",
        "persistent_role_store",
        "admin_session_revocation",
        "institutional_recovery",
        "strong_session_lifecycle",
    )

    assert all(requirement.label for requirement in PRODUCTIVE_AUTH_REQUIREMENTS)
    assert all(requirement.criterion for requirement in PRODUCTIVE_AUTH_REQUIREMENTS)


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
