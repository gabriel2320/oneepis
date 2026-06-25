#!/usr/bin/env node
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";

const root = process.cwd();

const sources = {
  model: "apps/api/src/oneepis_api/models/patient.py",
  schema: "apps/api/src/oneepis_api/schemas/patient.py",
  routes: "apps/api/src/oneepis_api/api/v1/routes/patient_core.py",
  openapi: "packages/contracts/openapi.json",
  ts: "apps/web/src/lib/type-contracts/patient.ts",
  client: "apps/web/src/lib/api/patients.ts",
  patientList: "apps/web/src/components/clinical/patient-list-pages.tsx",
  patientShell: "apps/web/src/components/clinical/patient-clinical-shell.tsx",
  patientRecord: "apps/web/src/components/clinical/patient-record-pages.tsx",
  patientStatus: "apps/web/src/components/clinical/patient-status-page.tsx",
  patientPrint: "apps/web/src/components/print/clinical-print.tsx",
  screenCapabilities: "apps/web/src/lib/screen-capabilities.ts",
};

const modelText = read(sources.model);
const schemaText = read(sources.schema);
const routesText = read(sources.routes);
const openapi = JSON.parse(read(sources.openapi));
const tsText = read(sources.ts);
const clientText = read(sources.client);
const screenText = [
  read(sources.patientList),
  read(sources.patientShell),
  read(sources.patientRecord),
  read(sources.patientStatus),
].join("\n");
const paperText = read(sources.patientPrint);
const capabilityText = read(sources.screenCapabilities);

const variables = [
  {
    variable: "first_name",
    category: "identity",
    endpoint: "GET/POST/PATCH /api/v1/patients",
    recommendation: "Mantener como identificador nominal visible en lista, ficha y papel.",
  },
  {
    variable: "last_name",
    category: "identity",
    endpoint: "GET/POST/PATCH /api/v1/patients",
    recommendation: "Mantener indexado y visible junto a first_name.",
  },
  {
    variable: "preferred_name",
    category: "identity",
    endpoint: "GET/POST/PATCH /api/v1/patients",
    recommendation: "Revisar si debe mostrarse con mayor prioridad en cabecera clinica.",
  },
  {
    variable: "birth_date",
    category: "identity",
    endpoint: "GET/POST /api/v1/patients",
    recommendation: "Mantener no editable por PATCH salvo flujo gobernado de identidad.",
  },
  {
    variable: "sex_at_birth",
    category: "identity",
    endpoint: "GET/POST /api/v1/patients",
    recommendation: "Mantener no editable por PATCH salvo flujo gobernado de identidad.",
  },
  {
    variable: "clinical_status",
    category: "clinical_state",
    endpoint: "GET/POST/PATCH /api/v1/patients",
    recommendation: "Mantener visible en ficha y editable solo desde estado clinico.",
  },
  {
    variable: "current_care_context",
    category: "clinical_state",
    endpoint: "GET/POST/PATCH /api/v1/patients",
    recommendation: "Mantener visible en ficha/lista y editable solo desde estado clinico.",
  },
  {
    variable: "document_id_hash",
    category: "identity_sensitive",
    endpoint: "GET/POST /api/v1/patients",
    recommendation: "Decidir si Patient TS debe tiparlo como campo expuesto o si backend debe ocultarlo del read model.",
  },
  {
    variable: "clinical_identifier",
    category: "administrative",
    endpoint: "GET/POST /api/v1/patients",
    recommendation: "Mantener como identificador clinico visible; no editar por PATCH sin flujo gobernado.",
  },
  {
    variable: "contact_phone",
    category: "contact",
    endpoint: "GET/POST/PATCH /api/v1/patients",
    recommendation: "Agregar al tipo Patient TS o retirar del read model; hoy create/update lo usan pero read TS no.",
  },
  {
    variable: "email",
    category: "contact",
    endpoint: "GET/POST/PATCH /api/v1/patients",
    recommendation: "Agregar al tipo Patient TS o retirar del read model; hoy create/update lo usan pero read TS no.",
  },
  {
    variable: "emergency_contact",
    category: "contact",
    endpoint: "GET/POST/PATCH /api/v1/patients",
    recommendation: "Agregar al tipo Patient TS o retirar del read model; definir estructura antes de mostrar en UI.",
  },
];

const rows = variables.map((definition) => buildRow(definition));
const report = {
  generated_at: new Date().toISOString(),
  scope: "patient",
  sources,
  rows,
  summary: summarize(rows),
};

