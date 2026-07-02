import pytest
from pydantic import ValidationError

from oneepis_api.core.config import Settings
from oneepis_api.core.productive_auth_contract import (
    DEVELOPMENT_ONLY_LOCAL_ROLE_VALUES,
    LOCAL_AUTH_DEVELOPMENT_LIMITS,
    LOCAL_ROLE_PRODUCTION_BOUNDARIES,
    PRODUCTIVE_AUTH_PROVIDER_CONTROLS,
    PRODUCTIVE_AUTH_REQUIREMENTS,
    PRODUCTIVE_AUTH_RUNTIME_STATUS,
    local_auth_development_setting_names,
    local_role_boundary_keys,
    productive_auth_provider_control_keys,
    productive_auth_requirement_keys,
)
from oneepis_api.services.auth import hash_password


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


def test_productive_auth_provider_controls_are_docs_only_contract() -> None:
    assert productive_auth_provider_control_keys() == (
        "oidc_saml_adapter",
        "mfa_assurance_claims",
        "persistent_subject_link",
        "role_group_sync",
        "central_session_revocation",
        "identity_event_audit",
    )
    assert all(control.label for control in PRODUCTIVE_AUTH_PROVIDER_CONTROLS)
    assert all(control.criterion for control in PRODUCTIVE_AUTH_PROVIDER_CONTROLS)
    assert {control.runtime_enabled for control in PRODUCTIVE_AUTH_PROVIDER_CONTROLS} == {False}
    assert {control.protocol_layer for control in PRODUCTIVE_AUTH_PROVIDER_CONTROLS} == {
        "identity_provider",
        "assurance",
        "session",
        "audit",
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


def test_local_role_boundaries_formalize_admin_dev_policy() -> None:
    assert DEVELOPMENT_ONLY_LOCAL_ROLE_VALUES == ("dev",)
    assert local_role_boundary_keys() == ("dev_role", "technical_admin")

    boundaries = {boundary.key: boundary for boundary in LOCAL_ROLE_PRODUCTION_BOUNDARIES}
    assert boundaries["dev_role"].role == "dev"
    assert boundaries["dev_role"].status == "development_only"
    assert "outside development" in boundaries["dev_role"].rule
    assert boundaries["technical_admin"].role == "admin"
    assert boundaries["technical_admin"].status == "not_productive_phi_access"
    assert "PHI access by itself" in boundaries["technical_admin"].rule


def test_non_development_rejects_local_dev_role() -> None:
    password_hash = hash_password("secret")

    with pytest.raises(ValidationError, match="dev"):
        Settings(
            environment="production",
            auth_secret="prod-secret",
            auth_local_users=f"dev@example.local|{password_hash}|Dev|dev",
        )


def test_productive_auth_contract_does_not_claim_runtime_identity_provider() -> None:
    assert PRODUCTIVE_AUTH_RUNTIME_STATUS == {
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
