import { existsSync } from "node:fs";
import { spawnSync } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

export function runPython(args, options = {}) {
  const python = resolvePython();
  const result = spawnSync(python.command, [...python.prefixArgs, ...args], {
    cwd: repoRoot,
    env: process.env,
    stdio: "inherit",
    shell: false,
    ...options,
  });
  if (result.error) {
    console.error(`No se pudo ejecutar Python: ${result.error.message}`);
    process.exit(1);
  }
  if (typeof result.status === "number" && result.status !== 0) {
    process.exit(result.status);
  }
  if (result.signal) {
    console.error(`Python termino por senal ${result.signal}.`);
    process.exit(1);
  }
}

export function resolvePython() {
  const candidates = pythonCandidates();
  for (const candidate of candidates) {
    if (candidate.absolutePath && !existsSync(candidate.command)) {
      continue;
    }
    const probe = spawnSync(candidate.command, [...candidate.prefixArgs, "--version"], {
      cwd: repoRoot,
      encoding: "utf8",
      shell: false,
    });
    if (probe.status === 0) {
      return candidate;
    }
  }
  console.error(
    "No se encontro Python usable. Define ONEEPIS_PYTHON o crea .venv con Python 3.12.",
  );
  process.exit(1);
}

function pythonCandidates() {
  const configured = process.env.ONEEPIS_PYTHON
    ? [candidate(process.env.ONEEPIS_PYTHON, { absolutePath: path.isAbsolute(process.env.ONEEPIS_PYTHON) })]
    : [];
  const venvCandidates =
    process.platform === "win32"
      ? [
          candidate(path.join(repoRoot, ".venv", "Scripts", "python.exe"), { absolutePath: true }),
          candidate(path.join(repoRoot, ".venv", "Scripts", "python"), { absolutePath: true }),
        ]
      : [candidate(path.join(repoRoot, ".venv", "bin", "python"), { absolutePath: true })];
  const systemCandidates =
    process.platform === "win32"
      ? [candidate("py", { prefixArgs: ["-3"] }), candidate("python")]
      : [candidate("python3"), candidate("python")];
  return [...configured, ...venvCandidates, ...systemCandidates];
}

function candidate(command, options = {}) {
  return {
    command,
    prefixArgs: options.prefixArgs ?? [],
    absolutePath: options.absolutePath ?? false,
  };
}
