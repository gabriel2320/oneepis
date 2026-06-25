#!/usr/bin/env node
import { existsSync, mkdirSync, readdirSync, readFileSync, statSync, writeFileSync } from "node:fs";
import { dirname, join, relative } from "node:path";

const root = process.cwd();

const sources = {
  models: "apps/api/src/oneepis_api/models",
  schemas: "apps/api/src/oneepis_api/schemas",
  routes: "apps/api/src/oneepis_api/api/v1/routes",
  auditService: "apps/api/src/oneepis_api/services/audit.py",
  webApi: "apps/web/src/lib/api",
  webTypes: "apps/web/src/lib/type-contracts",
  webApp: "apps/web/src/app",
  clinicalComponents: "apps/web/src/components/clinical",
  printComponents: "apps/web/src/components/print",
  screenCapabilities: "apps/web/src/lib/screen-capabilities.ts",
  screenTree: "docs/SCREEN_TREE.md",
};

const fileCache = new Map();
const modelFiles = readTree(sources.models, [".py"]);
const schemaFiles = readTree(sources.schemas, [".py"]);
const routeFiles = readTree(sources.routes, [".py"]);
const webApiFiles = readTree(sources.webApi, [".ts"]);
const webTypeFiles = readTree(sources.webTypes, [".ts"]);
const webAppFiles = readTree(sources.webApp, [".tsx", ".ts"]);
const clinicalComponentFiles = readTree(sources.clinicalComponents, [".tsx", ".ts"]);
const printComponentFiles = readTree(sources.printComponents, [".tsx", ".ts"]);
const allScreenFiles = [...webAppFiles, ...clinicalComponentFiles];
const allPaperFiles = [
  ...webAppFiles.filter((path) => path.includes("/print/")),
  ...printComponentFiles,
];
const auditServiceText = readOptional(sources.auditService);