write("reports/variable-map.json", `${JSON.stringify(report, null, 2)}\n`);
write("reports/variable-map.md", renderMarkdown(report));

console.log(
  `Variable map written: ${rows.length} patient variables, ${Object.entries(report.summary.states)
    .map(([state, count]) => `${state}=${count}`)
    .join(", ")}`,
);

function buildRow(definition) {
  const variable = definition.variable;
  const inModel = hasModelField(variable);
  const modelDescriptor = inModel ? modelFieldDescriptor(variable) : "";
  const schemaPresence = schemaClassesWithField(variable);
  const openapiPresence = openApiSchemasWithField(variable);
  const tsPresence = tsTypesWithField(variable);
  const clientPresence = clientUsesPatientTypes();
  const screenPresence = findUsages(variable, screenText);
  const paperPresence = findUsages(variable, paperText);
  const permission = routeHasPatientActor() ? "PatientActorDep on POST/PATCH" : "";
  const audit = routeHasPatientAudit() ? "patient.created / patient.updated" : "";
  const state = classify({
    inModel,
    schemaPresence,
    openapiPresence,
    tsPresence,
    screenPresence,
    paperPresence,
    permission,
    audit,
    variable,
  });

  return {
    dominio: "Paciente",
    variable,
    categoria: definition.category,
    tabla: inModel ? "patients" : "",
    modelo_sqlalchemy: modelDescriptor,
    schema_pydantic: schemaPresence.join(", ") || "",
    endpoint: definition.endpoint,
    openapi: openapiPresence.join(", ") || "",
    ts_type: tsPresence.join(", ") || "",
    api_client: clientPresence,
    pantalla: screenPresence.join(", ") || "no visible",
    papel: paperPresence.join(", ") || "no visible",
    permiso: permission || "PERMISSION_MISSING",
    auditoria: audit || "AUDIT_MISSING",
    screen_capability: capabilityText.includes("/pacientes") ? "patient routes declared" : "",
    estado: state,
    recomendacion: definition.recommendation,
  };
}

function classify({
  inModel,
  schemaPresence,
  openapiPresence,
  tsPresence,
  screenPresence,
  paperPresence,
  permission,
  audit,
  variable,
}) {
  if (!inModel && tsPresence.length > 0) {
    return "FRONTEND_ONLY";
  }
  if (inModel && schemaPresence.length > 0 && openapiPresence.length > 0 && tsPresence.length === 0) {
    return "BACKEND_ONLY";
  }
  if (schemaPresence.includes("PatientRead") && !tsPresence.includes("Patient")) {
    return "BACKEND_ONLY";
  }
  if (isEditable(variable) && !permission) {
    return "PERMISSION_MISSING";
  }
  if (isEditable(variable) && !audit) {
    return "AUDIT_MISSING";
  }
  if (inModel && tsPresence.length > 0 && screenPresence.length === 0 && paperPresence.length === 0) {
    return "UNUSED_FIELD";
  }
  return "OK";
}

function read(path) {
  return readFileSync(join(root, path), "utf8");
}

function write(path, content) {
  const target = join(root, path);
  mkdirSync(dirname(target), { recursive: true });
  writeFileSync(target, content);
}

function hasModelField(variable) {
  return new RegExp(`\\b${variable}\\s*:\\s*Mapped\\[`).test(modelText);
}

function modelFieldDescriptor(variable) {
  const line = modelText.split("\n").find((item) => new RegExp(`\\b${variable}\\s*:`).test(item));
  if (!line) {
    return "";
  }
  return `Patient.${variable} (${line.trim()})`;
}

function schemaClassesWithField(variable) {
  const baseHasField = new RegExp(`\\b${variable}\\s*:`).test(classBody(schemaText, "PatientBase"));
  const updateHasField = new RegExp(`\\b${variable}\\s*:`).test(classBody(schemaText, "PatientUpdate"));
  const classes = [];
  if (baseHasField) {
    classes.push("PatientBase", "PatientCreate", "PatientRead");
  }
  if (updateHasField) {
    classes.push("PatientUpdate");
  }
  if (variable === "patient") {
    classes.push("PatientRecordSnapshot");
  }
  return classes;
}

function openApiSchemasWithField(variable) {
  const schemas = openapi.components?.schemas ?? {};
  return ["PatientCreate", "PatientRead", "PatientUpdate", "PatientRecordSnapshot"].filter((name) => {
    const schema = schemas[name];
    return Boolean(schema?.properties?.[variable]);
  });
}

