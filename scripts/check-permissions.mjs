#!/usr/bin/env node
import { existsSync, mkdirSync, readdirSync, readFileSync, statSync, writeFileSync } from "node:fs";
import { dirname, join, relative } from "node:path";

const root = process.cwd();
const routeDir = "apps/api/src/oneepis_api/api/v1/routes";
const testFiles = readTree("apps/api/tests", [".py"]).filter(
  (path) => !path.endsWith("conftest.py") && !path.includes("helpers"),
);

const excludedFiles = new Set(["auth.py", "health.py", "ai.py", "patient_shared.py", "patient_audit.py"]);
const readLikePosts = new Set([
  "patient_core.py POST /{patient_id}/ai/suggestions",
]);
const delegatedAuditMarkers = [
  "confirm_patch_service(",
];
const forbiddenTestFilesByRoute = {
  "hospitalization.py": ["apps/api/tests/test_hospital_beds.py"],
  "hospitalization_daily_sheets.py": ["apps/api/tests/test_hospital_daily_sheets.py"],
  "hospitalization_indications.py": ["apps/api/tests/test_hospital_indications.py"],
  "patient_ai.py": ["apps/api/tests/test_patient_permissions.py"],
  "patient_allergies.py": ["apps/api/tests/test_patient_permissions.py"],
  "patient_core.py": ["apps/api/tests/test_patient_permissions.py"],
  "patient_encounters.py": ["apps/api/tests/test_patient_permissions.py"],
  "patient_entries.py": ["apps/api/tests/test_patient_permissions.py"],
  "patient_events.py": ["apps/api/tests/test_patient_permissions.py"],
  "patient_medications.py": ["apps/api/tests/test_patient_permissions.py"],
  "patient_problems.py": ["apps/api/tests/test_patient_permissions.py"],
  "patient_vitals.py": ["apps/api/tests/test_patient_permissions.py"],
};

const routeFiles = readTree(routeDir, [".py"]).filter((path) => !excludedFiles.has(path.split("/").at(-1)));
const rows = routeFiles.flatMap(inspectRouteFile);
const criticalRows = rows.filter((row) => row.critical_gaps.length > 0);
const warningRows = rows.filter((row) => row.warnings.length > 0);
const report = {
  generated_at: new Date().toISOString(),
  scope: "clinical_write_permissions",
  rows,
  summary: {
    routes_checked: rows.length,
    critical_gaps: criticalRows.length,
    warnings: rows.reduce((total, row) => total + row.warnings.length, 0),
  },
};

write("reports/permissions-map.json", `${JSON.stringify(report, null, 2)}\n`);
write("reports/permissions-map.md", renderMarkdown(report));

if (criticalRows.length > 0) {
  console.error(`Permission guard failed: ${criticalRows.length} critical route gap(s).`);
  for (const row of criticalRows) {
    console.error(`- ${row.route_file} ${row.method} ${row.path}: ${row.critical_gaps.join(", ")}`);
  }
  process.exit(1);
}

if (warningRows.length > 0) {
  console.error(`Permission guard failed: ${warningRows.length} route(s) without 403 test evidence.`);
  for (const row of warningRows) {
    console.error(`- ${row.route_file} ${row.method} ${row.path}: ${row.warnings.join(", ")}`);
  }
  process.exit(1);
}

console.log(
  `Permission guard passed: ${rows.length} mutating clinical routes, no critical gaps or warnings.`,
);

