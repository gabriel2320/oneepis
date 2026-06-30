from oneepis_api.core.external_ai_contract import (
    EXTERNAL_AI_PAYLOAD_RULES,
    EXTERNAL_AI_REQUIREMENTS,
    EXTERNAL_AI_RUNTIME_STATUS,
    external_ai_payload_rule_keys,
    external_ai_requirement_keys,
)


def test_external_ai_contract_tracks_minimum_requirements() -> None:
    assert external_ai_requirement_keys() == (
        "phi_privacy_gateway",
        "deidentification_or_minimization",
        "approved_provider_allowlist",
        "explicit_human_opt_in",
        "external_ai_audit",
        "legal_security_review",
    )

    assert all(requirement.label for requirement in EXTERNAL_AI_REQUIREMENTS)
    assert all(requirement.criterion for requirement in EXTERNAL_AI_REQUIREMENTS)
    assert {requirement.status for requirement in EXTERNAL_AI_REQUIREMENTS} == {
        "required_before_external_ai"
    }


def test_external_ai_payload_rules_block_phi_by_default() -> None:
    assert external_ai_payload_rule_keys() == (
        "raw_clinical_note",
        "patient_identifier",
        "document_attachment",
        "minimized_structured_context",
    )

    payload_states = {rule.key: rule.payload_state for rule in EXTERNAL_AI_PAYLOAD_RULES}
    assert payload_states["raw_clinical_note"] == "blocked"
    assert payload_states["patient_identifier"] == "blocked"
    assert payload_states["document_attachment"] == "blocked"
    assert payload_states["minimized_structured_context"] == "requires_gateway"
    assert all(rule.reason for rule in EXTERNAL_AI_PAYLOAD_RULES)


def test_external_ai_contract_does_not_claim_runtime_enablement() -> None:
    assert EXTERNAL_AI_RUNTIME_STATUS == {
        "external_ai_enabled": False,
        "phi_gateway_enabled": False,
        "approved_provider_allowlist_enabled": False,
        "external_payload_audit_enabled": False,
        "reason": (
            "External AI is blocked; this contract only defines requirements before "
            "any external provider can receive clinical payloads."
        ),
    }
