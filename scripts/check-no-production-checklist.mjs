import { existsSync, readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const checklistPath = path.join(repoRoot, "docs/NO_PRODUCTION_CHECKLIST.md");
const checklist = readFileSync(checklistPath, "utf8");

const requiredGateIds = [
  "NOPROD-SEC-001",
  "NOPROD-SEC-002",
  "NOPROD-SEC-003",
  "NOPROD-SEC-004",
  "NOPROD-SEC-005",
  "NOPROD-SEC-006",
  "NOPROD-SEC-007",
  "NOPROD-SEC-008",
  "NOPROD-SEC-009",
  "NOPROD-SEC-010",
  "NOPROD-SEC-011",
  "NOPROD-SEC-012",
];

const requiredEvidenceByGate = new Map([
  [
    "NOPROD-SEC-005",
    [
      "apps/api/tests/test_patient_read_audit.py",
      "apps/api/tests/test_patient_audit.py",
    ],
  ],
  [
    "NOPROD-SEC-006",
    ["apps/api/tests/test_phi_logging.py", "scripts/check-frontend-phi-logs.mjs"],
  ],
  [
    "NOPROD-SEC-007",
    [
      "apps/api/src/oneepis_api/core/clinical_access.py",
      "apps/api/src/oneepis_api/core/access_context_contract.py",
      "apps/api/src/oneepis_api/core/access_boundary_contract.py",
      "apps/api/src/oneepis_api/services/patient_access_relationship.py",
      "apps/api/tests/test_break_glass_guard.py",
      "apps/api/tests/test_clinical_access_contract.py",
      "apps/api/tests/test_access_context_contract.py",
      "apps/api/tests/test_access_boundary_contract.py",
      "apps/api/tests/test_patient_access_relationship.py",
      "apps/api/tests/test_patient_abac_enforcement.py",
    ],
  ],
  [
    "NOPROD-SEC-008",
    [
      "apps/api/src/oneepis_api/core/productive_auth_contract.py",
      "apps/api/tests/test_auth_session_contract.py",
      "apps/api/tests/test_productive_auth_contract.py",
    ],
  ],
]);

const errors = [];
const rowsById = new Map();

for (const line of checklist.split("\n")) {
  if (!line.startsWith("| NOPROD-SEC-")) {
    continue;
  }
  const cells = line
    .split("|")
    .slice(1, -1)
    .map((cell) => cell.trim());
  if (cells.length !== 5) {
    errors.push(`${cells[0] ?? "Unknown gate"} must have 5 table columns.`);
    continue;
  }
  const [id, gate, status, criterion, evidence] = cells;
  if (rowsById.has(id)) {
    errors.push(`${id} is duplicated.`);
  }
  rowsById.set(id, { gate, status, criterion, evidence });
}

for (const id of requiredGateIds) {
  if (!rowsById.has(id)) {
    errors.push(`${id} is missing from docs/NO_PRODUCTION_CHECKLIST.md.`);
  }
}

for (const [id, row] of rowsById.entries()) {
  if (!requiredGateIds.includes(id)) {
    errors.push(`${id} is not part of the versioned no-production gate inventory.`);
  }
  if (!["pendiente", "en progreso", "bloqueada"].includes(row.status)) {
    errors.push(`${id} has invalid status '${row.status}'.`);
  }
  if (!row.gate || !row.criterion || !row.evidence) {
    errors.push(`${id} must include gate, minimum criterion and evidence.`);
  }
  for (const referencedPath of markdownCodePaths(row.evidence)) {
    if (!existsSync(path.join(repoRoot, referencedPath))) {
      errors.push(`${id} references missing evidence path: ${referencedPath}`);
    }
  }
}

for (const [id, requiredPaths] of requiredEvidenceByGate.entries()) {
  const evidence = rowsById.get(id)?.evidence ?? "";
  for (const requiredPath of requiredPaths) {
    if (!evidence.includes(`\`${requiredPath}\``)) {
      errors.push(`${id} must reference ${requiredPath}.`);
    }
  }
}

if (errors.length > 0) {
  console.error("No-production checklist guard failed.");
  for (const error of errors) {
    console.error(`- ${error}`);
  }
  process.exit(1);
}

console.log(`No-production checklist guard passed: ${requiredGateIds.length} gates checked.`);

function markdownCodePaths(text) {
  return [...text.matchAll(/`([^`]+)`/g)]
    .map((match) => match[1])
    .filter((value) => /^(apps|docs|packages|scripts)\//.test(value));
}
