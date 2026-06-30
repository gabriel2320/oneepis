import { spawnSync } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { runPython } from "./python-command.mjs";

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const pytestArgs = process.argv.slice(2);

if (pytestArgs.length === 0) {
  console.error("Uso: npm run check:api:target -- apps/api/tests/test_file.py [pytest args]");
  process.exit(1);
}

for (const arg of pytestArgs) {
  if (arg.startsWith("-")) {
    continue;
  }
  const target = arg.split("::", 1)[0].replaceAll("\\", "/");
  if (!target.startsWith("apps/api/tests/")) {
    console.error(`Target no permitido para check:api:target: ${arg}`);
    console.error("Usa solo tests bajo apps/api/tests/. Para validacion completa: npm run check:api.");
    process.exit(1);
  }
}

runPython(["-m", "ruff", "check", "apps/api"]);
runPython(["-m", "pytest", ...pytestArgs]);

const guard = spawnSync("node", ["scripts/check-auth-session-contract.mjs"], {
  cwd: repoRoot,
  stdio: "inherit",
});
if (guard.status !== 0) {
  process.exit(guard.status ?? 1);
}
