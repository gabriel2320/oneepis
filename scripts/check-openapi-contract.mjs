import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { runPython } from "./python-command.mjs";

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const openApiPath = path.join(repoRoot, "packages/contracts/openapi.json");
const before = readFileSync(openApiPath, "utf8");

runPython(["apps/api/scripts/export_openapi.py"]);

const after = readFileSync(openApiPath, "utf8");

if (before !== after) {
  console.error("OpenAPI contract drift detected. Run `node scripts/export-openapi.mjs` and commit the result.");
  process.exit(1);
}

console.log("OpenAPI contract guard passed.");
