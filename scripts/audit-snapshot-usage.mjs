#!/usr/bin/env node
import { existsSync, mkdirSync, readdirSync, readFileSync, statSync, writeFileSync } from "node:fs";
import { dirname, join, relative } from "node:path";

const root = process.cwd();
const apiFiles = [
  "apps/web/src/lib/api/patients.ts",
  "apps/web/src/lib/api/clinical-record.ts",
  "apps/web/src/lib/api/hospitalization.ts",
];
const consumerDirs = [
  "apps/web/src/app",
  "apps/web/src/components/clinical",
  "apps/web/src/components/print",
];
const consumers = consumerDirs.flatMap((dir) => readTree(dir, [".ts", ".tsx"]));
const readModels = apiFiles.flatMap(readModelsFromFile);
const rows = readModels.map((model) => ({
  ...model,
  consumers: findConsumers(model.function_name),
  role: classify(model),
}));
const report = {
  generated_at: new Date().toISOString(),
  scope: "frontend_snapshot_usage",
  summary: {
    read_models: rows.length,
    snapshot_or_projection_models: rows.filter((row) => row.role !== "entity-list").length,
    unused_read_models: rows.filter((row) => row.consumers.length === 0).length,
  },
  rows,
};

write("reports/snapshot-usage-map.json", `${JSON.stringify(report, null, 2)}\n`);
write("reports/snapshot-usage-map.md", renderMarkdown(report));

console.log(
  `Snapshot usage map written: ${rows.length} read models, ${report.summary.unused_read_models} unused.`,
);

function readModelsFromFile(path) {
  const text = read(path);
  const matches = [...text.matchAll(/export function (\w+)\([^)]*\)\s*\{\n\s*return apiFetch<([^>]+)>\(([\s\S]*?)\);\n\}/g)];
  return matches
    .map((match) => {
      const body = match[3];
      if (body.includes("method:")) {
        return null;
      }
      const endpoint = endpointFromBody(body);
      if (!endpoint) {
        return null;
      }
      return {
        function_name: match[1],
        return_type: match[2].trim(),
        api_file: path,
        endpoint,
      };
    })
    .filter(Boolean);
}

function endpointFromBody(body) {
  const trimmed = body.trim();
  const backtick = trimmed.match(/`([^`]+)`/);
  if (backtick) {
    return backtick[1].replaceAll("${patientId}", "{patientId}");
  }
  const quoted = trimmed.match(/["']([^"']+)["']/);
  return quoted?.[1] ?? "";
}

function classify(model) {
  if (model.return_type.includes("PatientRecordSnapshot")) {
    return "patient-record-snapshot";
  }
  if (model.return_type.includes("ClinicalTimeline")) {
    return "timeline-projection";
  }
  if (model.return_type.includes("HospitalizationBoardItem")) {
    return "hospitalization-board-projection";
  }
  if (["listHospitalDailySheets", "listHospitalIndications"].includes(model.function_name)) {
    return "hospital-document-list";
  }
  return "entity-list";
}

function findConsumers(functionName) {
  const found = [];
  const pattern = new RegExp(`\\b${escapeRegExp(functionName)}\\b`);
  for (const path of consumers) {
    if (pattern.test(read(path))) {
      found.push(path);
    }
  }
  return found.sort();
}

function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function renderMarkdown(data) {
  const lines = [
    "# Snapshot Usage Map - OneEpis",
    "",
    `Generado: ${data.generated_at}`,
    "",
    "## Resumen",
    "",
    `- Read models frontend: ${data.summary.read_models}`,
    `- Snapshots/proyecciones: ${data.summary.snapshot_or_projection_models}`,
    `- Read models sin consumidor visible: ${data.summary.unused_read_models}`,
    "",
    "## Matriz",
    "",
    "Funcion | Rol | Endpoint | Tipo retorno | Cliente | Consumidores",
    "--- | --- | --- | --- | --- | ---",
    ...data.rows.map((row) =>
      [
        row.function_name,
        row.role,
        row.endpoint,
        row.return_type,
        row.api_file,
        compact(row.consumers),
      ]
        .map(markdownCell)
        .join(" | "),
    ),
  ];
  return `${lines.join("\n")}\n`;
}

function compact(items, limit = 6) {
  if (items.length === 0) {
    return "no detectado";
  }
  if (items.length <= limit) {
    return items.join(", ");
  }
  return `${items.slice(0, limit).join(", ")} (+${items.length - limit} mas)`;
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
