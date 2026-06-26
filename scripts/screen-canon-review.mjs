import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const screenTreePath = path.join(repoRoot, "docs/SCREEN_TREE.md");
const capabilitiesPath = path.join(repoRoot, "apps/web/src/lib/screen-capabilities.ts");

const routeHeader =
  "| Ruta | Modulo | Momento clinico | Estado | Fuente de verdad | Escritura | Permisos | Auditoria | Papel | IA permitida | Pendiente para completar |";

const screenTree = readFileSync(screenTreePath, "utf8");
const capabilitiesSource = readFileSync(capabilitiesPath, "utf8");
const routes = extractRouteRows(screenTree);
const capabilities = new Set(extractRegisteredRoutes(capabilitiesSource));
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
  const lines = markdown.split(/\r?\n/);
  const headerIndex = lines.findIndex((line) => line.trim() === routeHeader);
  if (headerIndex === -1) {
    errors.push("No se encontro la tabla de rutas reales en docs/SCREEN_TREE.md.");
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

function extractRegisteredRoutes(source) {
  const routes = [];
  const pattern = /capability\(\s*"([^"]+)"/g;
  let match;
  while ((match = pattern.exec(source)) !== null) {
    routes.push(match[1]);
  }
  return routes;
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

function stripBackticks(value) {
  return value.replace(/^`|`$/g, "");
}

function normalize(value) {
  return value
    .toLowerCase()
    .normalize("NFD")
    .replace(/\p{Diacritic}/gu, "");
}
