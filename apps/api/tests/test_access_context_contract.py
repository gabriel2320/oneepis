from oneepis_api.api.deps import ABAC_MINIMUM_REQUIREMENTS
from oneepis_api.core.access_context_contract import (
    ACCESS_CONTEXT_REQUIREMENTS,
    ACCESS_CONTEXT_RUNTIME_STATUS,
    CONTEXTUAL_ACCESS_HEADER_CONTRACTS,
    access_context_requirement_keys,
    contextual_access_header_names,
)
from oneepis_api.main import UNSUPPORTED_CONTEXTUAL_ACCESS_HEADERS


def test_access_context_contract_matches_abac_policy_requirements() -> None:
    assert access_context_requirement_keys() == ABAC_MINIMUM_REQUIREMENTS

    assert all(requirement.label for requirement in ACCESS_CONTEXT_REQUIREMENTS)
    assert all(requirement.criterion for requirement in ACCESS_CONTEXT_REQUIREMENTS)
    assert {requirement.status for requirement in ACCESS_CONTEXT_REQUIREMENTS} == {
        "required_before_phi"
    }


def test_contextual_header_contract_matches_current_runtime_rejections() -> None:
    assert contextual_access_header_names() == UNSUPPORTED_CONTEXTUAL_ACCESS_HEADERS

    mapped_requirement_keys = {
        contract.requirement_key for contract in CONTEXTUAL_ACCESS_HEADER_CONTRACTS
    }
    assert mapped_requirement_keys == set(ABAC_MINIMUM_REQUIREMENTS)

    assert {contract.status for contract in CONTEXTUAL_ACCESS_HEADER_CONTRACTS} == {
        "unsupported_until_runtime_abac"
    }
    assert {contract.audit_metadata for contract in CONTEXTUAL_ACCESS_HEADER_CONTRACTS} == {
        "header_name_only"
    }
    assert {contract.value_retention for contract in CONTEXTUAL_ACCESS_HEADER_CONTRACTS} == {
        "never_store_header_value"
    }


def test_access_context_contract_does_not_claim_runtime_abac() -> None:
    assert ACCESS_CONTEXT_RUNTIME_STATUS == {
        "runtime_abac_enforced": False,
        "contextual_headers_accepted": False,
        "break_glass_enabled": False,
        "reason": (
            "Contextual ABAC is an executable contract only; runtime enforcement is future work."
        ),
    }