const domains = [
  {
    domain: "Patient",
    table: "patients",
    model: "Patient",
    ownerStatus: "owner",
    clinical: false,
    routeHints: ["patient_core.py"],
    schemaHints: ["Patient"],
    tsHints: ["Patient"],
    clientHints: ["Patient", "patients", "getPatient", "createPatient", "updatePatient"],
    screenHints: ["patient", "pacientes", "Patient"],
    paperHints: ["patient", "pacientes", "Patient"],
    strictSourceRef: false,
    recommendation: "Mantener como raiz de identidad; conservar auditoria before/after en cambios.",
  },
  {
    domain: "ClinicalEncounter",
    table: "clinical_encounters",
    model: "ClinicalEncounter",
    ownerStatus: "owner",
    clinical: true,
    routeHints: ["patient_encounters.py"],
    schemaHints: ["ClinicalEncounter"],
    tsHints: ["ClinicalEncounter"],
    clientHints: ["Encounter", "encounter"],
    screenHints: ["encounter", "encuentro"],
    paperHints: ["encounter", "encuentro"],
    strictEncounter: false,
    strictSourceRef: false,
    recommendation: "Usar como eje de episodio cuando exista contexto activo.",
  },
  {
    domain: "ClinicalEntry",
    table: "clinical_entries",
    model: "ClinicalEntry",
    ownerStatus: "owner",
    clinical: true,
    routeHints: ["patient_entries.py"],
    schemaHints: ["ClinicalEntry"],
    tsHints: ["ClinicalEntry"],
    clientHints: ["ClinicalEntry", "clinical-entries"],
    screenHints: ["ClinicalEntry", "entry", "evolucion", "evoluciones"],
    paperHints: ["ClinicalEntry", "entry", "evolucion", "evoluciones"],
    strictEncounter: false,
    strictSourceRef: false,
    recommendation: "Tratar como documento narrativo primario; no exigir source_ref porque es fuente.",
  },
  {
    domain: "ClinicalEvent",
    table: "clinical_events",
    model: "ClinicalEvent",
    ownerStatus: "owner",
    clinical: true,
    routeHints: ["patient_events.py"],
    schemaHints: ["ClinicalEvent", "ClinicalTimeline"],
    tsHints: ["ClinicalEvent", "ClinicalTimeline"],
    clientHints: ["ClinicalEvent", "clinical-events", "timeline"],
    screenHints: ["ClinicalEvent", "event", "evento", "timeline"],
    paperHints: ["ClinicalEvent", "event", "evento", "timeline"],
    strictEncounter: false,
    strictSourceRef: true,
    recommendation: "Mantener como puente longitudinal entre fuente, timeline, ficha, IA y papel.",
  },
  {
    domain: "VitalSign",
    table: "vital_signs",
    model: "VitalSign",
    ownerStatus: "owner",
    clinical: true,
    routeHints: ["patient_vitals.py"],
    schemaHints: ["VitalSign"],
    tsHints: ["VitalSign"],
    clientHints: ["VitalSign", "vital-signs"],
    screenHints: ["VitalSign", "vital", "signos-vitales"],
    paperHints: ["VitalSign", "vital", "signos"],
    strictEncounter: false,
    strictSourceRef: false,
    recommendation: "Si el signo se usa como hecho longitudinal, crear ClinicalEvent con source_type=vital_sign.",
  },
  {
    domain: "Allergy",
    table: "allergies",
    model: "Allergy",
    ownerStatus: "owner",
    clinical: true,
    routeHints: ["patient_allergies.py"],
    schemaHints: ["Allergy"],
    tsHints: ["Allergy"],
    clientHints: ["Allergy", "allergies"],
    screenHints: ["Allergy", "allerg", "alerg"],
    paperHints: ["Allergy", "allerg", "alerg"],
    strictEncounter: false,
    strictSourceRef: false,
    recommendation: "Mantener como lista activa/historica del paciente; auditar altas, cambios y anulaciones.",
  },
  {
    domain: "Medication",
    table: "medications",
    model: "Medication",
    ownerStatus: "owner",
    clinical: true,
    routeHints: ["patient_medications.py"],
    schemaHints: ["Medication"],
    tsHints: ["Medication"],
    clientHints: ["Medication", "medications"],
    screenHints: ["Medication", "medicacion", "medication"],
    paperHints: ["Medication", "medicacion", "medication"],
    strictEncounter: false,
    strictSourceRef: false,
    recommendation: "Mantener como fuente estructurada de medicacion; no convertir receta en fuente primaria.",
  },
  {
    domain: "ActiveProblem",
    table: "active_problems",
    model: "ActiveProblem",
    ownerStatus: "owner",
    clinical: true,
    routeHints: ["patient_problems.py"],
    schemaHints: ["ActiveProblem"],
    tsHints: ["ActiveProblem"],
    clientHints: ["ActiveProblem", "problems"],
    screenHints: ["ActiveProblem", "problem", "problema"],
    paperHints: ["ActiveProblem", "problem", "problema"],
    strictEncounter: false,
    strictSourceRef: false,
    recommendation: "Mantener como fuente de problemas activos; enlazar eventos si nacen desde evolucion o IA.",
  },
  {
    domain: "LabResult",
    table: "",
    model: "",
    ownerStatus: "missing_owner",
    clinical: true,
    routeHints: ["patient_entries.py", "patient_events.py"],
    schemaHints: ["Lab", "LAB_RESULT", "EXAM_RESULT"],
    tsHints: ["Lab", "LAB_RESULT", "EXAM_RESULT"],
    clientHints: ["Lab", "lab", "exam"],
    screenHints: ["lab", "laboratorio", "exam"],
    paperHints: ["lab", "laboratorio", "exam"],
    strictEncounter: false,
    strictSourceRef: true,
    recommendation: "Hoy debe trazarse como ClinicalEntry LAB_RESULT o ClinicalEvent EXAM_RESULT hasta definir tabla dueña.",
  },
  {
    domain: "ClinicalRisk",
    table: "",
    model: "",
    ownerStatus: "missing_owner",
    clinical: true,
    routeHints: [],
    schemaHints: ["Risk", "risk"],
    tsHints: ["Risk", "risk"],
    clientHints: ["Risk", "risk"],
    screenHints: ["risk", "riesgo"],
    paperHints: ["risk", "riesgo"],
    strictEncounter: false,
    strictSourceRef: true,
    recommendation: "Si el riesgo es calculado, documentar fuente; si es clinico editable, definir tabla dueña antes de escribir.",
  },
  {
    domain: "AuditEvent",
    table: "audit_events",
    model: "AuditEvent",
    ownerStatus: "owner",
    clinical: false,
    routeHints: ["patient_audit.py"],
    schemaHints: ["AuditEvent"],
    tsHints: ["AuditEvent"],
    clientHints: ["AuditEvent", "audit-events"],
    screenHints: ["AuditEvent", "audit", "auditoria"],
    paperHints: ["AuditEvent", "audit", "auditoria"],
    strictSourceRef: false,
    recommendation: "Mantener como traza transversal; patient_id puede venir por entity_id o metadata, no como campo directo.",
  },
];

