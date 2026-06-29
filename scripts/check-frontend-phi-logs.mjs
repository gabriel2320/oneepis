import { readdirSync, readFileSync, statSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const sourceRoot = path.join(repoRoot, "apps/web/src");
const checkedExtensions = new Set([".js", ".jsx", ".ts", ".tsx"]);
const forbiddenConsole = /\bconsole\.(?:debug|error|info|log|warn)\s*\(/;
const violations = [];

for (const filePath of walk(sourceRoot)) {
  if (!checkedExtensions.has(path.extname(filePath))) {
    continue;
  }
  const source = readFileSync(filePath, "utf8");
  const lines = source.split(/\r?\n/);
  for (const [index, line] of lines.entries()) {
    if (forbiddenConsole.test(line)) {
      violations.push(`${relative(filePath)}:${index + 1}`);
    }
  }
}

if (violations.length > 0) {
  console.error("Frontend PHI log guard failed. Do not log from apps/web/src.");
  for (const violation of violations) {
    console.error(`- ${violation}`);
  }
  console.error("Use user-visible error states or backend audit events instead of console output.");
  process.exit(1);
}

console.log("Frontend PHI log guard passed: no console logging in apps/web/src.");

function walk(directory) {
  const entries = [];
  for (const entry of readdirSync(directory)) {
    const fullPath = path.join(directory, entry);
    const stats = statSync(fullPath);
    if (stats.isDirectory()) {
      entries.push(...walk(fullPath));
      continue;
    }
    if (stats.isFile()) {
      entries.push(fullPath);
    }
  }
  return entries;
}

function relative(filePath) {
  return path.relative(repoRoot, filePath);
}
