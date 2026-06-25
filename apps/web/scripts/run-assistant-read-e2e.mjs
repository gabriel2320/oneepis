import { spawn } from "node:child_process";
import { existsSync } from "node:fs";
import { fileURLToPath } from "node:url";

const playwrightCli = resolvePlaywrightCli();
const args = [
  playwrightCli,
  "test",
  "tests/e2e/assistant-read-real.spec.ts",
  "tests/e2e/medication-vademecum-real.spec.ts",
  "--project=chromium",
  "--reporter=line",
];
const command = process.execPath;
const child = spawn(command, args, {
  stdio: "inherit",
  env: {
    ...process.env,
    NEXT_PUBLIC_DEMO_MODE: "false",
    PLAYWRIGHT_PORT: process.env.PLAYWRIGHT_ASSISTANT_PORT ?? "3002",
  },
});

child.on("exit", (code, signal) => {
  if (signal) {
    process.kill(process.pid, signal);
    return;
  }
  process.exit(code ?? 1);
});

function resolvePlaywrightCli() {
  const candidates = [
    new URL("../node_modules/@playwright/test/cli.js", import.meta.url),
    new URL("../../../node_modules/playwright/cli.js", import.meta.url),
  ].map((url) => fileURLToPath(url));

  const cli = candidates.find((candidate) => existsSync(candidate));
  if (!cli) {
    console.error("No se encontro el CLI de Playwright. Ejecuta npm install en el workspace web.");
    process.exit(1);
  }
  return cli;
}