const rows = domains.map(buildDomainRow);
const report = {
  generated_at: new Date().toISOString(),
  scope: "clinical_traceability",
  sources,
  rows,
  summary: summarize(rows),
};

write("reports/traceability-map.json", `${JSON.stringify(report, null, 2)}\n`);
write("reports/traceability-map.md", renderMarkdown(report));

console.log(
  `Traceability map written: ${rows.length} domains, ${Object.entries(report.summary.states)
    .map(([state, count]) => `${state}=${count}`)
    .join(", ")}`,
);

function buildDomainRow(definition) {
  const model = definition.model ? findModel(definition.model) : missingModel(definition);
  const routes = findRouteCoverage(definition);
  const schemas = findReferences(schemaFiles, definition.schemaHints);
  const tsTypes = findReferences(webTypeFiles, definition.tsHints);
  const clients = findReferences(webApiFiles, definition.clientHints);
  const screens = findReferences(allScreenFiles, definition.screenHints, {
    exclude: (path) => path.includes("/print/"),
  });
  const paper = findReferences(allPaperFiles, definition.paperHints);
  const auditActions = routes.auditActions;
  const status = classify(definition, model, routes, schemas, tsTypes, clients, screens, paper);

  return {
    dominio: definition.domain,
    tabla_duena: model.table || definition.table || "sin tabla duena dedicada",
    modelo_sqlalchemy: model.className ? `${model.className} (${model.path})` : "no encontrado",
    id_primario: model.hasIdMixin ? "IdMixin.id" : model.hasField("id") ? "id" : "no detectado",
    patient_id: patientIdLabel(definition, model),
    encounter_id: fieldLabel(model, "encounter_id"),
    actor_id: actorLabel(model, routes),
    correlation_id: correlationLabel(definition, model, routes),
    source_type_source_ref: sourceLabel(definition, model),
    endpoints_creacion: routes.create.join(", ") || "no detectado",
    endpoints_lectura: routes.read.join(", ") || "no detectado",
    endpoints_actualizacion: routes.update.join(", ") || "no detectado",
    pantalla: screens.join(", ") || "no detectada",
    papel: paper.join(", ") || "no detectado",
    cliente_frontend: clients.join(", ") || "no detectado",
    tipo_frontend: tsTypes.join(", ") || "no detectado",
    schema_pydantic: schemas.join(", ") || "no detectado",
    auditoria: auditActions.join(", ") || "no detectada",
    riesgo_redundancia: redundancyRisk(definition, model, screens, paper),
    estado: status,
    recomendacion: definition.recommendation,
  };
}

function classify(definition, model, routes, schemas, tsTypes, clients, screens, paper) {
  if (definition.ownerStatus === "missing_owner") {
    return "DUPLICATED_TRUTH";
  }
  if (definition.clinical && !model.hasField("patient_id")) {
    return "NO_PATIENT_ID";
  }
  if (definition.strictEncounter && !model.hasField("encounter_id")) {
    return "NO_ENCOUNTER_LINK";
  }
  if (definition.strictSourceRef && !(model.hasField("source_type") && model.hasField("source_ref"))) {
    return "NO_SOURCE_REF";
  }
  if (routes.hasWrites && routes.auditActions.length === 0) {
    return "NO_AUDIT_EVENT";
  }
  if (screens.length > 0 && clients.length === 0 && routes.read.length === 0) {
    return "SCREEN_WITHOUT_SOURCE";
  }
  if (paper.length > 0 && clients.length === 0 && routes.read.length === 0) {
    return "PAPER_WITHOUT_SOURCE";
  }
  if (schemas.length > 0 && tsTypes.length === 0 && clients.length > 0) {
    return "FRONTEND_TYPE_DRIFT";
  }
  return "READ_MODEL_OK";
}

function findModel(className) {
  for (const path of modelFiles) {
    const text = read(path);
    const body = pythonClassBody(text, className);
    if (!body) {
      continue;
    }
    const classLine = text.split("\n").find((line) => line.startsWith(`class ${className}(`)) ?? "";
    const tableMatch = body.match(/__tablename__\s*=\s*"([^"]+)"/);
    return {
      className,
      path,
      body,
      table: tableMatch?.[1] ?? "",
      hasIdMixin: classLine.includes("IdMixin"),
      hasField(field) {
        return new RegExp(`\\b${escapeRegExp(field)}\\s*:`).test(body);
      },
    };
  }
  return missingModel({ model: className });
}

