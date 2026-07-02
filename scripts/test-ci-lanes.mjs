import { classifyChangedFiles } from "./ci-lanes.mjs";

const cases = [
  {
    name: "docs canon handoff runs contracts only",
    files: ["docs/CODEX_PLAN.md"],
    expected: { contracts: true, api: false, web: false, e2e: false, full: false },
  },
  {
    name: "api source runs api and contracts",
    files: ["apps/api/src/oneepis_api/api/v1/routes/patient_allergies.py"],
    expected: { api: true, contracts: true, web: false, e2e: false, full: false },
  },
  {
    name: "web app surface runs web and e2e",
    files: ["apps/web/src/app/pacientes/page.tsx"],
    expected: { web: true, e2e: true, api: false, full: false },
  },
  {
    name: "web library changes run web without full e2e lane",
    files: ["apps/web/src/lib/clinical-api.ts"],
    expected: { web: true, e2e: false, api: false, full: false },
  },
  {
    name: "alembic migration runs postgres",
    files: ["apps/api/alembic/versions/202607020001_patient_scope.py"],
    expected: { api: true, contracts: true, postgres: true, full: false },
  },
  {
    name: "workflow changes force full ci",
    files: [".github/workflows/ci.yml"],
    expected: { full: true },
  },
  {
    name: "package lock runs web and security",
    files: ["package-lock.json"],
    expected: { web: true, e2e: true, security: true, full: false },
  },
];

const failures = [];

for (const testCase of cases) {
  const lanes = classifyChangedFiles(testCase.files);
  for (const [lane, expectedValue] of Object.entries(testCase.expected)) {
    if (lanes[lane] !== expectedValue) {
      failures.push(
        `${testCase.name}: expected ${lane}=${expectedValue}, got ${lanes[lane]}`,
      );
    }
  }
}

if (failures.length > 0) {
  console.error("CI lane self-test failed.");
  for (const failure of failures) {
    console.error(`- ${failure}`);
  }
  process.exit(1);
}

console.log(`CI lane self-test passed: ${cases.length} cases checked.`);
