import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { duplicates, readScreenRegistry } from "./screen-registry.mjs";

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const matrix = readJson("packages/canon/screen-service-matrix.json");
const hisCatalog = readJson("packages/canon/his-service-catalog.json");
const actCatalog = readJson("packages/canon/clinical-act-catalog.json");
const registryRows = readScreenRegistry();
const errors = [];

if (matrix.schemaVersion !== 1) {
  errors.push("schemaVersion must be 1.");
}
if (!Array.isArray(matrix.screenMappings) || matrix.screenMappings.length === 0) {
  errors.push("screenMappings must be a non-empty array.");
}

const mappings = matrix.screenMappings ?? [];
const registryByRoute = new Map(registryRows.map((row) => [row.routePattern, row]));
const mappingByRoute = new Map(mappings.map((mapping) => [mapping.routePattern, mapping]));
const servicesByKey = new Map((hisCatalog.services ?? []).map((service) => [service.key, service]));
const actsByKey = new Map((actCatalog.acts ?? []).map((act) => [act.key, act]));

for (const routePattern of duplicates(mappings.map((mapping) => mapping.routePattern))) {
  errors.push(`Duplicate screen-service mapping route: ${routePattern}.`);
}

for (const row of registryRows.filter((item) => item.writePolicy !== "none")) {
  if (!mappingByRoute.has(row.routePattern)) {
    errors.push(`Writable screen ${row.routePattern} is missing from screen-service matrix.`);
  }
}

for (const mapping of mappings) {
  const row = registryByRoute.get(mapping.routePattern);
  if (!row) {
    errors.push(`Screen-service mapping references unknown route ${mapping.routePattern}.`);
  }
  if (!mapping.routePattern || !mapping.serviceKey || !mapping.backendSurface || !mapping.maturity) {
    errors.push(`Screen-service mapping ${mapping.routePattern || "<missing>"} is missing required fields.`);
  }

  const service = servicesByKey.get(mapping.serviceKey);
  if (!service) {
    errors.push(`Screen ${mapping.routePattern} references unknown serviceKey ${mapping.serviceKey}.`);
    continue;
  }
  if (mapping.backendSurface !== service.backendSurface) {
    errors.push(
      `Screen ${mapping.routePattern} backendSurface ${mapping.backendSurface} does not match service ${service.backendSurface}.`,
    );
  }
  if (mapping.runtimeWriteAbac !== false) {
    errors.push(`Screen ${mapping.routePattern} must not enable runtime write ABAC.`);
  }
  if (mapping.autonomousAiAllowed !== false) {
    errors.push(`Screen ${mapping.routePattern} must not allow autonomous AI.`);
  }

  if (service.writesClinicalRecord && !mapping.clinicalActKey) {
    errors.push(`Clinical write screen ${mapping.routePattern} must declare clinicalActKey.`);
  }
  if (mapping.clinicalActKey) {
    const act = actsByKey.get(mapping.clinicalActKey);
    if (!act) {
      errors.push(`Screen ${mapping.routePattern} references unknown clinicalActKey ${mapping.clinicalActKey}.`);
    } else if (act.serviceKey !== mapping.serviceKey || act.backendSurface !== mapping.backendSurface) {
      errors.push(`Screen ${mapping.routePattern} clinicalActKey does not match its service/backend surface.`);
    }
  }
}

if (errors.length > 0) {
  console.error("Screen-service matrix guard failed.");
  for (const error of errors) {
    console.error(`- ${error}`);
  }
  process.exit(1);
}

console.log(`Screen-service matrix guard passed: ${mappings.length} writable screens checked.`);

function readJson(relativePath) {
  return JSON.parse(readFileSync(path.join(repoRoot, relativePath), "utf8"));
}
