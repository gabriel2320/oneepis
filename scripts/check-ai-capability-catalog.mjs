import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { allowedAiProfiles, duplicates, readScreenRegistry } from "./screen-registry.mjs";

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const catalog = readJson("packages/canon/ai-capability-catalog.json");
const registryRows = readScreenRegistry();
const errors = [];

if (catalog.schemaVersion !== 1) {
  errors.push("schemaVersion must be 1.");
}
if (!Array.isArray(catalog.capabilities) || catalog.capabilities.length === 0) {
  errors.push("capabilities must be a non-empty array.");
}
if (!Array.isArray(catalog.profileCoverage) || catalog.profileCoverage.length === 0) {
  errors.push("profileCoverage must be a non-empty array.");
}

const capabilities = catalog.capabilities ?? [];
const coverage = catalog.profileCoverage ?? [];
const capabilitiesByKey = new Map(capabilities.map((capability) => [capability.key, capability]));
const usedProfiles = new Set(
  registryRows.map((row) => row.aiProfile).filter((profile) => profile && profile !== "none"),
);
const coveredProfiles = new Set(coverage.map((item) => item.aiProfile));

for (const key of duplicates(capabilities.map((capability) => capability.key))) {
  errors.push(`Duplicate AI capability key: ${key}.`);
}
for (const profile of duplicates(coverage.map((item) => item.aiProfile))) {
  errors.push(`Duplicate AI profile coverage: ${profile}.`);
}

for (const profile of usedProfiles) {
  if (!coveredProfiles.has(profile)) {
    errors.push(`AI profile ${profile} is used by a screen but missing from capability catalog.`);
  }
}

for (const coverageItem of coverage) {
  if (!allowedAiProfiles.has(coverageItem.aiProfile) || coverageItem.aiProfile === "none") {
    errors.push(`Unknown or invalid AI profile coverage: ${coverageItem.aiProfile}.`);
  }
  if (!Array.isArray(coverageItem.capabilityKeys) || coverageItem.capabilityKeys.length === 0) {
    errors.push(`AI profile ${coverageItem.aiProfile} must list capabilityKeys.`);
    continue;
  }
  for (const key of coverageItem.capabilityKeys) {
    if (!capabilitiesByKey.has(key)) {
      errors.push(`AI profile ${coverageItem.aiProfile} references unknown capability ${key}.`);
    }
  }
}

for (const capability of capabilities) {
  if (!capability.key || !capability.label || !capability.runtimeMode || !capability.outputPolicy) {
    errors.push(`AI capability ${capability.key || "<missing>"} is missing required fields.`);
  }
  if (!Array.isArray(capability.actions) || capability.actions.length === 0) {
    errors.push(`AI capability ${capability.key} must declare actions.`);
  }
  if (capability.externalProviderAllowed !== false) {
    errors.push(`AI capability ${capability.key} must not allow external providers.`);
  }
  if (capability.autonomousWriteAllowed !== false) {
    errors.push(`AI capability ${capability.key} must not allow autonomous writes.`);
  }
  if (capability.writesClinicalRecord !== false) {
    errors.push(`AI capability ${capability.key} must not write the clinical record.`);
  }
  if (capability.requiresHumanReview !== true) {
    errors.push(`AI capability ${capability.key} must require human review.`);
  }
}

const patchCoverage = coverage.find((item) => item.aiProfile === "patch");
if (patchCoverage) {
  const hasPatchProposal = patchCoverage.capabilityKeys.some((key) => {
    const capability = capabilitiesByKey.get(key);
    return capability?.clinicalPatchAllowed === true && capability?.autonomousWriteAllowed === false;
  });
  if (!hasPatchProposal) {
    errors.push("AI profile patch must include a human-confirmed patch proposal capability.");
  }
}

if (errors.length > 0) {
  console.error("AI capability catalog guard failed.");
  for (const error of errors) {
    console.error(`- ${error}`);
  }
  process.exit(1);
}

console.log(`AI capability catalog guard passed: ${capabilities.length} capabilities checked.`);

function readJson(relativePath) {
  return JSON.parse(readFileSync(path.join(repoRoot, relativePath), "utf8"));
}
