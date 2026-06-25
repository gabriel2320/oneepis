#!/usr/bin/env node
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";

const root = process.cwd();
const openApiPath = "packages/contracts/openapi.json";

const contracts = [
  {
    schema: "PatientRead",
    tsType: "Patient",
    tsFile: "apps/web/src/lib/type-contracts/patient.ts",
  },
  {
    schema: "ClinicalEncounterRead",
    tsType: "ClinicalEncounter",
    tsFile: "apps/web/src/lib/type-contracts/clinical-record.ts",
  },
  {
    schema: "ClinicalEntryRead",
    tsType: "ClinicalEntry",
    tsFile: "apps/web/src/lib/type-contracts/clinical-record.ts",
  },
  {
    schema: "ClinicalEventRead",
    tsType: "ClinicalEvent",
    tsFile: "apps/web/src/lib/type-contracts/clinical-record.ts",
  },
  {
    schema: "VitalSignRead",
    tsType: "VitalSign",
    tsFile: "apps/web/src/lib/type-contracts/clinical-record.ts",
  },
  {
    schema: "AllergyRead",
    tsType: "Allergy",
    tsFile: "apps/web/src/lib/type-contracts/clinical-record.ts",
  },
  {
    schema: "MedicationRead",
    tsType: "Medication",
    tsFile: "apps/web/src/lib/type-contracts/clinical-record.ts",
  },
  {
    schema: "ActiveProblemRead",
    tsType: "ActiveProblem",
    tsFile: "apps/web/src/lib/type-contracts/clinical-record.ts",
  },
  {
    schema: "PatientRecordSnapshot",
    tsType: "PatientRecordSnapshot",
    tsFile: "apps/web/src/lib/type-contracts/clinical-record.ts",
  },
  {
    schema: "HospitalBedRead",
    tsType: "HospitalBed",
    tsFile: "apps/web/src/lib/type-contracts/hospitalization.ts",
  },
  {
    schema: "HospitalDailySheetRead",
    tsType: "HospitalDailySheet",
    tsFile: "apps/web/src/lib/type-contracts/hospitalization.ts",
  },
  {
    schema: "HospitalIndicationRead",
    tsType: "HospitalIndication",
    tsFile: "apps/web/src/lib/type-contracts/hospitalization.ts",
  },
];
const knownMissingFields = {
  PatientRead: ["contact_phone", "document_id_hash", "email", "emergency_contact"],
  ClinicalEntryRead: ["extra_data"],
  MedicationRead: [
    "catalog_item_id",
    "created_at",
    "dose",
    "dose_check_snapshot",
    "dose_override_reason",
    "ended_on",
    "frequency",
    "id",
    "name",
    "patient_id",
    "route",
    "started_on",
    "status",
    "updated_at",
  ],
};

const openapi = JSON.parse(read(openApiPath));
const rows = contracts.map(compareContract);
const failedRows = rows.filter((row) => row.unexpected_missing_in_ts.length > 0);
const report = {
  generated_at: new Date().toISOString(),
  scope: "openapi_to_frontend_type_contracts",
  summary: {
    contracts_checked: rows.length,
    drifted_contracts: rows.filter((row) => row.missing_in_ts.length > 0).length,
    unexpected_drifted_contracts: failedRows.length,
  },
  rows,
};

write("reports/contract-drift-map.json", `${JSON.stringify(report, null, 2)}\n`);
write("reports/contract-drift-map.md", renderMarkdown(report));

if (failedRows.length > 0) {
  console.error(`Contract drift check failed: ${failedRows.length} contract(s) drifted.`);
  for (const row of failedRows) {
    console.error(
      `- ${row.schema} -> ${row.ts_type}: missing ${row.unexpected_missing_in_ts.join(", ")}`,
    );
  }
  process.exit(1);
}

const knownDriftRows = rows.filter((row) => row.known_missing_in_ts.length > 0);
if (knownDriftRows.length > 0) {
  console.warn(`Contract drift baseline: ${knownDriftRows.length} contract(s) have known drift.`);
}
console.log(`Contract drift check passed: ${rows.length} frontend contracts, no unexpected drift.`);

function compareContract(contract) {
  const schema = openapi.components?.schemas?.[contract.schema];
  if (!schema) {
    return {
      schema: contract.schema,
      ts_type: contract.tsType,
      ts_file: contract.tsFile,
      openapi_fields: [],
      ts_fields: [],
      missing_in_ts: ["OPENAPI_SCHEMA_NOT_FOUND"],
      known_missing_in_ts: [],
      unexpected_missing_in_ts: ["OPENAPI_SCHEMA_NOT_FOUND"],
      extra_in_ts: [],
    };
  }
  const tsFields = extractTsFields(contract.tsFile, contract.tsType);
  const openapiFields = Object.keys(schema.properties ?? {}).sort();
  const tsFieldSet = new Set(tsFields);
  const openapiFieldSet = new Set(openapiFields);
  const knownMissing = knownMissingFields[contract.schema] ?? [];
  const missing = openapiFields.filter((field) => !tsFieldSet.has(field));
  return {
    schema: contract.schema,
    ts_type: contract.tsType,
    ts_file: contract.tsFile,
    openapi_fields: openapiFields,
    ts_fields: tsFields,
    missing_in_ts: missing,
    known_missing_in_ts: missing.filter((field) => knownMissing.includes(field)),
    unexpected_missing_in_ts: missing.filter((field) => !knownMissing.includes(field)),
    extra_in_ts: tsFields.filter((field) => !openapiFieldSet.has(field)),
  };
}

function extractTsFields(tsFile, tsType) {
  const source = read(tsFile);
  const match = source.match(new RegExp(`export type ${tsType}\\s*=\\s*\\{([\\s\\S]*?)\\n\\};`));
  if (!match) {
    return [];
  }
  return [...match[1].matchAll(/^\s*([A-Za-z_][A-Za-z0-9_]*)\??:/gm)]
    .map((item) => item[1])
    .sort();
}

function renderMarkdown(data) {
  const lines = [
    "# Contract Drift Map - OneEpis",
    "",
    `Generado: ${data.generated_at}`,
    "",
    "## Resumen",
    "",
    `- Contratos revisados: ${data.summary.contracts_checked}`,
    `- Contratos con drift: ${data.summary.drifted_contracts}`,
    `- Contratos con drift no esperado: ${data.summary.unexpected_drifted_contracts}`,
    "",
    "## Matriz",
    "",
    "OpenAPI schema | TS type | TS file | Campos OpenAPI | Campos TS | Faltan en TS | Drift conocido | Drift no esperado | Extra en TS",
    "--- | --- | --- | --- | --- | --- | --- | --- | ---",
    ...data.rows.map((row) =>
      [
        row.schema,
        row.ts_type,
        row.ts_file,
        row.openapi_fields.join(", "),
        row.ts_fields.join(", "),
        row.missing_in_ts.join(", ") || "OK",
        row.known_missing_in_ts.join(", ") || "OK",
        row.unexpected_missing_in_ts.join(", ") || "OK",
        row.extra_in_ts.join(", ") || "OK",
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
