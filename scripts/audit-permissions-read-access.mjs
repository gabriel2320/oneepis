import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const apiDepsPath = path.join(repoRoot, "apps/api/src/oneepis_api/api/deps.py");
const webPermissionsPath = path.join(repoRoot, "apps/web/src/lib/permissions.ts");
const screenTreePath = path.join(repoRoot, "docs/SCREEN_TREE.md");

const apiDeps = readFileSync(apiDepsPath, "utf8");
const webPermissions = readFileSync(webPermissionsPath, "utf8");
const screenRows = extractScreenRows(readFileSync(screenTreePath, "utf8"));
const apiRequirements = extractApiRoleRequirements(apiDeps);
const webRoleSets = extractWebRoleSets(webPermissions);
const warnings = [];

for (const row of screenRows) {
  if (row.escritura === "si" && (row.permisos === "no" || row.auditoria === "no")) {
    warnings.push(`${row.route}: escritura visible sin permisos/auditoria declarados.`);
  }
  if (hasClinicalAiPermissionGap(row)) {
    warnings.push(`${row.route}: IA declarada sin permiso clinico explicito.`);
  }
}

console.log("# Audit: Permisos y Acceso de Lectura");
console.log("");
console.log("Reporte informativo; gaps se reportan como warnings no bloqueantes.");
console.log("");
console.log("## Backend");
console.log("");
for (const requirement of apiRequirements) {
  console.log(`- ${requirement.name}: ${requirement.roles.join(", ")}`);
}
console.log("");
console.log("## Frontend");
console.log("");
for (const roleSet of webRoleSets) {
  console.log(`- ${roleSet.name}: ${roleSet.roles.join(", ")}`);
}
console.log("");
console.log("## SCREEN_TREE");
console.log("");
console.log(`- Rutas documentadas: ${screenRows.length}`);
console.log(`- Rutas con escritura: ${screenRows.filter((row) => row.escritura === "si").length}`);
console.log(`- Rutas con IA declarada: ${screenRows.filter((row) => row.ia !== "no" && row.ia !== "none").length}`);
console.log("");
console.log("## Warnings");
console.log("");
if (warnings.length === 0) {
  console.log("- Sin warnings estructurales detectados.");
} else {
  for (const warning of warnings) {
    console.log(`- ${warning}`);
  }
}

function extractApiRoleRequirements(source) {
  const requirements = [];
  const pattern = /def\s+(require_[a-z_]+)\([^)]*\).*?return\s+require_roles\(([^)]*)\)\(user\)/gs;
  let match;
  while ((match = pattern.exec(source)) !== null) {
    if (match[1] === "require_roles") {
      continue;
    }
    requirements.push({
      name: match[1],
      roles: extractUserRoles(match[2]),
    });
  }
  return requirements.sort((a, b) => a.name.localeCompare(b.name));
}

function extractWebRoleSets(source) {
  const roleSets = [];
  const pattern = /const\s+([a-zA-Z0-9]+):\s*UserRole\[\]\s*=\s*\[([^\]]*)\]/g;
  let match;
  while ((match = pattern.exec(source)) !== null) {
    roleSets.push({
      name: match[1],
      roles: match[2]
        .split(",")
        .map((value) => value.replace(/["\s]/g, ""))
        .filter(Boolean),
    });
  }
  return roleSets.sort((a, b) => a.name.localeCompare(b.name));
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
      rows.push({
        route: cells[0].replace(/^`|`$/g, ""),
        escritura: cells[5],
        permisos: cells[6],
        auditoria: cells[7],
        ia: cells[9],
      });
    }
  }
  return rows;
}

function extractUserRoles(value) {
  const roles = [];
  const pattern = /UserRole\.([A-Z_]+)/g;
  let match;
  while ((match = pattern.exec(value)) !== null) {
    roles.push(match[1].toLowerCase());
  }
  return roles;
}

function hasClinicalAiPermissionGap(row) {
  if (row.ia === "no" || row.ia === "none") {
    return false;
  }
  if (/lectura|estado|config|sugeridos deterministas|no generativa|series|resumen no persistido/i.test(row.ia)) {
    return false;
  }
  if (/permiso IA|medico|admin|dev/i.test(row.permisos)) {
    return false;
  }
  return true;
}
