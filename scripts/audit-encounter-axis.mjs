#!/usr/bin/env node
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";

const root = process.cwd();

const domains = [
  {
    domain: "ClinicalEncounter",
    model: "ClinicalEncounter",
    table: "clinical_encounters",
    expectation: "EPISODE_OWNER",
    rationale: "Es la entidad dueña del episodio; no debe tener encounter_id propio.",
  },
  {
    domain: "ClinicalEntry",
    model: "ClinicalEntry",
    table: "clinical_entries",
    expectation: "OPTIONAL_ENCOUNTER",
    rationale: "SOAP/evolucion puede ser longitudinal, pero debe vincularse cuando existe episodio activo.",
  },
  {
    domain: "ClinicalEvent",
    model: "ClinicalEvent",
    table: "clinical_events",
    expectation: "OPTIONAL_ENCOUNTER",
    rationale: "Hecho longitudinal puede nacer fuera de un episodio, pero debe heredar encuentro cuando viene de acto clinico.",
  },
  {
    domain: "HospitalBed",
    model: "HospitalBed",
    table: "hospital_beds",
    expectation: "OPTIONAL_ASSIGNMENT",
    rationale: "La cama puede existir sin paciente; encounter_id aparece solo cuando se asigna a ingreso.",
  },
  {
    domain: "HospitalDailySheet",
    model: "HospitalDailySheet",
    table: "hospital_daily_sheets",
    expectation: "REQUIRED_ENCOUNTER",
    rationale: "Hoja diaria hospitalaria pertenece a un ingreso hospitalario activo.",
  },
  {
    domain: "HospitalIndication",
    model: "HospitalIndication",
    table: "hospital_indications",
    expectation: "REQUIRED_ENCOUNTER",
    rationale: "Indicacion hospitalaria minima pertenece a un ingreso hospitalario activo.",
  },
  {
    domain: "VitalSign",
    model: "VitalSign",
    table: "vital_signs",
    expectation: "PATIENT_LONGITUDINAL",
    rationale: "Signo vital vive por paciente; si explica episodio, se proyecta como ClinicalEvent con source_type vital_sign.",
  },
  {
    domain: "Allergy",
    model: "Allergy",
    table: "allergies",
    expectation: "PATIENT_LONGITUDINAL",
    rationale: "Alergia es longitudinal del paciente; no forzar episodio sin decision clinica.",
  },
  {
    domain: "Medication",
    model: "Medication",
    table: "medications",
    expectation: "PATIENT_LONGITUDINAL",
    rationale: "Medicacion activa no es receta ni orden; no forzar episodio hasta definir prescripcion legal.",
  },
  {
    domain: "ActiveProblem",
    model: "ActiveProblem",
    table: "active_problems",
    expectation: "PATIENT_LONGITUDINAL",
    rationale: "Problema activo puede cruzar episodios; el origen debe trazarse con eventos/evoluciones si aplica.",
  },
];

const modelFiles = [
  "apps/api/src/oneepis_api/models/clinical_record.py",
  "apps/api/src/oneepis_api/models/hospitalization.py",
];
const routeFiles = [
  "apps/api/src/oneepis_api/api/v1/routes/patient_entries.py",
  "apps/api/src/oneepis_api/api/v1/routes/patient_events.py",
  "apps/api/src/oneepis_api/api/v1/routes/hospitalization.py",
  "apps/api/src/oneepis_api/api/v1/routes/hospitalization_daily_sheets.py",
  "apps/api/src/oneepis_api/api/v1/routes/hospitalization_indications.py",
];
const schemaFiles = [
  "apps/api/src/oneepis_api/schemas/clinical_record_contracts/entries_events.py",
  "apps/api/src/oneepis_api/schemas/clinical_record_contracts/longitudinal.py",
  "apps/api/src/oneepis_api/schemas/hospitalization.py",
];
const webFiles = [
  "apps/web/src/lib/type-contracts/clinical-record.ts",
  "apps/web/src/lib/type-contracts/hospitalization.ts",
  "apps/web/src/components/clinical/patient-soap-page.tsx",
  "apps/web/src/components/clinical/patient-event-pages.tsx",
  "apps/web/src/components/clinical/patient-widgets.tsx",
  "apps/web/src/components/clinical/patient-formal-cover.tsx",
];

const rows = domains.map(inspectDomain);
const summary = {
  domains_reviewed: rows.length,
  required_encounter_ok: rows.filter(
    (row) => row.expectation === "REQUIRED_ENCOUNTER" && row.status === "OK",
  ).length,
  optional_encounter_ok: rows.filter(
    (row) => row.expectation === "OPTIONAL_ENCOUNTER" && row.status === "OK",
  ).length,
  longitudinal_not_forced: rows.filter((row) => row.expectation === "PATIENT_LONGITUDINAL").length,
  follow_up_required: rows.filter((row) => row.status !== "OK").length,
};
const report = {
  generated_at: new Date().toISOString(),
  scope: "clinical_encounter_axis",
  summary,
  rows,
};

write("reports/encounter-axis-map.json", `${JSON.stringify(report, null, 2)}\n`);
write("reports/encounter-axis-map.md", renderMarkdown(report));

