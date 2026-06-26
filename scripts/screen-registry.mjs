import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

export const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
export const appRoot = path.join(repoRoot, "apps/web/src/app");
export const registryPath = path.join(
  repoRoot,
  "apps/web/src/lib/screen-capabilities.registry.json",
);
export const screenTreePath = path.join(repoRoot, "docs/SCREEN_TREE.md");

export const routeHeader =
  "| Ruta | Modulo | Momento clinico | Estado | Fuente de verdad | Escritura | Permisos | Auditoria | Papel | IA permitida | Pendiente para completar |";

export const allowedStatuses = new Set([
  "completa",
  "completa/en expansion gobernada",
  "preparada",
  "bloqueada",
  "futura",
]);

export const allowedAiProfiles = new Set(["none", "read", "summary", "chart", "validate", "draft", "patch"]);

const requiredStringFields = [
  "routePattern",
  "module",
  "clinicalMoment",
  "status",
  "truthSource",
  "writePolicy",
  "permissionPolicy",
  "auditPolicy",
  "paperPolicy",
  "aiProfile",
  "futureComplexity",
];

export function readScreenRegistry() {
  const rows = JSON.parse(readFileSync(registryPath, "utf8"));
  validateScreenRegistryRows(rows);
  return rows;
}

export function validateScreenRegistryRows(rows) {
  const errors = [];
  if (!Array.isArray(rows)) {
    throw new Error("screen-capabilities.registry.json debe ser un arreglo.");
  }

  rows.forEach((row, index) => {
    for (const field of requiredStringFields) {
      if (typeof row?.[field] !== "string" || row[field].trim() === "") {
        errors.push(`Fila ${index + 1}: campo requerido invalido '${field}'.`);
      }
    }
    if (typeof row?.routePattern === "string" && !row.routePattern.startsWith("/")) {
      errors.push(`Fila ${index + 1}: routePattern debe empezar con '/'.`);
    }
    if (typeof row?.status === "string" && !allowedStatuses.has(row.status)) {
      errors.push(`Fila ${index + 1} (${row.routePattern ?? "sin ruta"}): estado no permitido '${row.status}'.`);
    }
    if (typeof row?.aiProfile === "string" && !allowedAiProfiles.has(row.aiProfile)) {
      errors.push(`Fila ${index + 1} (${row.routePattern ?? "sin ruta"}): aiProfile no permitido '${row.aiProfile}'.`);
    }
  });

  if (errors.length > 0) {
    throw new Error(["Screen registry invalido:", ...errors.map((error) => `- ${error}`)].join("\n"));
  }
}

export function renderRouteTable(rows) {
  return [
    routeHeader,
    "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ...rows.map((row) =>
      [
        code(row.routePattern),
        row.module,
        row.clinicalMoment,
        row.status,
        row.truthSource,
        row.writePolicy,
        row.permissionPolicy,
        row.auditPolicy,
        row.paperPolicy,
        aiProfileLabel(row.aiProfile),
        row.futureComplexity,
      ]
        .map(escapeCell)
        .join(" | "),
    ).map((line) => `| ${line} |`),
  ].join("\n");
}

export function aiProfileLabel(profile) {
  return {
    none: "no",
    read: "lectura contextual",
    summary: "lectura resumida",
    chart: "series",
    validate: "validacion local",
    draft: "borrador revisable",
    patch: "lectura, series, borrador",
  }[profile] ?? profile;
}

export function extractRealRouteRows(markdown) {
  const lines = markdown.split(/\r?\n/);
  const headerIndex = lines.findIndex((line) => line.trim() === routeHeader);
  if (headerIndex === -1) {
    return [];
  }

  const rows = [];
  for (const line of lines.slice(headerIndex + 2)) {
    if (!line.startsWith("|")) {
      break;
    }
    const cells = line
      .split("|")
      .slice(1, -1)
      .map((cell) => cell.trim());
    if (cells.length < 11) {
      continue;
    }
    rows.push({
      route: stripBackticks(cells[0]),
      module: cells[1],
      clinicalMoment: cells[2],
      status: cells[3],
      truthSource: cells[4],
      writePolicy: cells[5],
      permissionPolicy: cells[6],
      auditPolicy: cells[7],
      paperPolicy: cells[8],
      aiPolicy: cells[9],
      pending: cells[10],
    });
  }
  return rows;
}

export function stripBackticks(value) {
  return value.replace(/^`|`$/g, "");
}

export function duplicates(items) {
  const seen = new Set();
  const repeated = new Set();
  for (const item of items) {
    if (seen.has(item)) {
      repeated.add(item);
    }
    seen.add(item);
  }
  return [...repeated].sort();
}

function code(value) {
  return `\`${value}\``;
}

function escapeCell(value) {
  return String(value).replace(/\|/g, "\\|");
}
