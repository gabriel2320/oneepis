import { readdirSync, readFileSync, statSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const appRoot = path.join(repoRoot, "apps/web/src/app");
const screenTreePath = path.join(repoRoot, "docs/SCREEN_TREE.md");

const requiredRouteHeader =
  "| Ruta | Modulo | Momento clinico | Estado | Fuente de verdad | Escritura | Permisos | Auditoria | Papel | IA permitida | Pendiente para completar |";
const allowedStatuses = new Set([
  "completa",
  "completa/en expansion gobernada",
  "preparada",
  "bloqueada",
  "futura",
]);

const screenTree = readFileSync(screenTreePath, "utf8");
const errors = [];

if (!screenTree.includes(requiredRouteHeader)) {
  errors.push("docs/SCREEN_TREE.md no tiene la cabecera obligatoria de rutas reales.");
}

const visibleRoutes = discoverVisibleRoutes();
const realRouteRows = extractRealRouteRows(screenTree);
const documentedRoutes = new Set(realRouteRows.map((row) => row.route));
const missingRoutes = visibleRoutes.filter((route) => !documentedRoutes.has(route));

for (const route of missingRoutes) {
  errors.push(`Ruta visible sin fila en SCREEN_TREE: ${route}`);
}

for (const row of realRouteRows) {
  if (!allowedStatuses.has(row.status)) {
    errors.push(`Estado no permitido en ${row.route}: ${row.status}`);
  }
}

if (errors.length > 0) {
  console.error("Screen tree guard failed.");
  for (const error of errors) {
    console.error(`- ${error}`);
  }
  process.exit(1);
}

console.log(
  `Screen tree guard passed: ${visibleRoutes.length} visible routes documented, ${allowedStatuses.size} statuses allowed.`,
);

function discoverVisibleRoutes() {
  return walk(appRoot)
    .filter((file) => path.basename(file) === "page.tsx")
    .map((file) => {
      const directory = path.dirname(path.relative(appRoot, file));
      if (directory === ".") {
        return "/";
      }
      return `/${directory.split(path.sep).join("/")}`;
    })
    .sort();
}

function walk(root) {
  return readdirSync(root).flatMap((name) => {
    const fullPath = path.join(root, name);
    const stats = statSync(fullPath);
    if (stats.isDirectory()) {
      return walk(fullPath);
    }
    if (!stats.isFile()) {
      return [];
    }
    return [fullPath];
  });
}

function extractRealRouteRows(markdown) {
  const lines = markdown.split(/\r?\n/);
  const headerIndex = lines.findIndex((line) => line.trim() === requiredRouteHeader);
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
      route: cells[0].replace(/^`|`$/g, ""),
      status: cells[3],
    });
  }
  return rows;
}
