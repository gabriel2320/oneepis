import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { protectedClinicalRoutePrefixes } from "./clinical-access-contract.mjs";

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const openApiPath = path.join(repoRoot, "packages/contracts/openapi.json");
const openApi = JSON.parse(readFileSync(openApiPath, "utf8"));

const methods = new Set(["get", "post", "put", "patch", "delete"]);
const errors = [];
let checked = 0;

for (const [routePath, operations] of Object.entries(openApi.paths ?? {})) {
  if (!protectedClinicalRoutePrefixes.some((prefix) => routePath.startsWith(prefix))) {
    continue;
  }
  for (const [method, operation] of Object.entries(operations)) {
    if (!methods.has(method)) {
      continue;
    }
    checked += 1;
    if (!hasAuthorizationHeader(operation)) {
      errors.push(`${method.toUpperCase()} ${routePath} must declare Authorization header`);
    }
  }
}

if (checked === 0) {
  errors.push("Clinical auth contract guard did not find protected clinical routes.");
}

if (errors.length > 0) {
  console.error("Clinical auth contract guard failed.");
  for (const error of errors) {
    console.error(`- ${error}`);
  }
  process.exit(1);
}

console.log(`Clinical auth contract guard passed: ${checked} protected operations checked.`);

function hasAuthorizationHeader(operation) {
  return operation.parameters?.some(
    (parameter) => parameter.in === "header" && parameter.name === "Authorization",
  );
}
