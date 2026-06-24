#!/usr/bin/env node
import { existsSync, mkdirSync, readdirSync, readFileSync, statSync, writeFileSync } from "node:fs";
import { dirname, join, relative, sep } from "node:path";

const root = process.cwd();
const appRoot = join(root, "apps", "web", "src", "app");
const capabilitiesPath = join(root, "apps", "web", "src", "lib", "screen-capabilities.ts");

const capabilities = parseCapabilities();
const implementedRoutes = new Set(parseImplementedRoutes());
const byRoute = new Map(capabilities.map((capability) => [capability.route, capability]));
const printRows = capabilities.filter(
  (capability) => capability.screenKind === "print" && capability.paperPolicy === "carta",
);
const appPaperRows = capabilities.filter(
  (capability) => capability.screenKind === "app" && capability.paperPolicy === "carta",
);
const rows = printRows.map(inspectPrintRoute);

for (const capability of appPaperRows) {
  if (!capability.printRoute) {
    rows.push({
      route: capability.route,
      linked_app_route: capability.route,
      owner_entity: "no declarado",
      read_model: "no declarado",
      api_client: "no declarado",
      document_state: "no declarado",
      clinical_use: "no declarado",
      gaps: ["APP_PAPER_WITHOUT_PRINT_ROUTE"],
    });
    continue;
  }
  const printCapability = byRoute.get(capability.printRoute);
  if (!printCapability) {
    rows.push({
      route: capability.printRoute,
      linked_app_route: capability.route,
      owner_entity: "no declarado",
      read_model: "no declarado",
      api_client: "no declarado",
      document_state: "no declarado",
      clinical_use: "no declarado",
      gaps: ["PRINT_ROUTE_WITHOUT_CAPABILITY"],
    });
  }
}

const failedRows = rows.filter((row) => row.gaps.length > 0);
const report = {
  generated_at: new Date().toISOString(),
  scope: "paper_source_policy",
  summary: {
    print_routes_checked: printRows.length,
    app_routes_with_paper_policy: appPaperRows.length,
    gaps: failedRows.length,
  },
  rows,
};

write("reports/paper-source-map.json", `${JSON.stringify(report, null, 2)}\n`);
write("reports/paper-source-map.md", renderMarkdown(report));

if (failedRows.length > 0) {
  console.error(`Paper source check failed: ${failedRows.length} route gap(s).`);
  for (const row of failedRows) {
    console.error(`- ${row.route}: ${row.gaps.join(", ")}`);
  }
  process.exit(1);
}

console.log(
  `Paper source check passed: ${printRows.length} print routes, ${appPaperRows.length} app paper routes.`,
);

function inspectPrintRoute(capability) {
  const gaps = [];
  if (!implementedRoutes.has(capability.route)) {
    gaps.push("PRINT_ROUTE_NOT_IMPLEMENTED");
  }
  for (const field of [
    "printOwnerEntity",
    "printReadModel",
    "printApiClient",
    "printDocumentState",
    "printClinicalUse",
  ]) {
    if (!capability[field]) {
      gaps.push(`MISSING_${field.replace("print", "").toUpperCase()}`);
    }
  }
  if (
    capability.printClinicalUse &&
    !["development-only", "blocked"].includes(capability.printClinicalUse)
  ) {
    gaps.push("INVALID_CLINICAL_USE");
  }
  if (capability.lifecycle === "blocked" && capability.printClinicalUse !== "blocked") {
    gaps.push("BLOCKED_PRINT_NEEDS_BLOCKED_CLINICAL_USE");
  }

  return {
    route: capability.route,
    linked_app_route: linkedAppRoutes(capability.route).join(", ") || "sin ruta app vinculada",
    owner_entity: capability.printOwnerEntity || "no declarado",
    read_model: capability.printReadModel || "no declarado",
    api_client: capability.printApiClient || "no declarado",
    document_state: capability.printDocumentState || "no declarado",
    clinical_use: capability.printClinicalUse || "no declarado",
    gaps,
  };
}

function linkedAppRoutes(printRoute) {
  return appPaperRows
    .filter((capability) => capability.printRoute === printRoute)
    .map((capability) => capability.route)
    .sort();
}

function parseImplementedRoutes() {
  return uniqueSorted(walk(appRoot).filter((path) => path.endsWith(`${sep}page.tsx`)).map(routeFromPage));
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
        screenKind: parseStringField(body, "screenKind"),
        paperPolicy: parseStringField(body, "paperPolicy"),
        printRoute: parseStringField(body, "printRoute"),
        printOwnerEntity: parseStringField(body, "printOwnerEntity"),
        printReadModel: parseStringField(body, "printReadModel"),
        printApiClient: parseStringField(body, "printApiClient"),
        printDocumentState: parseStringField(body, "printDocumentState"),
        printClinicalUse: parseStringField(body, "printClinicalUse"),
      };
    })
    .filter(Boolean);
}

function parseStringField(body, name) {
  const match = body.match(new RegExp(`${name}:\\s*"([^"]+)"`));
  return match ? match[1] : null;
}

function routeFromPage(path) {
  const rel = relative(appRoot, path).split(sep);
  const segments = rel.slice(0, -1);
  return segments.length === 0 ? "/" : `/${segments.join("/")}`;
}

function walk(dir) {
  const files = [];
  for (const item of readDir(dir)) {
    const path = join(dir, item);
    if (statSync(path).isDirectory()) {
      files.push(...walk(path));
    } else {
      files.push(path);
    }
  }
  return files;
}

function renderMarkdown(data) {
  const lines = [
    "# Paper Source Map - OneEpis",
    "",
    `Generado: ${data.generated_at}`,
    "",
    "## Resumen",
    "",
    `- Rutas print revisadas: ${data.summary.print_routes_checked}`,
    `- Rutas app con paperPolicy=carta: ${data.summary.app_routes_with_paper_policy}`,
    `- Brechas: ${data.summary.gaps}`,
    "",
    "## Matriz",
    "",
    "Ruta print | Ruta app vinculada | Entidad duena | Read model | Cliente API | Estado documental | Uso clinico | Brechas",
    "--- | --- | --- | --- | --- | --- | --- | ---",
    ...data.rows.map((row) =>
      [
        row.route,
        row.linked_app_route,
        row.owner_entity,
        row.read_model,
        row.api_client,
        row.document_state,
        row.clinical_use,
        row.gaps.join(", ") || "OK",
      ]
        .map(markdownCell)
        .join(" | "),
    ),
  ];
  return `${lines.join("\n")}\n`;
}

function readDir(dir) {
  return existsSync(dir) ? readdirSync(dir) : [];
}

function read(path) {
  return readFileSync(path, "utf8");
}

function write(path, content) {
  const target = join(root, path);
  mkdirSync(dirname(target), { recursive: true });
  writeFileSync(target, content);
}

function uniqueSorted(values) {
  return [...new Set(values)].sort();
}

function markdownCell(value) {
  return String(value).replaceAll("\n", " ").replaceAll("|", "\\|");
}
