from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class ExternalAIRequirement:
    key: str
    label: str
    criterion: str
    status: Literal["required_before_external_ai"]


@dataclass(frozen=True)
class ExternalAIPayloadRule:
    key: str
    payload_state: Literal["blocked", "requires_gateway"]
    reason: str


EXTERNAL_AI_REQUIREMENTS: tuple[ExternalAIRequirement, ...] = (
    ExternalAIRequirement(
        key="phi_privacy_gateway",
        label="PHI privacy gateway",
        criterion=(
            "External AI traffic must pass through a privacy gateway that "
            "classifies, minimizes and blocks unsafe PHI payloads."
        ),
        status="required_before_external_ai",
    ),
    ExternalAIRequirement(
        key="deidentification_or_minimization",
        label="De-identification or minimization",
        criterion=(
            "Payloads must be de-identified or minimized to the approved use "
            "case before leaving the controlled environment."
        ),
        status="required_before_external_ai",
    ),
    ExternalAIRequirement(
        key="approved_provider_allowlist",
        label="Approved provider allowlist",
        criterion=(
            "External providers must be explicitly approved with endpoint, data "
            "processing terms and retention behavior documented."
        ),
        status="required_before_external_ai",
    ),
    ExternalAIRequirement(
        key="explicit_human_opt_in",
        label="Explicit human opt-in",
        criterion=(
            "A qualified user must explicitly opt in per workflow or policy "
            "scope before external AI is used."
        ),
        status="required_before_external_ai",
    ),
    ExternalAIRequirement(
        key="external_ai_audit",
        label="External AI audit",
        criterion=(
            "Every external AI request must audit actor, patient scope if any, "
            "provider, purpose, payload classification and correlation id."
        ),
        status="required_before_external_ai",
    ),
    ExternalAIRequirement(
        key="legal_security_review",
        label="Legal and security review",
        criterion=(
            "Legal, security and clinical governance must approve the provider, "
            "payload policy and allowed use."
        ),
        status="required_before_external_ai",
    ),
)


EXTERNAL_AI_PAYLOAD_RULES: tuple[ExternalAIPayloadRule, ...] = (
    ExternalAIPayloadRule(
        key="raw_clinical_note",
        payload_state="blocked",
        reason="Raw clinical free text can contain direct or indirect PHI.",
    ),
    ExternalAIPayloadRule(
        key="patient_identifier",
        payload_state="blocked",
        reason="Direct patient identifiers must not leave the controlled environment.",
    ),
    ExternalAIPayloadRule(
        key="document_attachment",
        payload_state="blocked",
        reason="Document upload workflows and custody controls are not productive yet.",
    ),
    ExternalAIPayloadRule(
        key="minimized_structured_context",
        payload_state="requires_gateway",
        reason="Structured context still requires gateway classification and audit.",
    ),
)


EXTERNAL_AI_RUNTIME_STATUS = {
    "external_ai_enabled": False,
    "phi_gateway_enabled": False,
    "approved_provider_allowlist_enabled": False,
    "external_payload_audit_enabled": False,
    "reason": (
        "External AI is blocked; this contract only defines requirements before "
        "any external provider can receive clinical payloads."
    ),
}


def external_ai_requirement_keys() -> tuple[str, ...]:
    return tuple(requirement.key for requirement in EXTERNAL_AI_REQUIREMENTS)


def external_ai_payload_rule_keys() -> tuple[str, ...]:
    return tuple(rule.key for rule in EXTERNAL_AI_PAYLOAD_RULES)
