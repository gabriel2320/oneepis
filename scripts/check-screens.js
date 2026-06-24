#!/usr/bin/env node
const { existsSync, readdirSync, readFileSync, statSync } = require("node:fs");
const { join, relative, sep } = require("node:path");

const root = process.cwd();
const screenTreePath = join(root, "docs", "SCREEN_TREE.md");
const appRoot = join(root, "apps", "web", "src", "app");
const capabilitiesPath = join(root, "apps", "web", "src", "lib", "screen-capabilities.ts");

function read(path) {
  return readFileSync(path, "utf8");
}

function uniqueSorted(values) {
  return [...new Set(values)].sort();
}

function parseDeclaredRoutes() {
  const markdown = read(screenTreePath);
  const routes = [];
  for (const match of markdown.matchAll(/```text\n([\s\S]*?)\n```/g)) {
    for (const rawLine of match[1].split("\n")) {
      const line = rawLine.trim();
      if (!line || line.startsWith("->")) {
        continue;
      }
      const route = line.includes("->") ? line.split("->")[0].trim() : line;
      if (route.startsWith("/")) {
        routes.push(route);
      }
    }
  }
  return uniqueSorted(routes);
}

function walk(dir) {
  const files = [];
  for (const item of readdirSync(dir)) {
    const path = join(dir, item);
    if (statSync(path).isDirectory()) {
      files.push(...walk(path));
    } else {
      files.push(path);
    }
  }
  return files;
}

function routeFromPage(path) {
  const rel = relative(appRoot, path).split(sep);
  const segments = rel.slice(0, -1);
  return segments.length === 0 ? "/" : `/${segments.join("/")}`;
}

function parseImplementedRoutes() {
  return uniqueSorted(walk(appRoot).filter((path) => path.endsWith(`${sep}page.tsx`)).map(routeFromPage));
}

function parseArrayField(body, name) {
  const match = body.match(new RegExp(`${name}:\\s*\\[([\\s\\S]*?)\\]`));
  if (!match) {
    return [];
  }
  return [...match[1].matchAll(/"([^"]+)"/g)].map((item) => item[1]);
}

function parseStringField(body, name) {
  const match = body.match(new RegExp(`${name}:\\s*"([^"]+)"`));
  return match ? match[1] : null;
}

function parseCapabilities() {
  const source = read(capabilitiesPath);
  const objectMatches = [...source.matchAll(/\{\n([\s\S]*?)\n  \}/g)];
  return objectMatches
    .map((match) => {
      const body = match[1];
      const route = parseStringField(body, "route");
      if (!route) {
        return null;
      }
      return {
        route,
        lifecycle: parseStringField(body, "lifecycle"),
        writePolicy: parseStringField(body, "writePolicy"),
        paperPolicy: parseStringField(body, "paperPolicy"),
        printRoute: parseStringField(body, "printRoute"),
        apiTestEvidence: parseArrayField(body, "apiTestEvidence"),
        blockExpectation: parseArrayField(body, "blockExpectation"),
      };
    })
    .filter(Boolean);
}

function diff(left, right) {
  const rightSet = new Set(right);
  return left.filter((item) => !rightSet.has(item));
}

function fail(errors) {
  if (errors.length === 0) {
    return;
  }
  console.error("Screen check failed:");
  for (const error of errors) {
    console.error(`- ${error}`);
  }
  process.exit(1);
}

const declared = parseDeclaredRoutes();
const implemented = parseImplementedRoutes();
const capabilities = parseCapabilities();
const capabilityRoutes = uniqueSorted(capabilities.map((capability) => capability.route));
const implementedSet = new Set(implemented);
const errors = [];

for (const route of diff(declared, implemented)) {
  errors.push(`Declared route is not implemented: ${route}`);
}
for (const route of diff(implemented, declared)) {
  errors.push(`Implemented route is not declared in SCREEN_TREE: ${route}`);
}
for (const route of diff(declared, capabilityRoutes)) {
  errors.push(`Declared route has no ScreenCapability: ${route}`);
}
for (const route of diff(capabilityRoutes, declared)) {
  errors.push(`ScreenCapability route is not declared in SCREEN_TREE: ${route}`);
}

for (const route of capabilityRoutes) {
  if (capabilityRoutes.indexOf(route) !== capabilityRoutes.lastIndexOf(route)) {
    errors.push(`Duplicate ScreenCapability route: ${route}`);
  }
}

for (const capability of capabilities) {
  if (capability.paperPolicy === "carta" && capability.printRoute && !implementedSet.has(capability.printRoute)) {
    errors.push(`paperPolicy=carta printRoute does not exist for ${capability.route}: ${capability.printRoute}`);
  }
  if (capability.writePolicy === "existing-api") {
    if (capability.apiTestEvidence.length === 0) {
      errors.push(`writePolicy=existing-api needs apiTestEvidence: ${capability.route}`);
    }
    for (const evidence of capability.apiTestEvidence) {
      if (!existsSync(join(root, evidence))) {
        errors.push(`apiTestEvidence does not exist for ${capability.route}: ${evidence}`);
      }
    }
  }
  if (capability.lifecycle === "blocked" && capability.blockExpectation.length === 0) {
    errors.push(`blocked lifecycle needs blockExpectation: ${capability.route}`);
  }
}

fail(errors);

console.log(
  `Screen check passed: ${declared.length} declared, ${implemented.length} implemented, ${capabilities.length} capabilities.`,
);
