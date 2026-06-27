import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const openApiPath = path.join(repoRoot, "packages/contracts/openapi.json");
const openApi = JSON.parse(readFileSync(openApiPath, "utf8"));

const authRoutes = [
  ["/api/v1/auth/login", "post"],
  ["/api/v1/auth/logout", "post"],
  ["/api/v1/auth/refresh", "post"],
  ["/api/v1/auth/me", "get"],
];

const protectedPatientReads = [
  "/api/v1/patients/{patient_id}",
  "/api/v1/patients/{patient_id}/record",
];

function hasAuthorizationHeader(operation) {
  return operation.parameters?.some(
    (parameter) => parameter.in === "header" && parameter.name === "Authorization",
  );
}

for (const [routePath, method] of authRoutes) {
  const operation = openApi.paths?.[routePath]?.[method];
  if (!operation) {
    throw new Error(`Auth session contract missing ${method.toUpperCase()} ${routePath}`);
  }
}

for (const routePath of protectedPatientReads) {
  const operation = openApi.paths?.[routePath]?.get;
  if (!operation) {
    throw new Error(`Auth session contract missing GET ${routePath}`);
  }
  if (!hasAuthorizationHeader(operation)) {
    throw new Error(`GET ${routePath} must declare Authorization header in OpenAPI`);
  }
}

console.log(
  `Auth session contract guard passed: ${authRoutes.length} auth routes and ${protectedPatientReads.length} protected patient reads checked.`,
);
