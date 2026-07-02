import assert from "node:assert/strict";

import { findAuditSnapshotAllowlistViolations } from "./check-audit-snapshot-allowlists.mjs";

const okFiles = [
  file(
    "apps/api/src/oneepis_api/api/v1/routes/patient_allergies.py",
    `
def create_allergy():
    record_audit_event(
        after=audit_snapshot(allergy, ALLERGY_AUDIT_FIELDS),
    )
`,
  ),
  file(
    "apps/api/src/oneepis_api/api/v1/routes/patient_vitals.py",
    `
def update_vital():
    before = audit_snapshot(
        vital,
        audit_fields,
    )
`,
  ),
];

assert.deepEqual(findAuditSnapshotAllowlistViolations(okFiles), []);

const violations = findAuditSnapshotAllowlistViolations([
  file(
    "apps/api/src/oneepis_api/api/v1/routes/patient_core.py",
    `
def unsafe_patient_update():
    before = audit_snapshot(patient)
`,
  ),
]);

assert.equal(violations.length, 1);
assert.match(violations[0], /patient_core.py:3/);
assert.match(violations[0], /explicit fields allowlist/);

console.log("Audit snapshot allowlist self-test passed.");

function file(path, content) {
  return { path, content };
}