console.log(
  `Encounter axis map written: ${summary.domains_reviewed} domains, ${summary.follow_up_required} follow-up item(s).`,
);

function inspectDomain(definition) {
  const model = findModel(definition.model);
  const schema = findReferences(schemaFiles, definition.model);
  const routes = findReferences(routeFiles, definition.model);
  const web = findReferences(webFiles, definition.domain) || findReferences(webFiles, "encounter_id");
  const hasEncounterId = Boolean(model?.body.includes("encounter_id:"));
  const nullableEncounter = Boolean(model?.body.includes("uuid.UUID | None"));
  const requiredEncounter = hasEncounterId && !nullableEncounter;
  const validatesEncounter = routes.some((path) => read(path).includes("validate_encounter_for_patient"));
  const requiresActiveHospitalization = routes.some((path) => read(path).includes("_require_active_hospitalization"));
  const validation_evidence =
    definition.expectation === "EPISODE_OWNER"
      ? "no aplica: entidad dueña"
      : validationLabel({ validatesEncounter, requiresActiveHospitalization });
  const status = classifyStatus(definition.expectation, {
    hasEncounterId,
    requiredEncounter,
    validatesEncounter,
    requiresActiveHospitalization,
  });

  return {
    domain: definition.domain,
    table: definition.table,
    expectation: definition.expectation,
    model_encounter_id: hasEncounterId
      ? requiredEncounter
        ? "required"
        : "optional"
      : "not_applicable",
    schema_evidence: compact(schema),
    route_evidence: compact(routes),
    frontend_evidence: compact(web),
    validation_evidence,
    status,
    recommendation: recommendation(definition, status),
    rationale: definition.rationale,
  };
}

function classifyStatus(expectation, evidence) {
  if (expectation === "EPISODE_OWNER") {
    return evidence.hasEncounterId ? "REVIEW" : "OK";
  }
  if (expectation === "REQUIRED_ENCOUNTER") {
    return evidence.requiredEncounter && evidence.requiresActiveHospitalization ? "OK" : "REVIEW";
  }
  if (expectation === "OPTIONAL_ENCOUNTER") {
    return evidence.hasEncounterId && evidence.validatesEncounter ? "OK" : "REVIEW";
  }
  if (expectation === "OPTIONAL_ASSIGNMENT") {
    return evidence.hasEncounterId ? "OK" : "REVIEW";
  }
  if (expectation === "PATIENT_LONGITUDINAL") {
    return evidence.hasEncounterId ? "REVIEW" : "OK";
  }
  return "REVIEW";
}

function recommendation(definition, status) {
  if (status === "OK") {
    return definition.rationale;
  }
  if (definition.expectation === "REQUIRED_ENCOUNTER") {
    return "Revisar si la ruta exige ingreso activo y si schema/read model expone encounter_id.";
  }
  if (definition.expectation === "OPTIONAL_ENCOUNTER") {
    return "Agregar validacion de encuentro antes de endurecer politica; no hacer migracion automatica.";
  }
  return "Revisar manualmente antes de forzar encounter_id.";
}

function validationLabel({ validatesEncounter, requiresActiveHospitalization }) {
  const items = [];
  if (validatesEncounter) {
    items.push("validate_encounter_for_patient");
  }
  if (requiresActiveHospitalization) {
    items.push("_require_active_hospitalization");
  }
  return items.join(", ") || "no detectada";
}

function findModel(name) {
  for (const path of modelFiles) {
    const text = read(path);
    const match = text.match(new RegExp(`class ${name}\\([\\s\\S]*?(?=\\nclass |$)`));
    if (match) {
      return { path, body: match[0] };
    }
  }
  return null;
}

function findReferences(files, pattern) {
  return files.filter((path) => existsSync(join(root, path)) && read(path).includes(pattern));
}

function compact(items, limit = 3) {
  if (!items || items.length === 0) {
    return "no detectado";
  }
  if (items.length <= limit) {
    return items.join(", ");
  }
  return `${items.slice(0, limit).join(", ")} (+${items.length - limit} mas)`;
}

function renderMarkdown(data) {
  const lines = [
    "# Encounter Axis Map - OneEpis",
    "",
    `Generado: ${data.generated_at}`,
    "",
    "## Resumen",
    "",
    `- Dominios revisados: ${data.summary.domains_reviewed}`,
    `- Required encounter OK: ${data.summary.required_encounter_ok}`,
    `- Optional encounter OK: ${data.summary.optional_encounter_ok}`,
    `- Longitudinales no forzados: ${data.summary.longitudinal_not_forced}`,
    `- Seguimientos requeridos: ${data.summary.follow_up_required}`,
    "",
    "## Politica",
    "",
    "Este reporte no cambia modelos. C7 solo declara donde `encounter_id` ya es eje clinico, donde es opcional y donde no debe forzarse sin decision clinica.",
    "",
    "## Matriz",
    "",
    "Dominio | Expectativa | Modelo encounter_id | Validacion | Estado | Recomendacion",
    "--- | --- | --- | --- | --- | ---",
    ...data.rows.map((row) =>
      [
        row.domain,
        row.expectation,
        row.model_encounter_id,
        row.validation_evidence,
        row.status,
        row.recommendation,
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
