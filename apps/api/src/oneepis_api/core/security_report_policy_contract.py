from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class SecurityReportCheck:
    key: str
    ci_step_name: str
    status: Literal["blocking", "report_only"]
    promotion_requirement: str


@dataclass(frozen=True)
class SecurityReportPolicyRequirement:
    key: str
    label: str
    criterion: str
    status: Literal["required_before_blocking_gate"]


SECURITY_REPORT_CHECKS: tuple[SecurityReportCheck, ...] = (
    SecurityReportCheck(
        key="gitleaks",
        ci_step_name="Secret scan report",
        status="blocking",
        promotion_requirement="Already blocks CI.",
    ),
    SecurityReportCheck(
        key="osv_npm_advisory_high",
        ci_step_name="OSV npm advisory high+ gate",
        status="blocking",
        promotion_requirement="Already blocks high and critical npm advisories.",
    ),
    SecurityReportCheck(
        key="pip_audit_high",
        ci_step_name="pip-audit high+ gate",
        status="blocking",
        promotion_requirement="Blocks high and critical Python advisories with reviewed waivers.",
    ),
    SecurityReportCheck(
        key="dependency_review",
        ci_step_name="Dependency review report",
        status="report_only",
        promotion_requirement="Needs reviewed baseline, owner, waiver process and severity SLA.",
    ),
    SecurityReportCheck(
        key="codeql",
        ci_step_name="CodeQL analyze report",
        status="report_only",
        promotion_requirement="Needs reviewed baseline, owner, waiver process and severity SLA.",
    ),
)


SECURITY_REPORT_POLICY_REQUIREMENTS: tuple[SecurityReportPolicyRequirement, ...] = (
    SecurityReportPolicyRequirement(
        key="reviewed_baseline",
        label="Reviewed baseline",
        criterion="Report-only findings need a reviewed baseline before blocking CI.",
        status="required_before_blocking_gate",
    ),
    SecurityReportPolicyRequirement(
        key="triage_owner",
        label="Triage owner",
        criterion="Every report-only gate needs an accountable owner for triage.",
        status="required_before_blocking_gate",
    ),
    SecurityReportPolicyRequirement(
        key="waiver_process",
        label="Waiver process",
        criterion="Accepted findings need expiry, rationale and review trail.",
        status="required_before_blocking_gate",
    ),
    SecurityReportPolicyRequirement(
        key="severity_sla",
        label="Severity SLA",
        criterion="Findings need severity-based review and remediation timelines.",
        status="required_before_blocking_gate",
    ),
)


def security_report_check_keys() -> tuple[str, ...]:
    return tuple(check.key for check in SECURITY_REPORT_CHECKS)


def report_only_security_check_keys() -> tuple[str, ...]:
    return tuple(check.key for check in SECURITY_REPORT_CHECKS if check.status == "report_only")


def blocking_security_check_keys() -> tuple[str, ...]:
    return tuple(check.key for check in SECURITY_REPORT_CHECKS if check.status == "blocking")


def security_report_policy_requirement_keys() -> tuple[str, ...]:
    return tuple(requirement.key for requirement in SECURITY_REPORT_POLICY_REQUIREMENTS)
