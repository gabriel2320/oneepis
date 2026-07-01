import { readdirSync, readFileSync, statSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const routeRoot = path.join(repoRoot, "apps/api/src/oneepis_api/api/v1/routes");
const allowedHelperFiles = new Set([
  "apps/api/src/oneepis_api/api/v1/routes/patient_shared.py",
  "apps/api/src/oneepis_api/api/v1/routes/patient_assistant_scope.py",
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
  const functions = functionsInFile(content);
  const auditMarkers = [
    "record_patient_scoped_read",
    ...functions
      .filter((fn) => fn.body.includes("record_patient_scoped_read"))
      .map((fn) => `${fn.name}(`),
  ];
  const enforcementMarkers = [
    ...allowedEnforcementMarkers,
    ...functions
      .filter((fn) => allowedEnforcementMarkers.some((marker) => fn.body.includes(marker)))
      .map((fn) => `${fn.name}(`),
  ];
  const readHandlers = functions.filter(
    (fn) => fn.isRouteHandler && firstMarkerIndex(fn.body, auditMarkers) >= 0,
  );
  if (readHandlers.length === 0) {
    errors.push(`${relativePath} imports patient-scoped read audit but no route handler call was found.`);
    continue;
  }
  checkedReadFiles += 1;
  for (const fn of readHandlers) {
    const firstReadAudit = firstMarkerIndex(fn.body, auditMarkers);
    const firstEnforcement = firstMarkerIndex(fn.body, enforcementMarkers);
    if (firstEnforcement < 0 || firstEnforcement > firstReadAudit) {
      errors.push(
        `${relativePath}:${fn.line} ${fn.name} records patient-scoped reads before patient-scope enforcement.`,
      );
    }
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

function functionsInFile(content) {
  const lines = content.split("\n");
  const functions = [];
  for (let index = 0; index < lines.length; index += 1) {
    const match = lines[index].match(/^def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(/);
    if (!match) {
      continue;
    }
    const bodyLines = [];
    for (let cursor = index + 1; cursor < lines.length; cursor += 1) {
      const line = lines[cursor];
      if (/^(def|@router\.|[A-Za-z_][A-Za-z0-9_]*\s*=)/.test(line)) {
        break;
      }
      bodyLines.push(line);
    }
    functions.push({
      name: match[1],
      line: index + 1,
      isRouteHandler: hasRouterDecorator(lines, index),
      body: bodyLines.join("\n"),
    });
  }
  return functions;
}

function hasRouterDecorator(lines, functionIndex) {
  for (let cursor = functionIndex - 1; cursor >= 0; cursor -= 1) {
    const line = lines[cursor];
    if (line.startsWith("@router.")) {
      return true;
    }
    if (
      line.trim() === "" ||
      line.startsWith("@") ||
      line.startsWith(" ") ||
      line.trim() === ")"
    ) {
      continue;
    }
    return false;
  }
  return false;
}

function firstMarkerIndex(content, markers) {
  const indexes = markers
    .map((marker) => content.indexOf(marker))
    .filter((index) => index >= 0);
  return indexes.length === 0 ? -1 : Math.min(...indexes);
}
