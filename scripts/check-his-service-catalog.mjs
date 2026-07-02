import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const catalogPath = path.join(repoRoot, "packages/canon/his-service-catalog.json");
const catalog = JSON.parse(readFileSync(catalogPath, "utf8"));

const requiredClinicalSurfaces = [
  "clinical_entries",
  "clinical_events",
  "clinical_orders",
  "vital_signs",
  "clinical_risks",
  "medications",
  "allergies",
  "active_problems",
  "encounters",
  "appointments",
  "lab_panels_results",
  "hospital_daily_sheets",
  "hospital_indications",
];
const errors = [];

if (catalog.schemaVersion !== 1) {
  errors.push("schemaVersion must be 1.");
}
if (!Array.isArray(catalog.services) || catalog.services.length === 0) {
  errors.push("services must be a non-empty array.");
}

const services = catalog.services ?? [];
const keys = services.map((service) => service.key);
for (const key of duplicates(keys)) {
  errors.push(`Duplicate HIS service key: ${key}.`);
}

for (const surface of requiredClinicalSurfaces) {
  const service = services.find((item) => item.backendSurface === surface);
  if (!service) {
    errors.push(`Missing HIS service for clinical surface ${surface}.`);
    continue;
  }
  if (!service.patientScoped || !service.writesClinicalRecord) {
    errors.push(`Clinical surface ${surface} must be patient-scoped and write-classified.`);
  }
  if (service.maturity !== "dev_write_abac") {
    errors.push(`Clinical surface ${surface} must stay at dev_write_abac maturity.`);
  }
}

for (const service of services) {
  if (!service.key || !service.label || !service.domain || !service.maturity) {
    errors.push(`HIS service ${service.key || "<missing>"} is missing required text fields.`);
  }
  if (service.runtimeWriteAbac !== false) {
    errors.push(`HIS service ${service.key} must not enable runtime write ABAC.`);
  }
  if (service.externalAiAllowed !== false) {
    errors.push(`HIS service ${service.key} must not allow external AI.`);
  }
}

if (errors.length > 0) {
  console.error("HIS service catalog guard failed.");
  for (const error of errors) {
    console.error(`- ${error}`);
  }
  process.exit(1);
}

console.log(`HIS service catalog guard passed: ${services.length} services checked.`);

function duplicates(values) {
  const seen = new Set();
  const duplicateValues = new Set();
  for (const value of values) {
    if (seen.has(value)) {
      duplicateValues.add(value);
    }
    seen.add(value);
  }
  return [...duplicateValues].sort();
}
