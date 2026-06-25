import { existsSync } from "node:fs";
import { spawnSync } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const requiredPythonMajor = 3;
const requiredPythonMinor = 12;

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
  const configured = configuredPython();
  if (configured) {
    return requirePythonVersion(configured, "ONEEPIS_PYTHON debe apuntar a Python 3.12.x.");
  }

  const venv = existingVenvPython();
  if (venv) {
    return requirePythonVersion(
      venv,
      "La .venv existente debe recrearse con Python 3.12.x antes de ejecutar scripts.",
    );
  }

  for (const candidate of systemPythonCandidates()) {
    const probed = probePython(candidate);
    if (probed.matchesRequiredVersion) {
      return probed.candidate;
    }
  }
  console.error(
    "No se encontro Python 3.12.x usable. Define ONEEPIS_PYTHON, instala Python 3.12 o crea .venv con Python 3.12.",
  );
  process.exit(1);
}

function configuredPython() {
  if (!process.env.ONEEPIS_PYTHON) {
    return null;
  }
  return candidate(process.env.ONEEPIS_PYTHON, {
    absolutePath: path.isAbsolute(process.env.ONEEPIS_PYTHON),
  });
}

function existingVenvPython() {
  const venvPath = path.join(repoRoot, ".venv");
  if (!existsSync(venvPath)) {
    return null;
  }
  const candidates =
    process.platform === "win32"
      ? [
          candidate(path.join(venvPath, "Scripts", "python.exe"), { absolutePath: true }),
          candidate(path.join(venvPath, "Scripts", "python"), { absolutePath: true }),
        ]
      : [candidate(path.join(venvPath, "bin", "python"), { absolutePath: true })];
  const existing = candidates.find((item) => existsSync(item.command));
  if (existing) {
    return existing;
  }
  console.error("Existe .venv, pero no se encontro su ejecutable Python. Recrea .venv con Python 3.12.");
  process.exit(1);
}

function systemPythonCandidates() {
  return process.platform === "win32"
    ? [candidate("py", { prefixArgs: ["-3.12"] }), candidate("python")]
    : [candidate("python3.12"), candidate("python3"), candidate("python")];
}

function requirePythonVersion(candidateToCheck, message) {
  const probed = probePython(candidateToCheck);
  if (probed.matchesRequiredVersion) {
    return probed.candidate;
  }
  const suffix = probed.version ? ` Version detectada: ${probed.version}.` : "";
  console.error(`${message}${suffix}`);
  process.exit(1);
}

function probePython(candidateToCheck) {
  if (candidateToCheck.absolutePath && !existsSync(candidateToCheck.command)) {
    return {
      candidate: candidateToCheck,
      matchesRequiredVersion: false,
      version: null,
    };
  }
  const probe = spawnSync(candidateToCheck.command, [...candidateToCheck.prefixArgs, "--version"], {
    cwd: repoRoot,
    encoding: "utf8",
    shell: false,
  });
  const output = `${probe.stdout ?? ""}${probe.stderr ?? ""}`.trim();
  const version = output.match(/Python\s+(\d+)\.(\d+)\.(\d+)/)?.[0]?.replace("Python ", "") ?? null;
  const versionParts = version?.split(".").map(Number) ?? [];
  return {
    candidate: { ...candidateToCheck, version },
    matchesRequiredVersion:
      probe.status === 0 &&
      versionParts[0] === requiredPythonMajor &&
      versionParts[1] === requiredPythonMinor,
    version,
  };
}

function candidate(command, options = {}) {
  return {
    command,
    prefixArgs: options.prefixArgs ?? [],
    absolutePath: options.absolutePath ?? false,
  };
}
