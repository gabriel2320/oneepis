import { readdirSync, readFileSync, statSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const routeRoot = path.join(repoRoot, "apps/api/src/oneepis_api/api/v1/routes");
const allowedHelperFiles = new Set([
  "apps/api/src/oneepis_api/api/v1/routes/patient_shared.py",
]);
const allowedEnforcementMarkers = [
  "enforce_patient_scope_for_read",
  "enforce_assistant_read_scope",
];

const errors = [];
let checkedReadFiles = 0;

for (const file of walk(routeRoot)) {
  const relativePath = toRepoPath(file);
  const content = readFileSync(file, "utf8");
  if (!content.includes("record_patient_scoped_read")) {
    continue;
  }
  if (allowedHelperFiles.has(relativePath)) {
    continue;
  }
  checkedReadFiles += 1;
  if (!allowedEnforcementMarkers.some((marker) => content.includes(marker))) {
    errors.push(
      `${relativePath} records patient-scoped reads but does not enforce patient scope.`,
    );
  }
}

if (checkedReadFiles === 0) {
  errors.push("No patient-scoped read route files were checked.");
}

if (errors.length > 0) {
  console.error("Patient-scoped read enforcement guard failed.");
  for (const error of errors) {
    console.error(`- ${error}`);
  }
  process.exit(1);
}

console.log(
  `Patient-scoped read enforcement guard passed: ${checkedReadFiles} route files checked.`,
);

function walk(root) {
  return readdirSync(root).flatMap((name) => {
    const fullPath = path.join(root, name);
    const stats = statSync(fullPath);
    if (stats.isDirectory()) {
      return walk(fullPath);
    }
    if (!stats.isFile() || !name.endsWith(".py")) {
      return [];
    }
    return [fullPath];
  });
}

function toRepoPath(file) {
  return path.relative(repoRoot, file).split(path.sep).join("/");
}
