from oneepis_api.api.deps import ABAC_MINIMUM_REQUIREMENTS, ACCESS_POLICIES
from oneepis_api.services.auth import UserRole


def test_access_policies_declare_future_abac_contract() -> None:
    assert ACCESS_POLICIES
    assert set(ABAC_MINIMUM_REQUIREMENTS) == {
        "institution_or_tenant",
        "care_team_or_service",
        "active_care_relationship_or_access_reason",
        "audited_break_glass",
    }

    for policy in ACCESS_POLICIES.values():
        assert policy.name
        assert policy.roles
        assert UserRole.ADMIN in policy.roles or UserRole.DEV in policy.roles
        assert set(policy.future_abac_requirements) == set(ABAC_MINIMUM_REQUIREMENTS)


def test_access_policy_role_boundaries_match_current_rbac() -> None:
    assert ACCESS_POLICIES["patient_read"].roles == frozenset(
        {
            UserRole.ADMIN,
            UserRole.MEDICO,
            UserRole.ENFERMERIA,
            UserRole.SOLO_LECTURA,
            UserRole.DEV,
        }
    )
    assert ACCESS_POLICIES["patient_write"].roles == frozenset(
        {UserRole.ADMIN, UserRole.MEDICO, UserRole.DEV}
    )
    assert ACCESS_POLICIES["clinical_event_write"].roles == frozenset(
        {UserRole.ADMIN, UserRole.MEDICO, UserRole.ENFERMERIA, UserRole.DEV}
    )
    assert ACCESS_POLICIES["nursing_structured_write"].roles == frozenset(
        {UserRole.ADMIN, UserRole.MEDICO, UserRole.ENFERMERIA, UserRole.DEV}
    )
    assert ACCESS_POLICIES["ai_access"].roles == frozenset(
        {UserRole.ADMIN, UserRole.MEDICO, UserRole.DEV}
    )
    assert ACCESS_POLICIES["audit_read"].roles == frozenset({UserRole.ADMIN, UserRole.DEV})
