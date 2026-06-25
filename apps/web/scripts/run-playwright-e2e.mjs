import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";

const playwrightCli = fileURLToPath(new URL("../../../node_modules/playwright/cli.js", import.meta.url));
const env = { ...process.env };
delete env.NO_COLOR;

const child = spawn(process.execPath, [playwrightCli, "test", ...process.argv.slice(2)], {
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