function inspectRouteFile(path) {
  const basename = path.split("/").at(-1);
  const text = read(path);
  const decorators = [...text.matchAll(/@router\.(post|patch|delete)\(([\s\S]*?)\)\ndef\s+(\w+)\(/g)];
  return decorators
    .map((match) => inspectRoute(path, basename, text, match))
    .filter(Boolean);
}

function inspectRoute(path, basename, text, match) {
  const method = match[1].toUpperCase();
  const decoratorArgs = match[2];
  const functionName = match[3];
  const routePath = decoratorArgs.match(/["']([^"']*)["']/)?.[1] ?? "";
  const routeKey = `${basename} ${method} ${routePath}`;
  if (readLikePosts.has(routeKey)) {
    return null;
  }
  const body = functionBody(text, functionName);
  const actor_or_access_dep = actorOrAccessDep(body);
  const audit = auditEvidence(body);
  const testEvidence = permissionTestEvidence(basename, routePath);
  const critical_gaps = [];
  const warnings = [];

  if (!actor_or_access_dep) {
    critical_gaps.push("NO_ACTOR_OR_ACCESS_DEP");
  }
  if (!audit) {
    critical_gaps.push("NO_AUDIT_EVENT");
  }
  if (!testEvidence.has_forbidden_test) {
    warnings.push("NO_403_TEST_DETECTED");
  }

  return {
    route_file: relative(root, join(root, path)),
    function_name: functionName,
    method,
    path: routePath,
    actor_or_access_dep: actor_or_access_dep || "no detectado",
    audit: audit || "no detectada",
    forbidden_test: testEvidence.files.join(", ") || "no detectado",
    critical_gaps,
    warnings,
  };
}

function actorOrAccessDep(body) {
  const dep = body.match(/\b(\w+(?:ActorDep|AccessDep))\b/);
  if (dep) {
    return dep[1];
  }
  const user = body.match(/\buser:\s*(AiAccessDep|ReadAccessDep)\b/);
  if (user) {
    return user[1];
  }
  return "";
}

function auditEvidence(body) {
  if (body.includes("record_audit_event(")) {
    return "record_audit_event";
  }
  const delegated = delegatedAuditMarkers.find((marker) => body.includes(marker));
  return delegated ? `delegated:${delegated.replace("(", "")}` : "";
}

function permissionTestEvidence(routeFile, routePath) {
  const basename = routeFile.split("/").at(-1);
  const candidates = forbiddenTestFilesByRoute[basename] ?? [];
  const files = [];
  for (const path of testFiles.filter((testPath) => candidates.includes(testPath))) {
    const text = read(path);
    if (!text.includes("403")) {
      continue;
    }
    if (hasRouteSpecificForbiddenEvidence(text, basename, routePath)) {
      files.push(relative(root, join(root, path)));
    }
  }
  return { has_forbidden_test: files.length > 0, files };
}

function hasRouteSpecificForbiddenEvidence(text, routeFile, routePath) {
  if (routeFile === "patient_core.py" && routePath === "") {
    return text.includes('client.post(\n        "/api/v1/patients"') && text.includes("403");
  }
  if (routeFile === "patient_core.py" && routePath === "/{patient_id}") {
    return text.includes("client.patch(") && text.includes('f"/api/v1/patients/{patient_id}"') && text.includes("403");
  }
  const routeSegments = routePath.split("/").filter((segment) => segment && !segment.startsWith("{"));
  return routeSegments.some((segment) => text.includes(segment)) && text.includes("403");
}

function functionBody(text, name) {
  const match = text.match(new RegExp(`def ${name}\\([\\s\\S]*?(?=\\n@router\\.|\\ndef |$)`));
  return match?.[0] ?? "";
}

function readTree(dir, extensions) {
  const fullDir = join(root, dir);
  if (!existsSync(fullDir)) {
    return [];
  }
  const results = [];
  for (const item of readdirSync(fullDir)) {
    const fullPath = join(fullDir, item);
    const relativePath = relative(root, fullPath);
    if (statSync(fullPath).isDirectory()) {
      results.push(...readTree(relativePath, extensions));
    } else if (extensions.some((extension) => item.endsWith(extension))) {
      results.push(relativePath);
    }
  }
  return results.sort();
}

function renderMarkdown(data) {
  const lines = [
    "# Permissions Map - OneEpis",
    "",
    `Generado: ${data.generated_at}`,
    "",
    "## Resumen",
    "",
    `- Rutas mutantes clinicas revisadas: ${data.summary.routes_checked}`,
    `- Brechas criticas: ${data.summary.critical_gaps}`,
    `- Advertencias: ${data.summary.warnings}`,
    "",
    "## Matriz",
    "",
    "Ruta | Funcion | Actor/permiso | Auditoria | Test 403 | Brechas criticas | Advertencias",
    "--- | --- | --- | --- | --- | --- | ---",
    ...data.rows.map((row) =>
      [
        `${row.method} ${row.path} (${row.route_file})`,
        row.function_name,
        row.actor_or_access_dep,
        row.audit,
        compact(row.forbidden_test),
        row.critical_gaps.join(", ") || "OK",
        row.warnings.join(", ") || "OK",
      ]
        .map(markdownCell)
        .join(" | "),
    ),
  ];
  return `${lines.join("\n")}\n`;
}

function compact(value, limit = 3) {
  const items = String(value)
    .split(", ")
    .filter(Boolean);
  if (items.length <= limit) {
    return value;
  }
  return `${items.slice(0, limit).join(", ")} (+${items.length - limit} mas)`;
}

function read(path) {
  return readFileSync(join(root, path), "utf8");
}

function write(path, content) {
  const target = join(root, path);
  mkdirSync(dirname(target), { recursive: true });
  writeFileSync(target, content);
}

function markdownCell(value) {
  return String(value).replaceAll("\n", " ").replaceAll("|", "\\|");
}
