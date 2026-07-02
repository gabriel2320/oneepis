import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const hisCatalog = readJson("packages/canon/his-service-catalog.json");
const actCatalog = readJson("packages/canon/clinical-act-catalog.json");
const errors = [];

if (actCatalog.schemaVersion !== 1) {
  errors.push("schemaVersion must be 1.");
}
if (!Array.isArray(actCatalog.acts) || actCatalog.acts.length === 0) {
  errors.push("acts must be a non-empty array.");
}

const services = hisCatalog.services ?? [];
const serviceKeys = new Set(services.map((service) => service.key));
const writeServiceKeys = services
  .filter((service) => service.writesClinicalRecord)
  .map((service) => service.key);
const acts = actCatalog.acts ?? [];

for (const key of duplicates(acts.map((act) => act.key))) {
  errors.push(`Duplicate clinical act key: ${key}.`);
}

for (const serviceKey of writeServiceKeys) {
  if (!acts.some((act) => act.serviceKey === serviceKey && act.writesClinicalRecord)) {
    errors.push(`Clinical write service ${serviceKey} has no mapped clinical act.`);
  }
}

for (const act of acts) {
  if (!act.key || !act.label || !act.serviceKey || !act.backendSurface || !act.maturity) {
    errors.push(`Clinical act ${act.key || "<missing>"} is missing required fields.`);
  }
  if (!serviceKeys.has(act.serviceKey)) {
    errors.push(`Clinical act ${act.key} references unknown serviceKey ${act.serviceKey}.`);
  }
  if (act.writesClinicalRecord !== true || act.requiresHumanActor !== true) {
    errors.push(`Clinical act ${act.key} must be human-authored clinical write intent.`);
  }
  if (act.autonomousAiAllowed !== false) {
    errors.push(`Clinical act ${act.key} must not allow autonomous AI.`);
  }
}

if (errors.length > 0) {
  console.error("Clinical act catalog guard failed.");
  for (const error of errors) {
    console.error(`- ${error}`);
  }
  process.exit(1);
}

console.log(`Clinical act catalog guard passed: ${acts.length} acts checked.`);

function readJson(relativePath) {
  return JSON.parse(readFileSync(path.join(repoRoot, relativePath), "utf8"));
}

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
