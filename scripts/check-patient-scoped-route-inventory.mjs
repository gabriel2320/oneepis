import { readFileSync } from "node:fs";
import { spawnSync } from "node:child_process";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

import { resolvePython } from "./python-command.mjs";

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const defaultOpenApiPath = path.join(repoRoot, "packages/contracts/openapi.json");
const openApiMethods = new Set(["get", "post", "patch", "delete"]);

export function checkPatientScopedRouteInventory(openApi, inventory) {
  const errors = [];
  const operations = patientScopedOpenApiOperations(openApi);
  const inventoryKeys = new Set(inventory.map(routeKey));
  const openApiKeys = new Set(operations.map(routeKey));

  for (const operation of operations) {
    if (!inventoryKeys.has(routeKey(operation))) {
      errors.push(
        `Missing patient-scoped route inventory classification: ${routeKey(operation)}`,
      );
    }
  }

  for (const route of inventory) {
    if (!route.path_template.includes("{patient_id}")) {
      continue;
    }
    if (!openApiKeys.has(routeKey(route))) {
      errors.push(
        `Patient-scoped route inventory entry does not exist in OpenAPI: ${routeKey(route)}`,
      );
    }
    if (route.runtime_write_abac !== false) {
      errors.push(`${routeKey(route)} must keep runtime_write_abac=false`);
    }
  }

  if (operations.length === 0) {
    errors.push("No OpenAPI operations with {patient_id} were checked.");
  }

  return {
    checked: operations.length,
    errors,
  };
}

export function patientScopedOpenApiOperations(openApi) {
  const operations = [];
  for (const [pathTemplate, pathOperations] of Object.entries(openApi.paths ?? {})) {
    if (!pathTemplate.includes("{patient_id}")) {
      continue;
    }
    for (const [method, operation] of Object.entries(pathOperations ?? {})) {
      if (!openApiMethods.has(method) || !operation) {
        continue;
      }
      operations.push({
        method: method.toUpperCase(),
        path_template: pathTemplate,
      });
    }
  }
  return operations.sort((left, right) => routeKey(left).localeCompare(routeKey(right)));
}

function main() {
  const openApi = JSON.parse(readFileSync(defaultOpenApiPath, "utf8"));
  const inventory = loadInventoryFromPython();
  const result = checkPatientScopedRouteInventory(openApi, inventory);

  if (result.errors.length > 0) {
    console.error("Patient-scoped route inventory OpenAPI guard failed.");
    for (const error of result.errors) {
      console.error(`- ${error}`);
    }
    process.exit(1);
  }

  console.log(
    `Patient-scoped route inventory OpenAPI guard passed: ${result.checked} operations checked.`,
  );
}

function loadInventoryFromPython() {
  const python = resolvePython();
  const result = spawnSync(
    python.command,
    [...python.prefixArgs, "apps/api/scripts/export_patient_scoped_route_inventory.py"],
    {
      cwd: repoRoot,
      env: process.env,
      encoding: "utf8",
      shell: false,
    },
  );

  if (result.error) {
    console.error(`Could not export patient-scoped route inventory: ${result.error.message}`);
    process.exit(1);
  }
  if (result.status !== 0) {
    console.error(result.stderr.trim());
    process.exit(result.status ?? 1);
  }

  return JSON.parse(result.stdout);
}

function routeKey(route) {
  return `${route.method.toUpperCase()} ${route.path_template}`;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main();
}
