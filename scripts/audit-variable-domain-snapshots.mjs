import { readFileSync, readdirSync, statSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const apiSchemaRoot = path.join(repoRoot, "apps/api/src/oneepis_api/schemas/clinical_record_contracts");
const webTypeRoot = path.join(repoRoot, "apps/web/src/lib/type-contracts");
const screenTreePath = path.join(repoRoot, "docs/SCREEN_TREE.md");

const apiSchemaFiles = walk(apiSchemaRoot, ".py");
const webTypeFiles = walk(webTypeRoot, ".ts");
const screenTree = readFileSync(screenTreePath, "utf8");
const screenRows = extractScreenRows(screenTree);

const apiClasses = apiSchemaFiles.flatMap((file) =>
  extractMatches(file, /^class\s+([A-Za-z0-9_]+)/gm),
);
const webExports = webTypeFiles.flatMap((file) =>
  extractMatches(file, /^export\s+type\s+([A-Za-z0-9_]+)/gm),
);
const modules = countBy(screenRows.map((row) => row.module));
const statuses = countBy(screenRows.map((row) => row.status));

console.log("# Audit: Variables, Dominios y Snapshots");
console.log("");
console.log("Reporte reproducible; no bloquea CI.");
console.log("");
console.log("## Resumen");
console.log("");
console.log(`- Schemas API inspeccionados: ${apiSchemaFiles.length}`);
console.log(`- Clases API detectadas: ${apiClasses.length}`);
console.log(`- Contratos TS inspeccionados: ${webTypeFiles.length}`);
console.log(`- Tipos TS exportados: ${webExports.length}`);
console.log(`- Rutas reales documentadas: ${screenRows.length}`);
console.log("");
console.log("## Modulos En SCREEN_TREE");
console.log("");
printCounts(modules);
console.log("");
console.log("## Estados En SCREEN_TREE");
console.log("");
printCounts(statuses);

function walk(root, extension) {
  return readdirSync(root).flatMap((name) => {
    const fullPath = path.join(root, name);
    const stats = statSync(fullPath);
    if (stats.isDirectory()) {
      return walk(fullPath, extension);
    }
    return stats.isFile() && fullPath.endsWith(extension) ? [fullPath] : [];
  });
}

function extractMatches(file, pattern) {
  const source = readFileSync(file, "utf8");
  const matches = [];
  let match;
  while ((match = pattern.exec(source)) !== null) {
    matches.push({ file: toRepoPath(file), name: match[1] });
  }
  return matches;
}

function extractScreenRows(markdown) {
  const header =
    "| Ruta | Modulo | Momento clinico | Estado | Fuente de verdad | Escritura | Permisos | Auditoria | Papel | IA permitida | Pendiente para completar |";
  const lines = markdown.split(/\r?\n/);
  const headerIndex = lines.findIndex((line) => line.trim() === header);
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
    if (cells.length >= 11) {
      rows.push({ route: cells[0], module: cells[1], status: cells[3] });
    }
  }
  return rows;
}

function countBy(items) {
  const counts = new Map();
  for (const item of items) {
    counts.set(item, (counts.get(item) ?? 0) + 1);
  }
  return [...counts.entries()].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
}

function printCounts(counts) {
  for (const [label, count] of counts) {
    console.log(`- ${label}: ${count}`);
  }
}

function toRepoPath(file) {
  return path.relative(repoRoot, file).split(path.sep).join("/");
}
