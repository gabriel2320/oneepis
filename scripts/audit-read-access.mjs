#!/usr/bin/env node
import { existsSync, mkdirSync, readdirSync, readFileSync, statSync, writeFileSync } from "node:fs";
import { dirname, join, relative } from "node:path";

const root = process.cwd();
const routeDir = "apps/api/src/oneepis_api/api/v1/routes";
const routeFiles = readTree(routeDir, [".py"]).filter((path) => !path.endsWith("__init__.py"));
const rows = routeFiles.flatMap(inspectRouteFile);
const sensitiveRows = rows.filter((row) => row.policy === "READ_AUDIT_CANDIDATE");
const report = {
  generated_at: new Date().toISOString(),
  scope: "clinical_read_access_report_only",
  summary: {
    get_routes_checked: rows.length,
    read_audit_candidates: sensitiveRows.length,
    technical_or_session_exemptions: rows.filter((row) => row.policy === "EXEMPT_TECHNICAL").length,
    report_only_gaps: sensitiveRows.filter((row) => row.current_read_audit === "no implementada").length,
  },
  rows,
};

write("reports/read-access-map.json", `${JSON.stringify(report, null, 2)}\n`);
write("reports/read-access-map.md", renderMarkdown(report));

console.log(
  `Read access map written: ${rows.length} GET routes, ${sensitiveRows.length} read audit candidates.`,
);

