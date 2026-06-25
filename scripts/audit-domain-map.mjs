#!/usr/bin/env node
import { existsSync, mkdirSync, readdirSync, readFileSync, statSync, writeFileSync } from "node:fs";
import { dirname, join, relative } from "node:path";

const root = process.cwd();
const traceabilityPath = "reports/traceability-map.json";

if (!existsSync(join(root, traceabilityPath))) {
  throw new Error("Missing reports/traceability-map.json. Run npm run audit:traceability first.");
}

const traceability = JSON.parse(readFileSync(join(root, traceabilityPath), "utf8"));
const apiTestFiles = readTree("apps/api/tests", [".py"]).filter(
  (path) => !path.endsWith("conftest.py") && !path.includes("helpers"),
);
const e2eTestFiles = readTree("apps/web/tests/e2e", [".ts"]);
const allTestFiles = [...apiTestFiles, ...e2eTestFiles];

const domainHints = {
  Patient: ["patient", "patients", "pacientes", "Patient"],
  ClinicalEncounter: ["encounter", "encounters", "encuentro", "encuentros"],
  ClinicalEntry: ["clinical_entry", "clinical-entries", "entry", "evolucion", "evoluciones"],
  ClinicalEvent: ["clinical_event", "clinical-events", "event", "evento", "timeline"],
  VitalSign: ["vital", "vital-signs", "signos"],
  Allergy: ["allergy", "allergies", "alerg"],
  Medication: ["medication", "medications", "medicacion"],
  ActiveProblem: ["problem", "problems", "problema"],
  LabResult: ["lab", "laboratorio", "exam", "LAB_RESULT", "EXAM_RESULT"],
  ClinicalRisk: ["risk", "riesgo"],
  AuditEvent: ["audit", "audit-events", "auditoria"],
};

const rows = traceability.rows.map((row) => {
  const tests = findTests(row.dominio);
  const gaps = classifyGaps(row, tests);
  return {
    dominio: row.dominio,
    modelo_sqlalchemy: row.modelo_sqlalchemy,
    tabla_duena: row.tabla_duena,
    schema_pydantic: row.schema_pydantic,
    endpoint_fastapi: endpoints(row),
    repositorio_servicio: repositoryOrService(row),
    openapi_path: openApiPathHint(row),
    tipo_ts: row.tipo_frontend,
    cliente_frontend: row.cliente_frontend,
    pantalla: row.pantalla,
    ruta_papel: row.papel,
    permisos: permissionLabel(row),
    auditoria: row.auditoria,
    tests_existentes: tests.join(", ") || "no detectado",
    gaps,
    estado: gaps.length === 0 ? "OK" : gaps.includes("NO_OWNER_TABLE") ? "BLOCKED_DOMAIN" : gaps[0],
    recomendacion: row.recomendacion,
  };
});

const report = {
  generated_at: new Date().toISOString(),
  scope: "clinical_domain_map",
  source_report: traceabilityPath,
  rows,
  summary: summarize(rows),
};

write("reports/domain-map.json", `${JSON.stringify(report, null, 2)}\n`);
write("reports/domain-map.md", renderMarkdown(report));

console.log(
  `Domain map written: ${rows.length} domains, ${Object.entries(report.summary.states)
    .map(([state, count]) => `${state}=${count}`)
    .join(", ")}`,
);

function endpoints(row) {
  return [row.endpoints_creacion, row.endpoints_lectura, row.endpoints_actualizacion]
    .filter((value) => value && value !== "no detectado")
    .join(" | ") || "no detectado";
}

function repositoryOrService(row) {
  if (row.dominio === "Patient") {
    return "apps/api/src/oneepis_api/repositories/patients.py";
  }
  if (["ClinicalEntry", "ClinicalEvent", "LabResult"].includes(row.dominio)) {
    return "apps/api/src/oneepis_api/services/clinical_context.py, apps/api/src/oneepis_api/services/clinical_intent.py";
  }
  if (row.dominio === "AuditEvent") {
    return "apps/api/src/oneepis_api/services/audit.py";
  }
  return "no detectado";
}

function openApiPathHint(row) {
  const endpoints = [
    row.endpoints_creacion,
    row.endpoints_lectura,
    row.endpoints_actualizacion,
  ].join(" ");
  const matches = [...endpoints.matchAll(/\b(?:GET|POST|PATCH|DELETE|PUT) ([^ ]+)/g)]
    .map((match) => match[1])
    .filter((route) => route !== "no");
  return unique(matches).join(", ") || "no detectado";
}

function permissionLabel(row) {
  if (row.actor_id !== "no detectado") {
    return row.actor_id;
  }
  if (row.endpoints_creacion !== "no detectado" || row.endpoints_actualizacion !== "no detectado") {
    return "PERMISSION_REVIEW_REQUIRED";
  }
  return "no aplica en primera pasada";
}

