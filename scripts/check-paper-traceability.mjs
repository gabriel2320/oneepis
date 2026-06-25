import { readFileSync, readdirSync, statSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const baselinePath = path.join(repoRoot, "docs/audit/paper-traceability-baseline.json");
const scanTargets = [
  path.join(repoRoot, "apps/web/src/components/print"),
  path.join(repoRoot, "apps/web/src/components/clinical/patient-paper-documents.tsx"),
];
const rules = [
  {
    id: "signed-demo-label",
    pattern: /Firmada demo/,
    message: "No usar etiqueta de firma demo en papel.",
  },
  {
    id: "demo-folio",
    pattern: /Folio demo/,
    message: "Usar folio interno, no folio demo.",
  },
  {
    id: "raw-entry-status",
    pattern: /Estado:\s*\{entry\.status\}|entry\.status\s*===\s*"draft"\s*\?\s*"Borrador"\s*:\s*entry\.status/,
    message: "Formatear estados clinicos antes de mostrarlos en papel.",
  },
  {
    id: "signed-status-ternary",
    pattern: /entry\.status\s*===\s*"signed"\s*\?\s*"Firmada/,
    message: "No presentar estado signed como firma legal.",
  },
];

const baseline = JSON.parse(readFileSync(baselinePath, "utf8"));
const allowed = new Set(baseline.allowedViolations ?? []);
const files = scanTargets.flatMap((target) => {
  const stats = statSync(target);
  return stats.isDirectory() ? walk(target) : [target];
});
const violations = [];

for (const file of files) {
  const source = readFileSync(file, "utf8");
  const lines = source.split(/\r?\n/);
  lines.forEach((line, index) => {
    for (const rule of rules) {
      if (rule.pattern.test(line)) {
        const key = `${rule.id}:${toRepoPath(file)}:${index + 1}`;
        violations.push({
          key,
          rule: rule.id,
          path: toRepoPath(file),
          line: index + 1,
          message: rule.message,
        });
      }
    }
  });
}

const newViolations = violations.filter((violation) => !allowed.has(violation.key));

if (newViolations.length > 0) {
  console.error("Paper traceability guard failed.");
  for (const violation of newViolations) {
    console.error(`- ${violation.path}:${violation.line} [${violation.rule}] ${violation.message}`);
  }
  process.exit(1);
}

console.log(
  `Paper traceability guard passed: ${files.length} files scanned, ${violations.length} baseline violations.`,
);

function walk(root) {
  return readdirSync(root).flatMap((name) => {
    const fullPath = path.join(root, name);
    const stats = statSync(fullPath);
    if (stats.isDirectory()) {
      return walk(fullPath);
    }
    return stats.isFile() && /\.(tsx|ts)$/.test(name) ? [fullPath] : [];
  });
}

function toRepoPath(file) {
  return path.relative(repoRoot, file).split(path.sep).join("/");
}
