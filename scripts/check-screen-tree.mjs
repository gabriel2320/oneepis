import { readdirSync, readFileSync, statSync } from "node:fs";
import path from "node:path";
import {
  allowedStatuses,
  appRoot,
  duplicates,
  extractRealRouteRows,
  readScreenRegistry,
  routeHeader,
  screenTreePath,
} from "./screen-registry.mjs";

const screenTree = readFileSync(screenTreePath, "utf8");
const registryRows = readScreenRegistry();
const errors = [];

if (!screenTree.includes(routeHeader)) {
  errors.push("docs/SCREEN_TREE.md no tiene la cabecera obligatoria de rutas reales.");
}

const visibleRoutes = discoverVisibleRoutes();
const realRouteRows = extractRealRouteRows(screenTree);
const documentedRoutes = new Set(realRouteRows.map((row) => row.route));
const registryRoutes = new Set(registryRows.map((row) => row.routePattern));
const missingRoutes = visibleRoutes.filter((route) => !documentedRoutes.has(route));

for (const route of duplicates(realRouteRows.map((row) => row.route))) {
  errors.push(`Ruta duplicada en SCREEN_TREE: ${route}`);
}

for (const route of missingRoutes) {
  errors.push(`Ruta visible sin fila en SCREEN_TREE: ${route}`);
}

for (const route of visibleRoutes) {
  if (!registryRoutes.has(route)) {
    errors.push(`Ruta visible sin fila en screen-capabilities.registry.json: ${route}`);
  }
}

for (const route of registryRoutes) {
  if (!visibleRoutes.includes(route)) {
    errors.push(`Ruta registrada sin page.tsx visible: ${route}`);
  }
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
