import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const pyprojectPath = path.join(repoRoot, "apps/api/pyproject.toml");
const lockPath = path.join(repoRoot, "apps/api/requirements.lock");

const pyproject = readFileSync(pyprojectPath, "utf8");
const lockText = readFileSync(lockPath, "utf8");
const lockPackages = parseLock(lockText);
const directPackages = [
  ...dependencyArray(pyproject, "dependencies"),
  ...dependencyArray(pyproject, "dev"),
].map(packageName);

const errors = [];

for (const [lineNumber, line] of lockText.split(/\r?\n/).entries()) {
  if (!line.trim() || line.startsWith("#")) {
    continue;
  }
  if (!/^[A-Za-z0-9_.-]+==[^=\s]+$/.test(line)) {
    errors.push(`apps/api/requirements.lock:${lineNumber + 1} must use exact name==version pins.`);
  }
}

for (const name of directPackages) {
  if (!lockPackages.has(normalizeName(name))) {
    errors.push(`Direct Python dependency ${name} from pyproject.toml is missing in requirements.lock.`);
  }
}

if (errors.length > 0) {
  console.error("Python lock guard failed.");
  for (const error of errors) {
    console.error(`- ${error}`);
  }
  process.exit(1);
}

console.log(`Python lock guard passed: ${lockPackages.size} pinned packages checked.`);

function dependencyArray(text, key) {
  const pattern =
    key === "dev"
      ? /\[project\.optional-dependencies\][\s\S]*?dev\s*=\s*\[(?<body>[\s\S]*?)\]/m
      : /\[project\][\s\S]*?dependencies\s*=\s*\[(?<body>[\s\S]*?)\]/m;
  const body = pattern.exec(text)?.groups?.body ?? "";
  return [...body.matchAll(/"([^"]+)"/g)].map((match) => match[1]);
}

function packageName(requirement) {
  return requirement.split(/[<>=!~\[]/, 1)[0];
}

function parseLock(text) {
  const packages = new Set();
  for (const line of text.split(/\r?\n/)) {
    const match = /^([A-Za-z0-9_.-]+)==/.exec(line.trim());
    if (match) {
      packages.add(normalizeName(match[1]));
    }
  }
  return packages;
}

function normalizeName(name) {
  return name.toLowerCase().replaceAll("_", "-");
}
