import json
from pathlib import Path

from oneepis_api.core.security_report_policy_contract import (
    SECURITY_REPORT_CHECKS,
    SECURITY_REPORT_POLICY_REQUIREMENTS,
    blocking_security_check_keys,
    report_only_security_check_keys,
    security_report_check_keys,
    security_report_policy_requirement_keys,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
CI_WORKFLOW = REPO_ROOT / ".github/workflows/ci.yml"
SECURITY_REPORT_POLICY = REPO_ROOT / "security/security-report-policy.json"


def test_security_report_contract_tracks_current_ci_gates() -> None:
    assert security_report_check_keys() == (
        "gitleaks",
        "osv_npm_advisory_high",
        "pip_audit_high",
        "dependency_review",
        "codeql",
    )
    assert blocking_security_check_keys() == (
        "gitleaks",
        "osv_npm_advisory_high",
        "pip_audit_high",
    )
    assert report_only_security_check_keys() == (
        "dependency_review",
        "codeql",
    )


def test_report_only_policy_requirements_are_explicit() -> None:
    assert security_report_policy_requirement_keys() == (
        "reviewed_baseline",
        "triage_owner",
        "waiver_process",
        "severity_sla",
    )
    assert all(requirement.label for requirement in SECURITY_REPORT_POLICY_REQUIREMENTS)
    assert all(requirement.criterion for requirement in SECURITY_REPORT_POLICY_REQUIREMENTS)
    assert {requirement.status for requirement in SECURITY_REPORT_POLICY_REQUIREMENTS} == {
        "required_before_blocking_gate"
    }


def test_security_report_contract_matches_workflow_step_names() -> None:
    workflow = CI_WORKFLOW.read_text()

    for check in SECURITY_REPORT_CHECKS:
        assert f"name: {check.ci_step_name}" in workflow


def test_report_only_ci_steps_remain_explicitly_non_blocking() -> None:
    workflow = CI_WORKFLOW.read_text()

    for step_name in (
        "Dependency review report",
        "CodeQL init report",
        "CodeQL analyze report",
    ):
        step_block = workflow.split(f"name: {step_name}", maxsplit=1)[1].split(
            "\n      - name:",
            maxsplit=1,
        )[0]
        assert "continue-on-error: true" in step_block


def test_blocking_security_steps_do_not_use_continue_on_error() -> None:
    workflow = CI_WORKFLOW.read_text()

    for step_name in ("Secret scan report", "OSV npm advisory high+ gate", "pip-audit high+ gate"):
        step_block = workflow.split(f"name: {step_name}", maxsplit=1)[1].split(
            "\n      - name:",
            maxsplit=1,
        )[0]
        assert "continue-on-error: true" not in step_block


def test_security_report_policy_baseline_and_waiver_contract_is_versioned() -> None:
    policy = json.loads(SECURITY_REPORT_POLICY.read_text())

    assert policy["schemaVersion"] == 1
    assert policy["owner"]
    assert policy["signals"]["pip_audit"]["status"] == "blocking_high_critical"
    assert policy["signals"]["pip_audit"]["minimumBlockingSeverity"] == "high"
    assert policy["signals"]["pip_audit"]["blockUnknownSeverity"] is True
    assert isinstance(policy["signals"]["pip_audit"]["baseline"], list)
    assert isinstance(policy["signals"]["pip_audit"]["waivers"], list)

    for signal_name in ("dependency_review", "codeql"):
        signal = policy["signals"][signal_name]
        assert signal["status"] == "report_only"
        assert signal["owner"]
        assert isinstance(signal["baseline"], list)
        assert signal["promotionRequirement"]

    for waiver in policy["signals"]["pip_audit"]["waivers"]:
        assert waiver["id"]
        assert waiver["packages"]
        assert waiver["owner"]
        assert waiver["reason"]
        assert waiver["expiresAt"]
