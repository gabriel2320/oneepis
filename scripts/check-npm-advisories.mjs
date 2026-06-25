import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const lockfilePath = path.join(repoRoot, "package-lock.json");
const osvApiBaseUrl = "https://api.osv.dev/v1";
const severityRank = new Map([
  ["unknown", -1],
  ["low", 0],
  ["medium", 1],
  ["moderate", 1],
  ["high", 2],
  ["critical", 3],
]);
const auditLevel = normalizeSeverityName(process.env.ONEEPIS_NPM_ADVISORY_LEVEL ?? "high");
const minimumSeverity = severityRank.get(auditLevel);
const waivers = [
  {
    id: "GHSA-qx2v-qp2m-jg93",
    packages: new Set(["postcss@8.4.31"]),
    reason:
      "Pinned by next@16.2.9 as an exact nested dependency; no Next 16 patch release updates it yet.",
  },
];

if (minimumSeverity === undefined || auditLevel === "unknown") {
  console.error(
    `Invalid ONEEPIS_NPM_ADVISORY_LEVEL="${process.env.ONEEPIS_NPM_ADVISORY_LEVEL}". Expected low, medium/moderate, high, or critical.`,
  );
  process.exit(2);
}

const lockedPackages = readLockedPackages();
const batchResults = await queryOsvBatch(lockedPackages);
const vulnerabilityPackages = collectVulnerabilityPackages(batchResults, lockedPackages);
const vulnerabilities = await fetchVulnerabilityDetails([...vulnerabilityPackages.keys()]);
const blockingVulnerabilities = vulnerabilities.filter(
  (vulnerability) =>
    (severityRank.get(vulnerability.severity) >= minimumSeverity ||
      vulnerability.severity === "unknown") &&
    !isWaived(vulnerability, vulnerabilityPackages),
);

console.log(`OSV check scanned ${lockedPackages.length} locked npm packages at ${auditLevel}+ severity.`);

if (vulnerabilities.length === 0) {
  console.log("No OSV vulnerabilities matched the locked package versions.");
  process.exit(0);
}

for (const vulnerability of vulnerabilities.sort(compareVulnerabilities)) {
  console.log(
    `- ${vulnerability.severity.toUpperCase()} ${vulnerability.id}: ${vulnerability.summary}`,
  );
  if (vulnerability.cvssScore !== null) {
    console.log(`  CVSS: ${vulnerability.cvssScore}`);
  }
  console.log(`  Packages: ${[...vulnerabilityPackages.get(vulnerability.id)].join(", ")}`);
  console.log(`  ${vulnerability.url}`);
  const waiver = matchingWaiver(vulnerability, vulnerabilityPackages);
  if (waiver) {
    console.log(`  Waived: ${waiver.reason}`);
  }
}

if (blockingVulnerabilities.length > 0) {
  console.error(`Found ${blockingVulnerabilities.length} OSV vulnerabilities at ${auditLevel}+ severity.`);
  process.exit(1);
}

console.log(`No OSV vulnerabilities at ${auditLevel}+ severity.`);

function readLockedPackages() {
  const lockfile = JSON.parse(readFileSync(lockfilePath, "utf8"));
  const packages = Object.entries(lockfile.packages ?? [])
    .filter(([packagePath, metadata]) => packagePath && metadata?.version)
    .map(([packagePath, metadata]) => ({
      name: metadata.name ?? packageNameFromLockfilePath(packagePath),
      version: metadata.version,
    }))
    .filter((item) => item.name && !item.name.startsWith("@oneepis/"));
  return [...new Map(packages.map((item) => [`${item.name}@${item.version}`, item])).values()].sort(
    (a, b) => `${a.name}@${a.version}`.localeCompare(`${b.name}@${b.version}`),
  );
}

function packageNameFromLockfilePath(packagePath) {
  const segments = packagePath.split("/node_modules/");
  const packagePathTail = segments.at(-1);
  if (!packagePathTail) {
    return null;
  }
  const packageSegments = packagePathTail.split("/");
  if (packageSegments[0]?.startsWith("@")) {
    return packageSegments.length >= 2 ? `${packageSegments[0]}/${packageSegments[1]}` : null;
  }
  return packageSegments[0] ?? null;
}

async function queryOsvBatch(packages) {
  const response = await postJson(`${osvApiBaseUrl}/querybatch`, {
    queries: packages.map((item) => ({
      package: {
        ecosystem: "npm",
        name: item.name,
      },
      version: item.version,
    })),
  });
  return response.results ?? [];
}

function collectVulnerabilityPackages(results, packages) {
  const vulnerabilityPackages = new Map();
  for (const [index, result] of results.entries()) {
    const lockedPackage = packages[index];
    for (const vulnerability of result.vulns ?? []) {
      const packageLabel = `${lockedPackage.name}@${lockedPackage.version}`;
      if (!vulnerabilityPackages.has(vulnerability.id)) {
        vulnerabilityPackages.set(vulnerability.id, new Set());
      }
      vulnerabilityPackages.get(vulnerability.id).add(packageLabel);
    }
  }
  return vulnerabilityPackages;
}

async function fetchVulnerabilityDetails(ids) {
  const details = [];
  for (const id of ids) {
    const vulnerability = await getJson(`${osvApiBaseUrl}/vulns/${encodeURIComponent(id)}`);
    details.push({
      id,
      summary: vulnerability.summary ?? "(no summary)",
      severity: normalizeSeverity(vulnerability),
      cvssScore: highestCvssScore(vulnerability),
      url: `https://osv.dev/vulnerability/${id}`,
    });
  }
  return details;
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

function normalizeSeverityName(severity) {
  const normalized = severity.toLowerCase();
  return normalized === "moderate" ? "medium" : normalized;
}

function highestCvssScore(vulnerability) {
  const scores = (vulnerability.severity ?? [])
    .map((entry) => Number(entry.score))
    .filter((score) => Number.isFinite(score));
  if (scores.length === 0) {
    return null;
  }
  return Math.max(...scores);
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

async function postJson(url, payload) {
  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "User-Agent": "oneepis-osv-check",
    },
    body: JSON.stringify(payload),
  });
  return readJsonResponse(response);
}

async function getJson(url) {
  const response = await fetch(url, {
    headers: {
      "User-Agent": "oneepis-osv-check",
    },
  });
  return readJsonResponse(response);
}

async function readJsonResponse(response) {
  if (!response.ok) {
    const body = await response.text();
    throw new Error(`OSV request failed: ${response.status} ${body}`);
  }
  return response.json();
}

function compareVulnerabilities(left, right) {
  const severityDelta = severityRank.get(right.severity) - severityRank.get(left.severity);
  if (severityDelta !== 0) {
    return severityDelta;
  }
  return left.id.localeCompare(right.id);
}

function isWaived(vulnerability, vulnerabilityPackages) {
  return Boolean(matchingWaiver(vulnerability, vulnerabilityPackages));
}

function matchingWaiver(vulnerability, vulnerabilityPackages) {
  const packages = vulnerabilityPackages.get(vulnerability.id) ?? new Set();
  return waivers.find(
    (waiver) =>
      waiver.id === vulnerability.id &&
      [...packages].every((packageLabel) => waiver.packages.has(packageLabel)),
  );
}
