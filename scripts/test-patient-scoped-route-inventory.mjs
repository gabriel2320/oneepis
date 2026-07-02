import assert from "node:assert/strict";

import {
  checkPatientScopedRouteInventory,
  patientScopedOpenApiOperations,
} from "./check-patient-scoped-route-inventory.mjs";

const sampleOpenApi = {
  paths: {
    "/api/v1/patients/{patient_id}/allergies": {
      get: {},
      post: {},
    },
    "/api/v1/patients/{patient_id}/allergies/{allergy_id}": {
      patch: {},
      delete: {},
    },
    "/api/v1/health": {
      get: {},
    },
  },
};

const completeInventory = [
  route("GET", "/api/v1/patients/{patient_id}/allergies"),
  route("POST", "/api/v1/patients/{patient_id}/allergies"),
  route("PATCH", "/api/v1/patients/{patient_id}/allergies/{allergy_id}"),
  route("DELETE", "/api/v1/patients/{patient_id}/allergies/{allergy_id}"),
];

assert.deepEqual(
  patientScopedOpenApiOperations(sampleOpenApi).map(
    (operation) => `${operation.method} ${operation.path_template}`,
  ),
  [
    "DELETE /api/v1/patients/{patient_id}/allergies/{allergy_id}",
    "GET /api/v1/patients/{patient_id}/allergies",
    "PATCH /api/v1/patients/{patient_id}/allergies/{allergy_id}",
    "POST /api/v1/patients/{patient_id}/allergies",
  ],
);

assert.deepEqual(checkPatientScopedRouteInventory(sampleOpenApi, completeInventory), {
  checked: 4,
  errors: [],
});

const missingPatch = checkPatientScopedRouteInventory(
  sampleOpenApi,
  completeInventory.filter((item) => item.method !== "PATCH"),
);
assert.equal(missingPatch.checked, 4);
assert.match(missingPatch.errors.join("\n"), /Missing patient-scoped route inventory/);
assert.match(
  missingPatch.errors.join("\n"),
  /PATCH \/api\/v1\/patients\/\{patient_id\}\/allergies\/\{allergy_id\}/,
);

const staleInventory = checkPatientScopedRouteInventory(sampleOpenApi, [
  ...completeInventory,
  route("GET", "/api/v1/patients/{patient_id}/missing"),
]);
assert.match(staleInventory.errors.join("\n"), /does not exist in OpenAPI/);

console.log("Patient-scoped route inventory self-test passed.");

function route(method, pathTemplate) {
  return {
    method,
    path_template: pathTemplate,
    surface: "allergies",
    patient_scoped: true,
    read_audit_required: method === "GET",
    read_abac_dev_only: method === "GET",
    write_surface: method !== "GET",
    write_abac_dev_only: method !== "GET",
    runtime_write_abac: false,
  };
}
