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


def test_security_report_contract_tracks_current_ci_gates() -> None:
    assert security_report_check_keys() == (
        "gitleaks",
        "osv_npm_advisory_high",
        "dependency_review",
        "codeql",
        "pip_audit",
    )
    assert blocking_security_check_keys() == ("gitleaks", "osv_npm_advisory_high")
    assert report_only_security_check_keys() == (
        "dependency_review",
        "codeql",
        "pip_audit",
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
        "pip-audit report",
    ):
        step_block = workflow.split(f"name: {step_name}", maxsplit=1)[1].split(
            "\n      - name:",
            maxsplit=1,
        )[0]
        assert "continue-on-error: true" in step_block


def test_blocking_security_steps_do_not_use_continue_on_error() -> None:
    workflow = CI_WORKFLOW.read_text()

    for step_name in ("Secret scan report", "OSV npm advisory high+ gate"):
        step_block = workflow.split(f"name: {step_name}", maxsplit=1)[1].split(
            "\n      - name:",
            maxsplit=1,
        )[0]
        assert "continue-on-error: true" not in step_block
