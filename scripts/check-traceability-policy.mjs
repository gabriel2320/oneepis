#!/usr/bin/env node
import { execFileSync } from "node:child_process";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";

const root = process.cwd();
const allowedBlockedDomains = new Set(["LabResult", "ClinicalRisk"]);

execFileSync("node", ["scripts/audit-traceability-map.mjs"], {
  cwd: root,
  stdio: "inherit",
});

const traceability = JSON.parse(read("reports/traceability-map.json"));
const rows = traceability.rows.map(inspectRow);
const failures = rows.filter((row) => row.gaps.length > 0);
const report = {
  generated_at: new Date().toISOString(),
  scope: "clinical_traceability_policy",
  summary: {
    domains_checked: rows.length,
    allowed_blocked_domains: [...allowedBlockedDomains].sort(),
    failures: failures.length,
  },
  rows,
};

write("reports/traceability-guard.json", `${JSON.stringify(report, null, 2)}\n`);
write("reports/traceability-guard.md", renderMarkdown(report));

if (failures.length > 0) {
  console.error(`Traceability policy failed: ${failures.length} domain gap(s).`);
  for (const row of failures) {
    console.error(`- ${row.domain}: ${row.gaps.join(", ")}`);
  }
  process.exit(1);
}

console.log(
  `Traceability policy passed: ${rows.length} domains, ${allowedBlockedDomains.size} blocked domain(s) allowed.`,
);

function inspectRow(row) {
  const gaps = [];
  const domain = row.dominio;
  const isAllowedBlocked = allowedBlockedDomains.has(domain);
  const hasOwner = row.estado === "READ_MODEL_OK";
  const isClinicalOwner = hasOwner && !["Patient", "AuditEvent"].includes(domain);

  if (!hasOwner && !isAllowedBlocked) {
    gaps.push(`UNEXPECTED_TRACEABILITY_STATE:${row.estado}`);
  }
  if (isAllowedBlocked && row.estado !== "DUPLICATED_TRUTH") {
    gaps.push(`BLOCKED_DOMAIN_STATE_CHANGED:${row.estado}`);
  }
  if (isClinicalOwner && row.patient_id !== "directo") {
    gaps.push("CLINICAL_OWNER_WITHOUT_DIRECT_PATIENT_ID");
  }
  if (domain === "ClinicalEvent" && row.source_type_source_ref !== "source_type + source_ref") {
    gaps.push("CLINICAL_EVENT_WITHOUT_SOURCE_REF");
  }
  if (isClinicalOwner && row.endpoints_creacion !== "no detectado" && row.auditoria === "no detectada") {
    gaps.push("CLINICAL_WRITE_WITHOUT_AUDIT_EVIDENCE");
  }
  if (domain === "Patient" && row.auditoria === "no detectada") {
    gaps.push("PATIENT_WITHOUT_AUDIT_EVIDENCE");
  }
  if (domain === "AuditEvent" && row.actor_id !== "modelo.actor_id") {
    gaps.push("AUDIT_EVENT_WITHOUT_ACTOR_ID");
  }

  return {
    domain,
    state: row.estado,
    table: row.tabla_duena,
    patient_id: row.patient_id,
    encounter_id: row.encounter_id,
    source_type_source_ref: row.source_type_source_ref,
    audit: row.auditoria,
    recommendation: row.recomendacion,
    allowed_blocked_domain: isAllowedBlocked,
    gaps,
  };
}

function renderMarkdown(data) {
  const lines = [
    "# Traceability Guard - OneEpis",
    "",
    `Generado: ${data.generated_at}`,
    "",
    "## Resumen",
    "",
    `- Dominios revisados: ${data.summary.domains_checked}`,
    `- Dominios bloqueados permitidos: ${data.summary.allowed_blocked_domains.join(", ")}`,
    `- Fallas: ${data.summary.failures}`,
    "",
    "## Matriz",
    "",
    "Dominio | Estado | Tabla | patient_id | encounter_id | source_type/source_ref | Auditoria | Bloqueado permitido | Brechas",
    "--- | --- | --- | --- | --- | --- | --- | --- | ---",
    ...data.rows.map((row) =>
      [
        row.domain,
        row.state,
        row.table,
        row.patient_id,
        row.encounter_id,
        row.source_type_source_ref,
        row.audit,
        row.allowed_blocked_domain ? "si" : "no",
        row.gaps.join(", ") || "OK",
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