function missingModel(definition) {
  return {
    className: definition.model ?? "",
    path: "",
    body: "",
    table: "",
    hasIdMixin: false,
    hasField() {
      return false;
    },
  };
}

function findRouteCoverage(definition) {
  const candidates = routeFiles.filter((path) =>
    definition.routeHints.some((hint) => path.includes(hint) || read(path).includes(hint)),
  );
  const create = [];
  const readEndpoints = [];
  const update = [];
  const auditActions = new Set();
  let hasWrites = false;
  for (const path of candidates) {
    const text = read(path);
    const routeLines = text
      .split("\n")
      .filter((line) => line.trim().startsWith("@router."))
      .map((line) => line.trim());
    for (const line of routeLines) {
      if (line.includes("@router.post")) {
        create.push(routeLabel(path, line));
        hasWrites = true;
      } else if (line.includes("@router.patch") || line.includes("@router.delete")) {
        update.push(routeLabel(path, line));
        hasWrites = true;
      } else if (line.includes("@router.get")) {
        readEndpoints.push(routeLabel(path, line));
      }
    }
    for (const action of text.matchAll(/action="([^"]+)"/g)) {
      auditActions.add(action[1]);
    }
  }
  return {
    create: unique(create),
    read: unique(readEndpoints),
    update: unique(update),
    auditActions: [...auditActions].sort(),
    hasWrites,
    files: candidates,
  };
}

function findReferences(files, hints, options = {}) {
  const matches = [];
  for (const path of files) {
    if (options.exclude?.(path)) {
      continue;
    }
    const text = read(path);
    if (hints.some((hint) => text.includes(hint) || path.toLowerCase().includes(hint.toLowerCase()))) {
      matches.push(path);
    }
  }
  return unique(matches).map((path) => relative(root, join(root, path)));
}

function patientIdLabel(definition, model) {
  if (model.hasField("patient_id")) {
    return "directo";
  }
  if (definition.domain === "Patient") {
    return "id propio";
  }
  if (definition.domain === "AuditEvent") {
    return "indirecto por entity_id/metadata";
  }
  return "NO_PATIENT_ID";
}

function fieldLabel(model, field) {
  return model.hasField(field) ? "directo" : "no detectado";
}

function actorLabel(model, routes) {
  if (model.hasField("actor_id")) {
    return "modelo.actor_id";
  }
  if (model.hasField("created_by")) {
    return "modelo.created_by";
  }
  if (routes.files.some((path) => read(path).includes("actor: PatientActorDep"))) {
    return "PatientActorDep en endpoint";
  }
  if (routes.files.some((path) => read(path).includes("actor: AuthenticatedUser"))) {
    return "AuthenticatedUser en endpoint";
  }
  return "no detectado";
}

function correlationLabel(definition, model, routes) {
  if (model.hasField("correlation_id")) {
    return "directo";
  }
  if (definition.domain === "AuditEvent") {
    return auditServiceText.includes("correlation_id") ? "directo via audit context" : "directo";
  }
  if (routes.auditActions.length > 0 && auditServiceText.includes("correlation_id")) {
    return "via AuditEvent";
  }
  return "no detectado";
}

function sourceLabel(definition, model) {
  if (model.hasField("source_type") && model.hasField("source_ref")) {
    return "source_type + source_ref";
  }
  if (definition.strictSourceRef) {
    return "NO_SOURCE_REF";
  }
  return "no requerido en primera pasada";
}

function redundancyRisk(definition, model, screens, paper) {
  if (definition.ownerStatus === "missing_owner") {
    return "alto: no hay tabla duena dedicada; riesgo de vivir como texto, evento o entrada";
  }
  if (paper.length > 0 && !model.hasField("source_ref") && definition.strictSourceRef) {
    return "medio: se imprime/proyecta sin source_ref detectable";
  }
  if (screens.length > 0 && paper.length > 0) {
    return "bajo: tiene proyecciones visibles; verificar que lean la fuente duena";
  }
  return "bajo";
}

function routeLabel(path, line) {
  const method = line.match(/@router\.(get|post|patch|delete|put)/)?.[1]?.toUpperCase() ?? "ROUTE";
  const route = line.match(/\("([^"]*)"/)?.[1] ?? "";
  return `${method} ${route} (${relative(root, join(root, path))})`;
}

