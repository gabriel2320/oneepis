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
  "enforce_and_record_assistant_read",
];
const allowedReadAuditMarkers = [
  "record_patient_scoped_read",
  "record_read_audit_event",
  "enforce_and_record_assistant_read",
];
const auditOnlyReadActions = [
  "patient_audit.read",
];

const errors = [];
let checkedReadHandlers = 0;

for (const file of walk(routeRoot)) {
  const relativePath = toRepoPath(file);
  const content = readFileSync(file, "utf8");
  if (allowedHelperFiles.has(relativePath)) {
    continue;
  }
  const functions = functionsInFile(content);
  const auditMarkers = [
    ...allowedReadAuditMarkers,
    ...functions
      .filter((fn) => allowedReadAuditMarkers.some((marker) => fn.body.includes(marker)))
      .map((fn) => `${fn.name}(`),
  ];
  const enforcementMarkers = [
    ...allowedEnforcementMarkers,
    ...functions
      .filter((fn) => allowedEnforcementMarkers.some((marker) => fn.body.includes(marker)))
      .map((fn) => `${fn.name}(`),
  ];
  const readHandlers = functions.filter((fn) => isPatientScopedReadHandler(fn));
  for (const fn of readHandlers) {
    const firstReadAudit = firstMarkerIndex(fn.body, auditMarkers);
    const firstEnforcement = firstMarkerIndex(fn.body, enforcementMarkers);
    checkedReadHandlers += 1;
    if (firstReadAudit < 0 && !isAuditOnlyReadHandler(fn)) {
      errors.push(
        `${relativePath}:${fn.line} ${fn.name} is a patient-scoped read handler without patient-scoped read audit.`,
      );
      continue;
    }
    if (isAuditOnlyReadHandler(fn)) {
      continue;
    }
    if (firstEnforcement < 0 || firstEnforcement > firstReadAudit) {
      errors.push(
        `${relativePath}:${fn.line} ${fn.name} records patient-scoped reads before patient-scope enforcement.`,
      );
    }
  }
}

if (checkedReadHandlers === 0) {
  errors.push("No patient-scoped read route handlers were checked.");
}

if (errors.length > 0) {
  console.error("Patient-scoped read enforcement guard failed.");
  for (const error of errors) {
    console.error(`- ${error}`);
  }
  process.exit(1);
}

console.log(
  `Patient-scoped read enforcement guard passed: ${checkedReadHandlers} route handlers checked.`,
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
      routeDecorator: routeDecorator(lines, index),
      body: bodyLines.join("\n"),
    });
  }
  return functions;
}

function routeDecorator(lines, functionIndex) {
  const decoratorLines = [];
  for (let cursor = functionIndex - 1; cursor >= 0; cursor -= 1) {
    const line = lines[cursor];
    if (line.startsWith("@router.")) {
      decoratorLines.unshift(line);
      const text = decoratorLines.join("\n");
      const methodMatch = text.match(/@router\.(get|post|put|patch|delete)\b/);
      return {
        method: methodMatch?.[1] ?? null,
        text,
      };
    }
    if (
      line.trim() === "" ||
      line.startsWith("@") ||
      line.startsWith(" ") ||
      line.trim() === ")"
    ) {
      decoratorLines.unshift(line);
      continue;
    }
    return null;
  }
  return null;
}

function firstMarkerIndex(content, markers) {
  const indexes = markers
    .map((marker) => content.indexOf(marker))
    .filter((index) => index >= 0);
  return indexes.length === 0 ? -1 : Math.min(...indexes);
}

function isPatientScopedReadHandler(fn) {
  return fn.routeDecorator?.method === "get" && fn.routeDecorator.text.includes("{patient_id}");
}

function isAuditOnlyReadHandler(fn) {
  return auditOnlyReadActions.some((action) => fn.body.includes(action));
}