function inspectRouteFile(path) {
  const basename = path.split("/").at(-1);
  const text = read(path);
  const decorators = [...text.matchAll(/@router\.get\(([\s\S]*?)\)\ndef\s+(\w+)\(/g)];
  return decorators.map((match) => inspectRoute(path, basename, text, match));
}

function inspectRoute(path, basename, text, match) {
  const routePath = match[1].match(/["']([^"']*)["']/)?.[1] ?? "";
  const functionName = match[2];
  const body = functionBody(text, functionName);
  const fullPath = joinApiPath(prefixForFile(basename, text), routePath);
  const classification = classifyReadRoute(basename, fullPath, body);
  const access = accessEvidence(text, body, classification.policy);
  return {
    route_file: relative(root, join(root, path)),
    function_name: functionName,
    method: "GET",
    path: routePath,
    full_path: fullPath,
    policy: classification.policy,
    sensitivity: classification.sensitivity,
    access_dependency: access || "no detectada",
    current_read_audit: classification.policy === "READ_AUDIT_CANDIDATE" ? "no implementada" : "no requerida",
    recommendation: classification.recommendation,
  };
}

function classifyReadRoute(basename, fullPath, body) {
  if (
    basename === "health.py" ||
    fullPath === "/api/v1/ai/status" ||
    fullPath === "/api/v1/auth/me"
  ) {
    return {
      policy: "EXEMPT_TECHNICAL",
      sensitivity: "tecnica_o_sesion",
      recommendation: "Mantener fuera de auditoria clinica de lectura.",
    };
  }

  if (fullPath.includes("/audit-events")) {
    return candidate("audit_trail", "Prioridad alta: lectura de auditoria clinica debe dejar trail.");
  }
  if (fullPath.includes("/record")) {
    return candidate("patient_record", "Prioridad alta: lectura de ficha longitudinal debe auditarse.");
  }
  if (fullPath.includes("/timeline")) {
    return candidate("clinical_timeline", "Auditar como lectura longitudinal sensible.");
  }
  if (fullPath.includes("/hospitalization/patients/")) {
    return candidate("hospital_document", "Auditar como lectura de documento o lista clinica hospitalaria.");
  }
  if (fullPath.includes("/hospitalization/active")) {
    return candidate("hospital_board", "Auditar si expone pacientes hospitalizados; revisar volumen antes de bloquear.");
  }
  if (fullPath.includes("/patients/{patient_id}")) {
    return candidate("patient_child_entity", "Auditar como lectura de entidad clinica asociada a paciente.");
  }
  if (fullPath === "/api/v1/patients" || fullPath.includes("/patients")) {
    return candidate("patient_search_or_identity", "Auditar o muestrear segun volumen: expone identidad/lista de pacientes.");
  }
  if (body.includes("Patient") || body.includes("Clinical") || body.includes("Hospital")) {
    return candidate("clinical_read", "Revisar manualmente; parece lectura clinica por modelo o schema.");
  }

  return {
    policy: "EXEMPT_TECHNICAL",
    sensitivity: "no_clinica_detectada",
    recommendation: "Sin evidencia de lectura clinica sensible en esta pasada.",
  };
}

function candidate(sensitivity, recommendation) {
  return {
    policy: "READ_AUDIT_CANDIDATE",
    sensitivity,
    recommendation,
  };
}

function accessEvidence(text, body, policy) {
  if (body.match(/\b(\w+ReadAccessDep)\b/)) {
    return body.match(/\b(\w+ReadAccessDep)\b/)?.[1] ?? "";
  }
  if (body.match(/\b(AiAccessDep|CurrentUserDep)\b/)) {
    return body.match(/\b(AiAccessDep|CurrentUserDep)\b/)?.[1] ?? "";
  }
  if (text.includes("dependencies=[Depends(require_patient_read_access)]")) {
    return "router:require_patient_read_access";
  }
  if (text.includes("PATIENT_ROUTER_OPTIONS")) {
    return "router:PATIENT_ROUTER_OPTIONS";
  }
  return policy === "EXEMPT_TECHNICAL" ? "no requerida" : "";
}

function prefixForFile(basename, text) {
  const explicitPrefix = text.match(/APIRouter\([\s\S]*?prefix=["']([^"']+)["']/)?.[1];
  if (explicitPrefix) {
    return explicitPrefix;
  }
  if (text.includes("PATIENT_ROUTER_OPTIONS") || basename.startsWith("patient_")) {
    return "/patients";
  }
  return "";
}

function joinApiPath(prefix, routePath) {
  const parts = ["/api/v1", prefix, routePath]
    .map((part) => part.trim())
    .filter(Boolean)
    .map((part) => part.replace(/^\/+|\/+$/g, ""));
  return `/${parts.join("/")}`.replace(/\/+/g, "/");
}

function functionBody(text, name) {
  const match = text.match(new RegExp(`def ${name}\\([\\s\\S]*?(?=\\n@router\\.|\\ndef |$)`));
  return match?.[0] ?? "";
}

function renderMarkdown(data) {
  const lines = [
    "# Read Access Map - OneEpis",
    "",
    `Generado: ${data.generated_at}`,
    "",
    "## Resumen",
    "",
    `- Rutas GET revisadas: ${data.summary.get_routes_checked}`,
    `- Candidatas a auditoria de lectura: ${data.summary.read_audit_candidates}`,
    `- Exenciones tecnicas/sesion: ${data.summary.technical_or_session_exemptions}`,
    `- Brechas report-only: ${data.summary.report_only_gaps}`,
    "",
    "## Politica",
    "",
    "Este reporte no bloquea CI. C5-01 solo clasifica rutas de lectura sensibles para disenar auditoria de acceso antes de escribir eventos nuevos.",
    "",
    "## Matriz",
    "",
    "Ruta | Funcion | Politica | Sensibilidad | Acceso | Auditoria lectura actual | Recomendacion",
    "--- | --- | --- | --- | --- | --- | ---",
    ...data.rows.map((row) =>
      [
        `${row.method} ${row.full_path} (${row.route_file})`,
        row.function_name,
        row.policy,
        row.sensitivity,
        row.access_dependency,
        row.current_read_audit,
        row.recommendation,
      ]
        .map(markdownCell)
        .join(" | "),
    ),
  ];
  return `${lines.join("\n")}\n`;
}

function readTree(dir, extensions) {
  const fullDir = join(root, dir);
  if (!existsSync(fullDir)) {
    return [];
  }
  const results = [];
  for (const item of readdirSync(fullDir)) {
    const fullPath = join(fullDir, item);
    const relativePath = relative(root, fullPath);
    if (statSync(fullPath).isDirectory()) {
      results.push(...readTree(relativePath, extensions));
    } else if (extensions.some((extension) => item.endsWith(extension))) {
      results.push(relativePath);
    }
  }
  return results.sort();
}

function read(path) {
  return readFileSync(join(root, path), "utf8");
}

function write(path, content) {
  const target = join(root, path);
  mkdirSync(dirname(target), { recursive: true });
  writeFileSync(target, content);
}

function markdownCell(value) {
  return String(value).replaceAll("\n", " ").replaceAll("|", "\\|");
}