function pythonClassBody(text, name) {
  const match = text.match(new RegExp(`class ${escapeRegExp(name)}\\([^)]*\\):\\n([\\s\\S]*?)(?=\\nclass |$)`));
  return match?.[1] ?? "";
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
  if (!fileCache.has(path)) {
    fileCache.set(path, readFileSync(join(root, path), "utf8"));
  }
  return fileCache.get(path);
}

function readOptional(path) {
  return existsSync(join(root, path)) ? read(path) : "";
}

function write(path, content) {
  const target = join(root, path);
  mkdirSync(dirname(target), { recursive: true });
  writeFileSync(target, content);
}

function summarize(items) {
  const states = {};
  for (const item of items) {
    states[item.estado] = (states[item.estado] ?? 0) + 1;
  }
  return {
    total: items.length,
    states,
    critical_findings: items
      .filter((item) => item.estado !== "READ_MODEL_OK")
      .map((item) => `${item.dominio}: ${item.estado}`),
  };
}

function renderMarkdown(data) {
  const blockedRows = data.rows.filter((row) => row.estado === "DUPLICATED_TRUTH");
  const header = [
    "# Traceability Map - OneEpis",
    "",
    `Generado: ${data.generated_at}`,
    "",
    "## Resumen",
    "",
    `- Dominios auditados: ${data.summary.total}`,
    ...Object.entries(data.summary.states).map(([state, count]) => `- ${state}: ${count}`),
    "",
    "## Hallazgos criticos",
    "",
    ...(data.summary.critical_findings.length
      ? data.summary.critical_findings.map((item) => `- ${item}`)
      : ["- Sin hallazgos criticos."]),
    "",
    "## Lectura ejecutiva",
    "",
    "- Patient, ClinicalEntry, ClinicalEvent y AuditEvent son las piezas centrales de trazabilidad actual.",
    "- ClinicalEvent es el unico dominio inicial con fuente explicita source_type/source_ref.",
    "- LabResult y ClinicalRisk no deben escribirse como nuevas verdades hasta definir tabla duena o regla de proyeccion.",
    "",
    "## Dominios bloqueados",
    "",
    ...(blockedRows.length
      ? blockedRows.map(
          (row) =>
            `- ${row.dominio}: no implementar pantalla productiva, tabla secundaria ni escritura nueva. ${row.recomendacion}`,
        )
      : ["- Sin dominios bloqueados por verdad duplicada."]),
    "",
    "## Matriz",
    "",
    [
      "Dominio",
      "Tabla dueña",
      "Modelo SQLAlchemy",
      "ID primario",
      "patient_id",
      "encounter_id",
      "actor_id",
      "correlation_id",
      "source_type/source_ref",
      "Creación",
      "Lectura",
      "Actualización",
      "Pantalla",
      "Papel",
      "Auditoría",
      "Riesgo redundancia",
      "Estado",
      "Recomendación",
    ].join(" | "),
    [
      "---",
      "---",
      "---",
      "---",
      "---",
      "---",
      "---",
      "---",
      "---",
      "---",
      "---",
      "---",
      "---",
      "---",
      "---",
      "---",
      "---",
      "---",
    ].join(" | "),
  ];

  const rows = data.rows.map((row) =>
    [
      row.dominio,
      row.tabla_duena,
      row.modelo_sqlalchemy,
      row.id_primario,
      row.patient_id,
      row.encounter_id,
      row.actor_id,
      row.correlation_id,
      row.source_type_source_ref,
      row.endpoints_creacion,
      row.endpoints_lectura,
      row.endpoints_actualizacion,
      compactList(row.pantalla),
      compactList(row.papel),
      row.auditoria,
      row.riesgo_redundancia,
      row.estado,
      row.recomendacion,
    ]
      .map(markdownCell)
      .join(" | "),
  );

  return `${[...header, ...rows].join("\n")}\n`;
}

function unique(items) {
  return [...new Set(items)].sort();
}

function markdownCell(value) {
  return String(value).replaceAll("\n", " ").replaceAll("|", "\\|");
}

function compactList(value, limit = 6) {
  const items = String(value)
    .split(", ")
    .filter(Boolean);
  if (items.length <= limit) {
    return value;
  }
  return `${items.slice(0, limit).join(", ")} (+${items.length - limit} mas)`;
}

function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}
