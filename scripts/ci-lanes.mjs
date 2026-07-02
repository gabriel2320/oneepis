import { spawnSync } from "node:child_process";
import { appendFileSync } from "node:fs";
import { pathToFileURL } from "node:url";

export const laneNames = ["api", "contracts", "web", "e2e", "postgres", "security", "full"];

export function classifyChangedFiles(changedFiles) {
  const lanes = Object.fromEntries(laneNames.map((name) => [name, false]));
  const files = changedFiles.map(normalizePath).filter(Boolean);

  for (const file of files) {
    if (isFullCiPath(file)) {
      lanes.full = true;
    }

    if (isApiPath(file)) {
      lanes.api = true;
      lanes.contracts = true;
    }

    if (isContractPath(file)) {
      lanes.contracts = true;
    }

    if (isWebPath(file)) {
      lanes.web = true;
    }

    if (isE2ePath(file)) {
      lanes.e2e = true;
    }

    if (isPostgresPath(file)) {
      lanes.postgres = true;
    }

    if (isSecurityPath(file)) {
      lanes.security = true;
    }
  }

  return lanes;
}

function main() {
  const options = parseArgs(process.argv.slice(2));
  let changedFiles = options.files;
  let usedFallback = false;

  if (changedFiles.length === 0) {
    const diff = readChangedFilesFromGit(options.base, options.head);
    changedFiles = diff.files;
    usedFallback = !diff.ok;
  }

  const lanes = usedFallback ? fullLanes() : classifyChangedFiles(changedFiles);

  console.log(`Changed files: ${changedFiles.length}`);
  for (const file of changedFiles) {
    console.log(`- ${file}`);
  }
  console.log(`CI lanes: ${laneNames.map((name) => `${name}=${lanes[name]}`).join(", ")}`);

  if (options.githubOutput) {
    writeGithubOutput(lanes);
  }
}

function parseArgs(args) {
  const options = {
    base: process.env.ONEEPIS_CI_BASE_SHA ?? "",
    head: process.env.ONEEPIS_CI_HEAD_SHA ?? "",
    files: [],
    githubOutput: false,
  };

  for (let index = 0; index < args.length; index += 1) {
    const arg = args[index];
    if (arg === "--base") {
      options.base = args[index + 1] ?? "";
      index += 1;
      continue;
    }
    if (arg === "--head") {
      options.head = args[index + 1] ?? "";
      index += 1;
      continue;
    }
    if (arg === "--github-output") {
      options.githubOutput = true;
      continue;
    }
    if (arg === "--files") {
      options.files = args.slice(index + 1);
      break;
    }
  }

  return options;
}

function readChangedFilesFromGit(base, head) {
  if (!usableSha(base) || !usableSha(head)) {
    console.warn("Cannot determine a usable base/head SHA for CI lanes; using full CI.");
    return { ok: false, files: [] };
  }

  const result = spawnSync("git", ["diff", "--name-only", "--no-renames", base, head], {
    encoding: "utf8",
    shell: false,
  });

  if (result.status !== 0 || result.error) {
    console.warn("Cannot diff base/head for CI lanes; using full CI.");
    if (result.error) {
      console.warn(result.error.message);
    }
    if (result.stderr) {
      console.warn(result.stderr.trim());
    }
    return { ok: false, files: [] };
  }

  return {
    ok: true,
    files: result.stdout
      .split(/\r?\n/)
      .map((line) => line.trim())
      .filter(Boolean),
  };
}

function writeGithubOutput(lanes) {
  const outputPath = process.env.GITHUB_OUTPUT;
  if (!outputPath) {
    return;
  }

  const output = laneNames.map((name) => `${name}=${lanes[name]}`).join("\n");
  appendFileSync(outputPath, `${output}\n`);
}

function fullLanes() {
  return Object.fromEntries(laneNames.map((name) => [name, name === "full"]));
}

function normalizePath(filePath) {
  return filePath.replaceAll("\\", "/").replace(/^\.\//, "");
}

function usableSha(value) {
  return /^[0-9a-f]{40}$/i.test(value) && !/^0{40}$/.test(value);
}

function isFullCiPath(file) {
  return (
    file.startsWith(".github/") ||
    file === "package.json" ||
    file === "scripts/ci-lanes.mjs" ||
    file === "scripts/test-ci-lanes.mjs" ||
    file === "scripts/check-ownership.mjs" ||
    file === "scripts/check-toolchain.mjs" ||
    file === "scripts/python-command.mjs"
  );
}

function isApiPath(file) {
  return (
    file.startsWith("apps/api/") ||
    [
      "scripts/check-api.mjs",
      "scripts/check-api-target.mjs",
      "scripts/check-auth-session-contract.mjs",
      "scripts/clinical-access-contract.mjs",
      "scripts/export-openapi.mjs",
    ].includes(file)
  );
}

function isContractPath(file) {
  return (
    file.startsWith("packages/contracts/") ||
    [
      "docs/CODEX_PLAN.md",
      "docs/CURRENT_STATE.md",
      "docs/GOVERNANCE.md",
      "docs/NO_PRODUCTION_CHECKLIST.md",
      "docs/SCREEN_TREE.md",
      "scripts/check-assistant-read-contract.mjs",
      "scripts/check-clinical-auth-contract.mjs",
      "scripts/check-doc-canon.mjs",
      "scripts/check-no-production-checklist.mjs",
      "scripts/check-patient-scoped-read-enforcement.mjs",
    ].includes(file)
  );
}

function isWebPath(file) {
  return (
    file.startsWith("apps/web/") ||
    file.startsWith("packages/contracts/") ||
    file === "package-lock.json"
  );
}

function isE2ePath(file) {
  return (
    file.startsWith("apps/web/tests/e2e/") ||
    file.startsWith("apps/web/src/app/") ||
    file.startsWith("apps/web/src/components/") ||
    file === "apps/web/playwright.config.ts" ||
    file === "apps/web/scripts/run-assistant-read-e2e.mjs" ||
    file === "apps/web/scripts/run-playwright-e2e.mjs" ||
    file === "apps/web/src/lib/screen-capabilities.registry.json" ||
    file === "package-lock.json"
  );
}

function isPostgresPath(file) {
  return (
    file.startsWith("apps/api/alembic/") ||
    file.startsWith("apps/api/src/oneepis_api/db/") ||
    file.startsWith("apps/api/src/oneepis_api/models/") ||
    file === "apps/api/alembic.ini"
  );
}

function isSecurityPath(file) {
  return (
    file === "SECURITY.md" ||
    file === "package-lock.json" ||
    file === "apps/api/pyproject.toml" ||
    file === "apps/web/package.json" ||
    file === "docs/NO_PRODUCTION_CHECKLIST.md" ||
    file === "docs/OLLAMA_AND_TOOLS.md" ||
    file === "docs/SECURITY_PRIVACY.md" ||
    file === "scripts/check-npm-advisories.mjs"
  );
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main();
}
