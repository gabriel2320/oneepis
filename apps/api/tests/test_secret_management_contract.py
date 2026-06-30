from oneepis_api.core.config import DEFAULT_AUTH_SECRET, Settings
from oneepis_api.core.secret_management_contract import (
    SECRET_BACKED_SETTINGS,
    SECRET_MANAGEMENT_REQUIREMENTS,
    secret_backed_setting_names,
    secret_management_requirement_keys,
)


def test_secret_management_contract_tracks_minimum_requirements() -> None:
    assert secret_management_requirement_keys() == (
        "external_secret_store",
        "secret_owners",
        "rotation_policy",
        "incident_procedure",
        "environment_isolation",
    )

    assert all(requirement.label for requirement in SECRET_MANAGEMENT_REQUIREMENTS)
    assert all(requirement.criterion for requirement in SECRET_MANAGEMENT_REQUIREMENTS)
    assert {requirement.status for requirement in SECRET_MANAGEMENT_REQUIREMENTS} == {
        "required_before_production"
    }


def test_secret_backed_settings_are_bound_to_existing_config() -> None:
    assert secret_backed_setting_names() == ("auth_secret", "database_url")

    for setting_name in secret_backed_setting_names():
        assert setting_name in Settings.model_fields


def test_development_defaults_are_explicitly_scoped() -> None:
    assert Settings().auth_secret == DEFAULT_AUTH_SECRET
    assert all(setting.development_default_allowed for setting in SECRET_BACKED_SETTINGS)
    assert all("production" not in setting.purpose.lower() for setting in SECRET_BACKED_SETTINGS)