function tsTypesWithField(variable) {
  const result = [];
  const patientCreate = objectTypeBody(tsText, "PatientCreate");
  const patient = objectTypeBody(tsText, "Patient");
  const patientUpdate = aliasBody(tsText, "PatientUpdate");
  if (new RegExp(`\\b${variable}\\??:`).test(patientCreate)) {
    result.push("PatientCreate");
  }
  if (patientUpdate.includes(`"${variable}"`)) {
    result.push("PatientUpdate");
  }
  if (new RegExp(`\\b${variable}\\??:`).test(patient)) {
    result.push("Patient");
  }
  return result;
}

function clientUsesPatientTypes() {
  const functions = ["listPatients", "createPatient", "updatePatient", "getPatient", "getPatientRecord"];
  return functions.filter((name) => clientText.includes(`function ${name}`)).join(", ");
}

function routeHasPatientActor() {
  return routesText.includes("actor: PatientActorDep");
}

function routeHasPatientAudit() {
  return routesText.includes('action="patient.created"') && routesText.includes('action="patient.updated"');
}

function findUsages(variable, text) {
  const usages = [];
  const files = {
    "patient-list": sources.patientList,
    "patient-shell": sources.patientShell,
    "patient-record": sources.patientRecord,
    "patient-status": sources.patientStatus,
    "patient-print": sources.patientPrint,
  };
  for (const [label, path] of Object.entries(files)) {
    if (text === paperText && label !== "patient-print") {
      continue;
    }
    if (text !== paperText && label === "patient-print") {
      continue;
    }
    if (existsSync(join(root, path)) && read(path).includes(variable)) {
      usages.push(path);
    }
  }
  return usages;
}

function isEditable(variable) {
  return schemaClassesWithField(variable).includes("PatientCreate") || schemaClassesWithField(variable).includes("PatientUpdate");
}

function classBody(text, name) {
  const match = text.match(new RegExp(`class ${name}[^:]*:\\n([\\s\\S]*?)(?=\\nclass |\\n\\n[A-Z_]+\\s*=|$)`));
  return match?.[1] ?? "";
}

function objectTypeBody(text, name) {
  const marker = `export type ${name} = {`;
  const start = text.indexOf(marker);
  if (start < 0) {
    return "";
  }
  const bodyStart = start + marker.length;
  let depth = 1;
  for (let index = bodyStart; index < text.length; index += 1) {
    const char = text[index];
    if (char === "{") {
      depth += 1;
    }
    if (char === "}") {
      depth -= 1;
      if (depth === 0) {
        return text.slice(bodyStart, index);
      }
    }
  }
  return "";
}

function aliasBody(text, name) {
  const marker = `export type ${name} =`;
  const start = text.indexOf(marker);
  if (start < 0) {
    return "";
  }
  const nextExport = text.indexOf("\nexport type ", start + marker.length);
  return text.slice(start + marker.length, nextExport < 0 ? text.length : nextExport);
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
      .filter((item) => item.estado !== "OK")
      .map((item) => `${item.variable}: ${item.estado}`),
  };
}

function renderMarkdown(data) {
  const header = [
    "# Variable Map - Dominio Paciente",
    "",
    `Generado: ${data.generated_at}`,
    "",
    "## Resumen",
    "",
    `- Total variables: ${data.summary.total}`,
    ...Object.entries(data.summary.states).map(([state, count]) => `- ${state}: ${count}`),
    "",
    "## Hallazgos críticos",
    "",
    ...(data.summary.critical_findings.length
      ? data.summary.critical_findings.map((item) => `- ${item}`)
      : ["- Sin hallazgos críticos."]),
    "",
    "## Matriz",
    "",
    [
      "Dominio",
      "Variable",
      "Tabla",
      "Modelo SQLAlchemy",
      "Schema Pydantic",
      "Endpoint",
      "OpenAPI",
      "TS Type",
      "API Client",
      "Pantalla",
      "Papel",
      "Permiso",
      "Auditoría",
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
    ].join(" | "),
  ];

  const rows = data.rows.map((row) =>
    [
      row.dominio,
      row.variable,
      row.tabla,
      row.modelo_sqlalchemy,
      row.schema_pydantic,
      row.endpoint,
      row.openapi,
      row.ts_type,
      row.api_client,
      row.pantalla,
      row.papel,
      row.permiso,
      row.auditoria,
      row.estado,
      row.recomendacion,
    ]
      .map(markdownCell)
      .join(" | "),
  );

  return `${[...header, ...rows].join("\n")}\n`;
}

function markdownCell(value) {
  return String(value).replaceAll("\n", " ").replaceAll("|", "\\|");
}
