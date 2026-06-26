import { readFileSync } from "node:fs";
import {
  extractRealRouteRows,
  readScreenRegistry,
  screenTreePath,
} from "./screen-registry.mjs";

const screenTree = readFileSync(screenTreePath, "utf8");
const routes = extractRouteRows(screenTree);
const capabilities = new Set(readScreenRegistry().map((row) => row.routePattern));
const errors = [];

const phases = [
  phase("01-login", "Login y cuenta", ["Acceso/configuracion"], (route) =>
    ["/", "/login", "/login/recuperar", "/login/desbloquear", "/login/desbloquear/confirmar"].includes(route.route),
  ),
  phase("02-mapa", "Mapa fisico y lugares de trabajo", ["Acceso/configuracion"], (route) =>
    ["/home", "/mapa"].includes(route.route),
  ),
  phase("03-ambulatorio", "Experiencia ambulatoria", ["Ambulatorio"]),
  phase("04-hospitalizacion", "Experiencia hospitalizada", ["Hospitalizacion"]),
  phase("05-ficha", "Ficha tradicional longitudinal", [
    "Nucleo paciente",
    "Episodios",
    "Medicacion/vademecum",
    "Ordenes/resultados",
    "Seguridad/auditoria",
  ]),
  phase("06-documentos", "Documentos y papel", ["Documentos/papel"]),
  phase("07-ia-config", "IA contextual y configuracion", ["IA clinica"], (route) =>
    route.module === "IA clinica" || route.route.startsWith("/configuracion"),
  ),
];

validateRoutes(routes, capabilities, errors);
validateCanonInvariants(routes, errors);

if (errors.length > 0) {
  console.error("Screen canon review failed.");
  for (const error of errors) {
    console.error(`- ${error}`);
  }
  process.exit(1);
}

printReviewQueue(routes, phases);

function phase(id, label, modules, filter = null) {
  return { id, label, modules, filter };
}

function extractRouteRows(markdown) {
  const rows = extractRealRouteRows(markdown);
  if (rows.length === 0) {
    errors.push("No se encontro la tabla de rutas reales en docs/SCREEN_TREE.md.");
  }
  return rows;
}

function validateRoutes(routes, capabilities, errors) {
  for (const route of routes) {
    const emptyFields = Object.entries(route)
      .filter(([, value]) => value.length === 0)
      .map(([key]) => key);
    if (emptyFields.length > 0) {
      errors.push(`${route.route} tiene campos vacios: ${emptyFields.join(", ")}`);
    }
    if (!capabilities.has(route.route)) {
      errors.push(`${route.route} no tiene ScreenCapability registrado.`);
    }
  }
}

function validateCanonInvariants(routes, errors) {
  const byRoute = new Map(routes.map((route) => [route.route, route]));
  expectIncludes(byRoute, "/login", "permissionPolicy", "publico/control UI", errors);
  expectIncludes(byRoute, "/login", "aiPolicy", "no", errors);
  expectIncludes(byRoute, "/home", "truthSource", "mapa fisico", errors);
  expectIncludes(byRoute, "/home", "pending", "lugares fisicos", errors);

  for (const route of routes) {
    if (route.route.startsWith("/print/") && route.paperPolicy === "no") {
      errors.push(`${route.route} es ruta print pero declara papel=no.`);
    }
    if (route.status === "bloqueada" && route.writePolicy === "si") {
      errors.push(`${route.route} esta bloqueada pero declara escritura activa.`);
    }
    if (route.module === "IA clinica" && route.auditPolicy === "si si confirma") {
      continue;
    }
    if (route.writePolicy === "si" && route.auditPolicy === "no") {
      errors.push(`${route.route} escribe pero no declara auditoria.`);
    }
  }
}

function expectIncludes(byRoute, route, key, expected, errors) {
  const row = byRoute.get(route);
  if (!row) {
    errors.push(`Falta ruta canonica ${route}.`);
    return;
  }
  if (!normalize(row[key]).includes(normalize(expected))) {
    errors.push(`${route} debe incluir "${expected}" en ${key}; actual: "${row[key]}".`);
  }
}

function printReviewQueue(routes, phases) {
  console.log("Screen canon review passed.");
  console.log("");
  console.log("Review queue:");
  const assigned = new Set();
  for (const item of phases) {
    const rows = routes.filter((route) => {
      if (item.filter) {
        return item.filter(route);
      }
      return item.modules.includes(route.module);
    });
    if (rows.length === 0) {
      continue;
    }
    console.log(`\n${item.id} ${item.label}`);
    for (const row of rows) {
      assigned.add(row.route);
      console.log(
        `- ${row.route} | ${row.status} | ${row.module} | ${row.clinicalMoment} | pendiente: ${row.pending}`,
      );
    }
  }

  const unassigned = routes.filter((route) => !assigned.has(route.route));
  if (unassigned.length > 0) {
    console.log("\n99-sin-fase Rutas documentadas sin fase canonica");
    for (const row of unassigned) {
      console.log(`- ${row.route} | ${row.status} | ${row.module}`);
    }
  }
}

function normalize(value) {
  return value
    .toLowerCase()
    .normalize("NFD")
    .replace(/\p{Diacritic}/gu, "");
}
