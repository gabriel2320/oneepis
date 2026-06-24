#!/usr/bin/env node
const { existsSync } = require("node:fs");
const { join } = require("node:path");
const { spawnSync } = require("node:child_process");

const candidates =
  process.platform === "win32"
    ? [
        join(".venv", "Scripts", "python.exe"),
        join(".venv", "Scripts", "python"),
        "py",
        "python",
      ]
    : [join(".venv", "bin", "python"), "python3", "python"];

const python = candidates.find((candidate) => {
  if (candidate.includes(".venv")) {
    return existsSync(candidate);
  }
  return true;
});

const result = spawnSync(python, process.argv.slice(2), {
  stdio: "inherit",
  shell: false,
});

if (result.error) {
  console.error(result.error.message);
  process.exit(1);
}

process.exit(result.status ?? 1);
