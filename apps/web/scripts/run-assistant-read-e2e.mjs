import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";

const playwrightCli = fileURLToPath(new URL("../../../node_modules/playwright/cli.js", import.meta.url));
const args = [
  playwrightCli,
  "test",
  "tests/e2e/assistant-read-real.spec.ts",
  "tests/e2e/audit-events-real.spec.ts",
  "tests/e2e/medication-vademecum-real.spec.ts",
  "tests/e2e/clinical-permissions-real.spec.ts",
  "--project=chromium",
  "--reporter=line",
];
const command = process.execPath;
const env = { ...process.env };
delete env.NO_COLOR;
env.NEXT_PUBLIC_DEMO_MODE = "false";
env.PLAYWRIGHT_PORT = process.env.PLAYWRIGHT_ASSISTANT_PORT ?? "3002";

const child = spawn(command, args, {
  stdio: "inherit",
  env,
});

child.on("exit", (code, signal) => {
  if (signal) {
    process.kill(process.pid, signal);
    return;
  }
  process.exit(code ?? 1);
});
