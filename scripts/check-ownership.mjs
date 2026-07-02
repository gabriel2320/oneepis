import { existsSync, readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

const ownership = {
  creator: "Gabriel Tesser",
  owner: "EPIONE",
  notice: "OneEpis was created by Gabriel Tesser and is owned by EPIONE.",
  copyright: "Copyright (c) 2026 EPIONE. All rights reserved.",
  license: "UNLICENSED",
};

const requiredTextPhrases = {
  "README.md": [
    ownership.notice,
    ownership.creator,
    ownership.owner,
    ownership.copyright,
    "No license or right of use is granted except by written agreement with EPIONE.",
  ],
  "LICENSE.md": [
    ownership.notice,
    ownership.copyright,
    "No rights are granted",
    "written agreement signed by EPIONE",
    "proprietary to EPIONE",
  ],
  "OWNERSHIP.md": [
    ownership.notice,
    ownership.copyright,
    "The OneEpis source code, documentation, architecture, user interface",
    "No rights are granted to use, copy, modify, distribute, host, deploy",
  ],
  "apps/api/pyproject.toml": [
    ownership.notice,
    ownership.copyright,
    "owner = \"EPIONE\"",
    "creator = \"Gabriel Tesser\"",
  ],
};

const ownershipEncodingCheckedFiles = [
  ...Object.keys(requiredTextPhrases),
  "package.json",
  "apps/web/package.json",
];

const requiredCiJobs = [
  "api",
  "web",
  "contracts",
  "e2e",
  "postgres-alembic",
  "security-report",
];

const errors = [];

for (const [relativePath, phrases] of Object.entries(requiredTextPhrases)) {
  const content = readTextFile(relativePath);
  if (content === null) {
    continue;
  }

  for (const phrase of phrases) {
    requirePhrase(relativePath, content, phrase);
  }
}

for (const relativePath of ownershipEncodingCheckedFiles) {
  const content = readTextFile(relativePath);
  if (content !== null) {
    requireNoCopyrightEncodingDrift(relativePath, content);
  }
}

const rootPackage = readJsonFile("package.json");
const webPackage = readJsonFile("apps/web/package.json");
const packageLock = readJsonFile("package-lock.json");

if (rootPackage) {
  requirePackageOwnership("package.json", rootPackage);
}

if (webPackage) {
  requirePackageOwnership("apps/web/package.json", webPackage);
}

if (packageLock && rootPackage && webPackage) {
  requirePackageLockOwnership(packageLock, rootPackage, webPackage);
}

const ciWorkflow = readTextFile(".github/workflows/ci.yml");
if (ciWorkflow) {
  requirePhrase(".github/workflows/ci.yml", ciWorkflow, "npm run check:ownership");
  requirePhrase(".github/workflows/ci.yml", ciWorkflow, "ownership:");
  for (const jobName of requiredCiJobs) {
    if (!jobDeclaresNeed(ciWorkflow, jobName, "ownership")) {
      errors.push(`${jobName} CI job must declare "needs: ownership"`);
    }
  }
}

if (errors.length > 0) {
  console.error("\nOneEpis ownership check failed.\n");
  for (const error of errors) {
    console.error(`- ${error}`);
  }
  console.error(
    "\nOneEpis must preserve creator and owner attribution: Gabriel Tesser / EPIONE.\n",
  );
  process.exit(1);
}

console.log("OneEpis ownership check passed.");

function readTextFile(relativePath) {
  const absolutePath = path.join(repoRoot, relativePath);

  if (!existsSync(absolutePath)) {
    errors.push(`Missing required ownership file: ${relativePath}`);
    return null;
  }

  return readFileSync(absolutePath, "utf8");
}

function readJsonFile(relativePath) {
  const content = readTextFile(relativePath);
  if (content === null) {
    return null;
  }

  try {
    return JSON.parse(content);
  } catch (error) {
    errors.push(`${relativePath} is not valid JSON: ${error.message}`);
    return null;
  }
}

function requirePhrase(relativePath, content, phrase) {
  if (!content.includes(phrase)) {
    errors.push(`${relativePath} is missing required phrase: "${phrase}"`);
  }
}

function requireNoCopyrightEncodingDrift(relativePath, content) {
  if (content.includes("\u00a9") || content.includes("\u00c2\u00a9")) {
    errors.push(`${relativePath} must use ASCII copyright text: "${ownership.copyright}"`);
  }
}

function requirePackageOwnership(relativePath, manifest) {
  requireJsonValue(relativePath, manifest, "author", ownership.creator);
  requireJsonValue(relativePath, manifest, "license", ownership.license);
  requireJsonValue(relativePath, manifest, "copyright", ownership.copyright);
  requireJsonValue(relativePath, manifest.ownership ?? {}, "creator", ownership.creator);
  requireJsonValue(relativePath, manifest.ownership ?? {}, "owner", ownership.owner);
  requireJsonValue(relativePath, manifest.ownership ?? {}, "notice", ownership.notice);
}

function requirePackageLockOwnership(packageLock, rootPackage, webPackage) {
  const lockRootPackage = packageLock.packages?.[""];
  const lockWebPackage = packageLock.packages?.["apps/web"];

  if (!lockRootPackage) {
    errors.push('package-lock.json is missing packages[""] root metadata');
  } else {
    requireJsonValue("package-lock.json packages[\"\"]", lockRootPackage, "name", rootPackage.name);
    requireJsonValue(
      "package-lock.json packages[\"\"]",
      lockRootPackage,
      "version",
      rootPackage.version,
    );
    requireJsonValue(
      "package-lock.json packages[\"\"]",
      lockRootPackage,
      "license",
      rootPackage.license,
    );
  }

  if (!lockWebPackage) {
    errors.push('package-lock.json is missing packages["apps/web"] workspace metadata');
  } else {
    requireJsonValue(
      "package-lock.json packages[\"apps/web\"]",
      lockWebPackage,
      "name",
      webPackage.name,
    );
    requireJsonValue(
      "package-lock.json packages[\"apps/web\"]",
      lockWebPackage,
      "version",
      webPackage.version,
    );
    requireJsonValue(
      "package-lock.json packages[\"apps/web\"]",
      lockWebPackage,
      "license",
      webPackage.license,
    );
  }
}

function requireJsonValue(relativePath, object, key, expectedValue) {
  if (object[key] !== expectedValue) {
    errors.push(`${relativePath} must set ${key} to ${JSON.stringify(expectedValue)}`);
  }
}

function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function jobDeclaresNeed(workflow, jobName, neededJobName) {
  const jobBlock = new RegExp(
    `^  ${escapeRegExp(jobName)}:\\r?\\n(?<body>(?:    .*\\r?\\n)*)`,
    "m",
  ).exec(workflow)?.groups?.body;

  if (!jobBlock) {
    return false;
  }

  if (new RegExp(`^    needs:\\s*${escapeRegExp(neededJobName)}\\s*$`, "m").test(jobBlock)) {
    return true;
  }

  if (
    new RegExp(`^    needs:\\s*\\[[^\\]]*\\b${escapeRegExp(neededJobName)}\\b[^\\]]*\\]`, "m").test(
      jobBlock,
    )
  ) {
    return true;
  }

  const listNeeds = /^    needs:\r?\n(?<items>(?:      - .+\r?\n)+)/m.exec(jobBlock)?.groups?.items;
  return Boolean(
    listNeeds
      ?.split(/\r?\n/)
      .map((line) => line.replace(/^\s*-\s*/, "").trim())
      .includes(neededJobName),
  );
}
