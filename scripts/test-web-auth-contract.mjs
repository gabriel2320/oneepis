import assert from "node:assert/strict";

import { findWebAuthContractViolations } from "./check-web-auth-contract.mjs";

assert.deepEqual(
  findWebAuthContractViolations([
    file(
      "apps/web/src/lib/api/client.ts",
      `
const AUTH_SESSION_STORAGE_KEY = "oneepis.auth.session";
const LEGACY_BEARER_STORAGE_KEY = "oneepis.auth.token";

export function setStoredAuthToken(token) {
  if (token) {
    window.localStorage.setItem(AUTH_SESSION_STORAGE_KEY, "active");
    window.localStorage.removeItem(LEGACY_BEARER_STORAGE_KEY);
  }
}
`,
    ),
  ]),
  [],
);

const violations = findWebAuthContractViolations([
  file(
    "apps/web/src/lib/api/client.ts",
    [
      'export const AUTH_TOKEN_STORAGE_KEY = "oneepis.auth.token";',
      "const token = getStoredBearerToken();",
      'return window.localStorage.getItem("oneepis.auth.token");',
      'headers.set("Authorization", `Bearer ${token}`);',
    ].join("\n"),
  ),
]);

assert.equal(violations.length, 4);
assert.match(violations.join("\n"), /bearer token storage keys/);
assert.match(violations.join("\n"), /web storage/);
assert.match(violations.join("\n"), /legacy bearer token/);
assert.match(violations.join("\n"), /HttpOnly cookies/);

console.log("Web auth contract self-test passed.");

function file(path, content) {
  return { path, content };
}