function classifyGaps(row, tests) {
  const gaps = [];
  if (row.tabla_duena === "sin tabla duena dedicada") {
    gaps.push("NO_OWNER_TABLE");
  }
  if (row.modelo_sqlalchemy === "no encontrado") {
    gaps.push("NO_MODEL");
  }
  if (row.schema_pydantic === "no detectado") {
    gaps.push("NO_SCHEMA");
  }
  if (row.tipo_frontend === "no detectado") {
    gaps.push("NO_TS_TYPE");
  }
  if (row.cliente_frontend === "no detectado" && hasReadableEndpoint(row)) {
    gaps.push("NO_CLIENT");
  }
  if (row.pantalla === "no detectada" && row.dominio !== "AuditEvent") {
    gaps.push("NO_SCREEN");
  }
  if (row.papel === "no detectado" && shouldHavePaper(row)) {
    gaps.push("NO_PRINT_SOURCE");
  }
  if (row.auditoria === "no detectada" && hasWritableEndpoint(row)) {
    gaps.push("NO_AUDIT");
  }
  if (tests.length === 0) {
    gaps.push("NO_TEST");
  }
  return gaps;
}

function hasReadableEndpoint(row) {
  return row.endpoints_lectura !== "no detectado";
}

function hasWritableEndpoint(row) {
  return row.endpoints_creacion !== "no detectado" || row.endpoints_actualizacion !== "no detectado";
}

function shouldHavePaper(row) {
  return ["Patient", "ClinicalEntry", "ClinicalEvent", "VitalSign", "Medication", "ActiveProblem"].includes(
    row.dominio,
  );
}

function findTests(domain) {
  const hints = domainHints[domain] ?? [domain];
  const matches = [];
  for (const path of allTestFiles) {
    const text = readFileSync(join(root, path), "utf8");
    if (hints.some((hint) => path.toLowerCase().includes(hint.toLowerCase()) || text.includes(hint))) {
      matches.push(path);
    }
  }
  return unique(matches.map((path) => relative(root, join(root, path))));
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

function summarize(items) {
  const states = {};
  for (const item of items) {
    states[item.estado] = (states[item.estado] ?? 0) + 1;
  }
  return {
    total: items.length,
    states,
    gaps: items.flatMap((item) => item.gaps.map((gap) => `${item.dominio}: ${gap}`)),
  };
}

function renderMarkdown(data) {
  const lines = [
    "# Domain Map - OneEpis",
    "",
    `Generado: ${data.generated_at}`,
    "",
    `Fuente: ${data.source_report}`,
    "",
    "## Resumen",
    "",
    `- Dominios auditados: ${data.summary.total}`,
    ...Object.entries(data.summary.states).map(([state, count]) => `- ${state}: ${count}`),
    "",
    "## Gaps",
    "",
    ...(data.summary.gaps.length ? data.summary.gaps.map((gap) => `- ${gap}`) : ["- Sin gaps detectados."]),
    "",
    "## Matriz",
    "",
    [
      "Dominio",
      "Tabla",
      "Modelo",
      "Schema",
      "Endpoint",
      "Repo/Service",
      "OpenAPI path",
      "TS",
      "Cliente",
      "Pantalla",
      "Papel",
      "Permisos",
      "Auditoria",
      "Tests",
      "Estado",
      "Recomendacion",
    ].join(" | "),
    [
      "---",
      "---",
      "---",
      "---",
      "---",
      "---",
      "---",
      "---",
      "---",
      "---",
      "---",
      "---",
      "---",
      "---",
      "---",
      "---",
    ].join(" | "),
    ...data.rows.map((row) =>
      [
        row.dominio,
        row.tabla_duena,
        compactList(row.modelo_sqlalchemy, 1),
        compactList(row.schema_pydantic),
        compactList(row.endpoint_fastapi, 3),
        compactList(row.repositorio_servicio, 3),
        compactList(row.openapi_path, 4),
        compactList(row.tipo_ts, 3),
        compactList(row.cliente_frontend, 3),
        compactList(row.pantalla),
        compactList(row.ruta_papel),
        row.permisos,
        compactList(row.auditoria, 4),
        compactList(row.tests_existentes, 4),
        row.estado,
        row.recomendacion,
      ]
        .map(markdownCell)
        .join(" | "),
    ),
  ];
  return `${lines.join("\n")}\n`;
}

function compactList(value, limit = 6) {
  const items = String(value)
    .split(", ")
    .filter(Boolean);
  if (items.length <= limit) {
    return value;
  }
  return `${items.slice(0, limit).join(", ")} (+${items.length - limit} mas)`;
}

function write(path, content) {
  const target = join(root, path);
  mkdirSync(dirname(target), { recursive: true });
  writeFileSync(target, content);
}

function markdownCell(value) {
  return String(value).replaceAll("\n", " ").replaceAll("|", "\\|");
}

function unique(items) {
  return [...new Set(items)].sort();
}
