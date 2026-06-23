import { readFileSync, readdirSync, statSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const appRoot = path.join(repoRoot, "apps/web/src/app");
const registryPath = path.join(repoRoot, "apps/web/src/lib/screen-capabilities.ts");

const registry = readFileSync(registryPath, "utf8");
const visibleRoutes = discoverVisibleRoutes();
const registeredRoutes = extractRegisteredRoutes(registry);
const errors = [];

for (const route of visibleRoutes) {
  if (!registeredRoutes.has(route)) {
    errors.push(`Ruta visible sin ScreenCapability: ${route}`);
  }
}

for (const route of registeredRoutes) {
  if (!visibleRoutes.includes(route)) {
    errors.push(`ScreenCapability sin page.tsx visible: ${route}`);
  }
}

if (errors.length > 0) {
  console.error("Screen capability guard failed.");
  for (const error of errors) {
    console.error(`- ${error}`);
  }
  process.exit(1);
}

console.log(`Screen capability guard passed: ${visibleRoutes.length} visible routes registered.`);

function discoverVisibleRoutes() {
  return walk(appRoot)
    .filter((file) => path.basename(file) === "page.tsx")
    .map((file) => {
      const directory = path.dirname(path.relative(appRoot, file));
      return directory === "." ? "/" : `/${directory.split(path.sep).join("/")}`;
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
    return stats.isFile() ? [fullPath] : [];
  });
}

function extractRegisteredRoutes(source) {
  const routes = new Set();
  const pattern = /capability\(\s*"([^"]+)"/g;
  let match;
  while ((match = pattern.exec(source)) !== null) {
    routes.add(match[1]);
  }
  return routes;
}
