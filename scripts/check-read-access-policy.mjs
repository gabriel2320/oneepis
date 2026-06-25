#!/usr/bin/env node
import { execFileSync } from "node:child_process";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";

const root = process.cwd();

execFileSync("node", ["scripts/audit-read-access.mjs"], {
  cwd: root,
  stdio: "inherit",
});

const readAccess = JSON.parse(read("reports/read-access-map.json"));
const rows = readAccess.rows.map(classifyPolicy);
const summary = {
  routes_reviewed: rows.length,
  audit_required_p0: rows.filter((row) => row.proposed_policy === "AUDIT_REQUIRED_P0").length,
  audit_required_p1: rows.filter((row) => row.proposed_policy === "AUDIT_REQUIRED_P1").length,
  review_volume_policy: rows.filter((row) => row.proposed_policy === "REVIEW_VOLUME_POLICY").length,
  exempt_technical: rows.filter((row) => row.proposed_policy === "EXEMPT_TECHNICAL").length,
  blocking_ready: false,
};
const report = {
  generated_at: new Date().toISOString(),
  scope: "clinical_read_access_policy_report_only",
  source_report: "reports/read-access-map.json",
  report_only: true,
  summary,
  blockers_before_blocking: [
    "definir retencion y volumen esperado de eventos de lectura",
    "evitar auditoria de endpoints tecnicos o polling frecuente",
    "definir si busquedas/listas se auditan siempre, por muestreo o por acceso a ficha",
    "definir estructura de evento sin duplicar datos clinicos sensibles en metadata",
    "agregar tests de no regresion antes de activar bloqueo CI",
  ],
  required_event_fields: [
    "actor_id",
    "actor_roles",
    "request_method",
    "request_path",
    "correlation_id",
    "patient_id cuando exista",
    "resource_type",
    "resource_id cuando exista",
    "access_policy",
    "created_at",
  ],
  rows,
};

assertReportOnly(report);

write("reports/read-access-policy.json", `${JSON.stringify(report, null, 2)}\n`);
write("reports/read-access-policy.md", renderMarkdown(report));

console.log(
  `Read access policy report written: ${summary.audit_required_p0} P0, ${summary.audit_required_p1} P1, ${summary.review_volume_policy} volume review.`,
);

function classifyPolicy(row) {
  const classification = proposedPolicy(row);
  return {
    route: `${row.method} ${row.full_path}`,
    route_file: row.route_file,
    function_name: row.function_name,
    sensitivity: row.sensitivity,
    current_policy: row.policy,
    proposed_policy: classification.policy,
    rollout_phase: classification.rollout,
    rationale: classification.rationale,
    ci_behavior: "report-only",
  };
}

function assertReportOnly(report) {
  if (report.summary.blocking_ready) {
    throw new Error("Read access policy cannot be blocking until retention, volume and tests are defined.");
  }
  const blockingRows = report.rows.filter((row) => row.ci_behavior !== "report-only");
  if (blockingRows.length > 0) {
    throw new Error(
      `Read access policy must remain report-only; ${blockingRows.length} row(s) changed CI behavior.`,
    );
  }
}

function proposedPolicy(row) {
  if (row.policy === "EXEMPT_TECHNICAL") {
    return {
      policy: "EXEMPT_TECHNICAL",
      rollout: "no_aplica",
      rationale: "Ruta tecnica, health, sesion o estado operacional sin lectura clinica de paciente.",
    };
  }

  if (["audit_trail", "patient_record", "clinical_timeline", "hospital_document"].includes(row.sensitivity)) {
    return {
      policy: "AUDIT_REQUIRED_P0",
      rollout: "primera_implementacion",
      rationale: "Lectura clinica sensible o documental; debe dejar trail antes de produccion.",
    };
  }

  if (["patient_child_entity", "hospital_board"].includes(row.sensitivity)) {
    return {
      policy: "AUDIT_REQUIRED_P1",
      rollout: "segunda_implementacion",
      rationale: "Lectura clinica de entidad o tablero con paciente; auditable tras validar volumen.",
    };
  }

  if (["patient_search_or_identity", "clinical_read"].includes(row.sensitivity)) {
    return {
      policy: "REVIEW_VOLUME_POLICY",
      rollout: "diseno_retencion",
      rationale: "Puede generar alto volumen o corresponder a catalogo/lista; requiere politica de muestreo o retencion.",
    };
  }

  return {
    policy: "REVIEW_VOLUME_POLICY",
    rollout: "revision_manual",
    rationale: "Clasificacion automatica insuficiente; revisar antes de auditar o eximir.",
  };
}

function renderMarkdown(data) {
  const lines = [
    "# Read Access Policy - OneEpis",
    "",
    `Generado: ${data.generated_at}`,
    "",
    "## Resumen",
    "",
    `- Rutas revisadas: ${data.summary.routes_reviewed}`,
    `- Auditoria requerida P0: ${data.summary.audit_required_p0}`,
    `- Auditoria requerida P1: ${data.summary.audit_required_p1}`,
    `- Requieren politica de volumen/retencion: ${data.summary.review_volume_policy}`,
    `- Exentas tecnicas: ${data.summary.exempt_technical}`,
    `- Listo para bloqueo CI: ${data.summary.blocking_ready ? "si" : "no"}`,
    "",
    "## Bloqueantes antes de activar CI",
    "",
    ...data.blockers_before_blocking.map((item) => `- ${item}`),
    "",
    "## Campos minimos futuros",
    "",
    ...data.required_event_fields.map((item) => `- ${item}`),
    "",
    "## Matriz",
    "",
    "Ruta | Sensibilidad | Politica propuesta | Fase | CI | Razon",
    "--- | --- | --- | --- | --- | ---",
    ...data.rows.map((row) =>
      [
        `${row.route} (${row.route_file})`,
        row.sensitivity,
        row.proposed_policy,
        row.rollout_phase,
        row.ci_behavior,
        row.rationale,
      ]
        .map(markdownCell)
        .join(" | "),
    ),
  ];
  return `${lines.join("\n")}\n`;
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
