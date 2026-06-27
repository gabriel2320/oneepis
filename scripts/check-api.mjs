import { runPython } from "./python-command.mjs";
import { spawnSync } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

runPython(["-m", "ruff", "check", "apps/api"]);
runPython(["-m", "pytest", "apps/api/tests"]);

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const guard = spawnSync("node", ["scripts/check-auth-session-contract.mjs"], {
  cwd: repoRoot,
  stdio: "inherit",
});
if (guard.status !== 0) {
  process.exit(guard.status ?? 1);
}
