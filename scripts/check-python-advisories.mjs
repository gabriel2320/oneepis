import { spawnSync } from "node:child_process";
import { mkdtempSync, readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

import { resolvePython } from "./python-command.mjs";

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const policyPath = path.join(repoRoot, "security/security-report-policy.json");
const osvApiBaseUrl = "https://api.osv.dev/v1";
const severityRank = new Map([
  ["unknown", -1],
  ["low", 0],
  ["medium", 1],
  ["moderate", 1],
  ["high", 2],
  ["critical", 3],
]);

export function validateSecurityReportPolicy(policy, now = new Date()) {
  const errors = [];
  if (policy?.schemaVersion !== 1) {
    errors.push("schemaVersion must be 1.");
  }
  if (typeof policy?.owner !== "string" || policy.owner.trim() === "") {
    errors.push("owner is required.");
  }
  for (const signalName of ["pip_audit", "dependency_review", "codeql"]) {
    const signal = policy?.signals?.[signalName];
    if (!signal) {
      errors.push(`signals.${signalName} is required.`);
      continue;
    }
    if (typeof signal.owner !== "string" || signal.owner.trim() === "") {
      errors.push(`signals.${signalName}.owner is required.`);
    }
    if (!Array.isArray(signal.baseline)) {
      errors.push(`signals.${signalName}.baseline must be an array.`);
    }
  }
  const pipAudit = policy?.signals?.pip_audit;
  if (pipAudit) {
    if (pipAudit.status !== "blocking_high_critical") {
      errors.push("signals.pip_audit.status must be blocking_high_critical.");
    }
    if (normalizeSeverityName(pipAudit.minimumBlockingSeverity ?? "") !== "high") {
      errors.push("signals.pip_audit.minimumBlockingSeverity must be high.");
    }
    if (!Array.isArray(pipAudit.waivers)) {
      errors.push("signals.pip_audit.waivers must be an array.");
    } else {
      for (const [index, waiver] of pipAudit.waivers.entries()) {
        errors.push(...validateWaiver(waiver, index, now));
      }
    }
  }
  return errors;
}

export function pythonAdvisoriesFromAuditJson(auditJson, severityById = new Map()) {
  const advisories = [];
  for (const dependency of auditJson.dependencies ?? []) {
    if (!Array.isArray(dependency.vulns)) {
      continue;
    }
    for (const vulnerability of dependency.vulns) {
      const aliases = Array.isArray(vulnerability.aliases) ? vulnerability.aliases : [];
      advisories.push({
        id: vulnerability.id,
        aliases,
        packageName: dependency.name,
        packageVersion: dependency.version,
        packageLabel: `${dependency.name}@${dependency.version}`,
        fixVersions: vulnerability.fix_versions ?? [],
        severity: severityForVulnerability(vulnerability.id, aliases, severityById),
        description: vulnerability.description ?? "",
      });
    }
  }
  return advisories;
}

export function blockingPythonAdvisories(advisories, policy) {
  const pipAudit = policy.signals.pip_audit;
  const minimumSeverity = severityRank.get(normalizeSeverityName(pipAudit.minimumBlockingSeverity));
  return advisories.filter((advisory) => {
    if (isWaived(advisory, pipAudit.waivers ?? [])) {
      return false;
    }
    const rank = severityRank.get(advisory.severity);
    if (advisory.severity === "unknown") {
      return Boolean(pipAudit.blockUnknownSeverity);
    }
    return rank >= minimumSeverity;
  });
}

export function normalizeSeverityName(severity) {
  const normalized = String(severity).toLowerCase();
  return normalized === "moderate" ? "medium" : normalized;
}

function readPolicy() {
  return JSON.parse(readFileSync(policyPath, "utf8"));
}

function runPipAuditJson() {
  const python = resolvePython();
  const cacheDir = mkdtempSync(path.join(tmpdir(), "oneepis-pip-audit-"));
  try {
    const result = spawnSync(
      python.command,
      [
        ...python.prefixArgs,
        "-m",
        "pip_audit",
        "--progress-spinner",
        "off",
        "--cache-dir",
        cacheDir,
        "--skip-editable",
        "--format",
        "json",
      ],
      {
        cwd: repoRoot,
        encoding: "utf8",
        shell: false,
      },
    );
    if (result.error) {
      throw new Error(`pip-audit failed to start: ${result.error.message}`);
    }
    if (![0, 1].includes(result.status)) {
      throw new Error(`pip-audit failed with status ${result.status}.\n${result.stderr}`);
    }
    const jsonText = extractJsonObject(result.stdout);
    if (!jsonText) {
      throw new Error(`pip-audit did not emit JSON.\n${result.stderr}`);
    }
    return JSON.parse(jsonText);
  } finally {
    rmSync(cacheDir, { recursive: true, force: true });
  }
}

function extractJsonObject(stdout) {
  const start = stdout.indexOf("{");
  const end = stdout.lastIndexOf("}");
  if (start < 0 || end < start) {
    return "";
  }
  return stdout.slice(start, end + 1);
}

async function fetchSeverityDetails(auditJson) {
  const ids = new Set();
  for (const dependency of auditJson.dependencies ?? []) {
    for (const vulnerability of dependency.vulns ?? []) {
      ids.add(vulnerability.id);
      for (const alias of vulnerability.aliases ?? []) {
        ids.add(alias);
      }
    }
  }
  const severityById = new Map();
  for (const id of ids) {
    const detail = await fetchOsvDetail(id);
    if (!detail) {
      continue;
    }
    severityById.set(id, normalizeSeverity(detail));
  }
  return severityById;
}

async function fetchOsvDetail(id) {
  const response = await fetch(`${osvApiBaseUrl}/vulns/${encodeURIComponent(id)}`, {
    headers: { "User-Agent": "oneepis-python-advisory-check" },
  });
  if (response.status === 404) {
    return null;
  }
  if (!response.ok) {
    throw new Error(`OSV request failed for ${id}: ${response.status} ${await response.text()}`);
  }
  return response.json();
}

function normalizeSeverity(vulnerability) {
  const databaseSeverity = vulnerability.database_specific?.severity;
  if (typeof databaseSeverity === "string") {
    const normalized = normalizeSeverityName(databaseSeverity);
    if (severityRank.has(normalized)) {
      return normalized;
    }
  }
  const cvssScore = highestCvssScore(vulnerability);
  if (cvssScore !== null) {
    return severityFromCvssScore(cvssScore);
  }
  return "unknown";
}

function severityForVulnerability(id, aliases, severityById) {
  for (const candidate of [id, ...aliases]) {
    const severity = severityById.get(candidate);
    if (severity) {
      return severity;
    }
  }
  return "unknown";
}

function highestCvssScore(vulnerability) {
  const scores = (vulnerability.severity ?? [])
    .map((entry) => Number(entry.score))
    .filter((score) => Number.isFinite(score));
  return scores.length > 0 ? Math.max(...scores) : null;
}

function severityFromCvssScore(score) {
  if (score >= 9) {
    return "critical";
  }
  if (score >= 7) {
    return "high";
  }
  if (score >= 4) {
    return "medium";
  }
  return "low";
}

function validateWaiver(waiver, index, now) {
  const prefix = `signals.pip_audit.waivers[${index}]`;
  const errors = [];
  for (const field of ["id", "owner", "reason", "expiresAt"]) {
    if (typeof waiver?.[field] !== "string" || waiver[field].trim() === "") {
      errors.push(`${prefix}.${field} is required.`);
    }
  }
  if (!Array.isArray(waiver?.packages) || waiver.packages.length === 0) {
    errors.push(`${prefix}.packages must be a non-empty array.`);
  }
  const expiresAt = Date.parse(`${waiver?.expiresAt ?? ""}T23:59:59Z`);
  if (!Number.isFinite(expiresAt)) {
    errors.push(`${prefix}.expiresAt must be an ISO date.`);
  } else if (expiresAt < now.getTime()) {
    errors.push(`${prefix}.expiresAt is expired.`);
  }
  return errors;
}

function isWaived(advisory, waivers) {
  return Boolean(matchingWaiver(advisory, waivers));
}

function matchingWaiver(advisory, waivers) {
  return waivers.find((waiver) => {
    const waiverIds = new Set([waiver.id, ...(waiver.aliases ?? [])]);
    const advisoryIds = new Set([advisory.id, ...advisory.aliases]);
    const idMatches = [...advisoryIds].some((id) => waiverIds.has(id));
    return idMatches && waiver.packages.includes(advisory.packageLabel);
  });
}

function auditedDependencyCount(auditJson) {
  return (auditJson.dependencies ?? []).filter((dependency) => dependency.version).length;
}

function compareAdvisories(left, right) {
  const severityDelta = severityRank.get(right.severity) - severityRank.get(left.severity);
  if (severityDelta !== 0) {
    return severityDelta;
  }
  return `${left.id}:${left.packageLabel}`.localeCompare(`${right.id}:${right.packageLabel}`);
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const policy = readPolicy();
  const errors = validateSecurityReportPolicy(policy);
  if (errors.length > 0) {
    console.error("Python advisory policy is invalid.");
    for (const error of errors) {
      console.error(`- ${error}`);
    }
    process.exit(1);
  }
  const auditJson = runPipAuditJson();
  const severityById = await fetchSeverityDetails(auditJson);
  const advisories = pythonAdvisoriesFromAuditJson(auditJson, severityById);
  const blocking = blockingPythonAdvisories(advisories, policy);
  const auditLevel = policy.signals.pip_audit.minimumBlockingSeverity;

  console.log(
    `Python advisory guard scanned ${auditedDependencyCount(auditJson)} packages at ${auditLevel}+ severity.`,
  );
  for (const advisory of advisories.sort(compareAdvisories)) {
    console.log(
      `- ${advisory.severity.toUpperCase()} ${advisory.id}: ${advisory.packageLabel}`,
    );
    if (advisory.fixVersions.length > 0) {
      console.log(`  Fix versions: ${advisory.fixVersions.join(", ")}`);
    }
    if (advisory.aliases.length > 0) {
      console.log(`  Aliases: ${advisory.aliases.join(", ")}`);
    }
    const waiver = matchingWaiver(advisory, policy.signals.pip_audit.waivers ?? []);
    if (waiver) {
      console.log(`  Waived until ${waiver.expiresAt}: ${waiver.reason}`);
    }
  }
  if (blocking.length > 0) {
    console.error(`Found ${blocking.length} Python advisories at ${auditLevel}+ severity.`);
    process.exit(1);
  }
  console.log(`No Python advisories at ${auditLevel}+ severity.`);
}
