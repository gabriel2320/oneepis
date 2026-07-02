import assert from "node:assert/strict";

import {
  blockingPythonAdvisories,
  pythonAdvisoriesFromAuditJson,
  validateSecurityReportPolicy,
} from "./check-python-advisories.mjs";

const basePolicy = {
  schemaVersion: 1,
  owner: "EPIONE security",
  signals: {
    pip_audit: {
      status: "blocking_high_critical",
      owner: "EPIONE security",
      minimumBlockingSeverity: "high",
      blockUnknownSeverity: true,
      baseline: [],
      waivers: [],
    },
    dependency_review: {
      status: "report_only",
      owner: "EPIONE security",
      baseline: [],
    },
    codeql: {
      status: "report_only",
      owner: "EPIONE security",
      baseline: [],
    },
  },
};

assert.deepEqual(validateSecurityReportPolicy(basePolicy, new Date("2026-07-02T12:00:00Z")), []);

const advisories = pythonAdvisoriesFromAuditJson(
  {
    dependencies: [
      {
        name: "pytest",
        version: "8.4.2",
        vulns: [
          {
            id: "CVE-2025-71176",
            aliases: ["GHSA-6w46-j5rx-g56g"],
            fix_versions: ["9.0.3"],
          },
        ],
      },
      {
        name: "demo-low",
        version: "1.0.0",
        vulns: [{ id: "LOW-1", aliases: [], fix_versions: ["1.0.1"] }],
      },
    ],
  },
  new Map([
    ["CVE-2025-71176", "high"],
    ["LOW-1", "low"],
  ]),
);

assert.deepEqual(
  blockingPythonAdvisories(advisories, basePolicy).map((advisory) => advisory.id),
  ["CVE-2025-71176"],
);

const waivedPolicy = structuredClone(basePolicy);
waivedPolicy.signals.pip_audit.waivers = [
  {
    id: "GHSA-6w46-j5rx-g56g",
    packages: ["pytest@8.4.2"],
    owner: "EPIONE security",
    reason: "Temporary test waiver.",
    expiresAt: "2026-07-31",
  },
];

assert.deepEqual(validateSecurityReportPolicy(waivedPolicy, new Date("2026-07-02T12:00:00Z")), []);
assert.deepEqual(blockingPythonAdvisories(advisories, waivedPolicy), []);

const expiredPolicy = structuredClone(waivedPolicy);
expiredPolicy.signals.pip_audit.waivers[0].expiresAt = "2026-01-01";
assert.match(
  validateSecurityReportPolicy(expiredPolicy, new Date("2026-07-02T12:00:00Z")).join("\n"),
  /expired/,
);

console.log("Python advisory guard self-test passed.");
