import { existsSync, readdirSync, readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const docsDir = path.join(repoRoot, "docs");

const errors = [];

const forbiddenDocs = [
  /^ONEEPIS_REPORT_\d{4}-\d{2}-\d{2}\.md$/,
  /^SCREEN_CANON_REVIEW\.md$/,
];

for (const entry of readdirSync(docsDir)) {
  if (forbiddenDocs.some((pattern) => pattern.test(entry))) {
    errors.push(
      `docs/${entry} duplicates live state. Use CURRENT_STATE, CODEX_PLAN or ROADMAP instead.`,
    );
  }
}

const currentState = readDoc("CURRENT_STATE.md");
const codexPlan = readDoc("CODEX_PLAN.md");
const governance = readDoc("GOVERNANCE.md");

assertMaxLines("docs/CURRENT_STATE.md", currentState, 180);
assertMaxLines("docs/CODEX_PLAN.md", codexPlan, 140);

requireText(
  currentState,
  "Al cerrar cada PR que cambie plan, avance, estado, seguridad o no-produccion",
  "CURRENT_STATE must include the PR-end doc sync rule.",
);
requireText(
  codexPlan,
  "Sincronizacion Documental Obligatoria",
  "CODEX_PLAN must tell agents how to sync live docs.",
);
requireText(
  governance,
  "Sincronizacion Documental Obligatoria",
  "GOVERNANCE must define canonical doc synchronization.",
);
requireText(
  codexPlan,
  "Ultimo PR sincronizado:",
  "CODEX_PLAN must expose the latest synchronized PR number.",
);

const requiredLiveDocs = [
  "docs/CURRENT_STATE.md",
  "docs/CODEX_PLAN.md",
  "docs/NO_PRODUCTION_CHECKLIST.md",
  "docs/GOVERNANCE.md",
];

for (const docPath of requiredLiveDocs) {
  if (!existsSync(path.join(repoRoot, docPath))) {
    errors.push(`Missing live documentation file: ${docPath}`);
  }
}

if (errors.length > 0) {
  console.error("Documentation canon guard failed.");
  for (const error of errors) {
    console.error(`- ${error}`);
  }
  process.exit(1);
}

console.log("Documentation canon guard passed.");

function readDoc(name) {
  return readFileSync(path.join(docsDir, name), "utf8");
}

function assertMaxLines(label, content, maxLines) {
  const lineCount = content.trimEnd().split("\n").length;
  if (lineCount > maxLines) {
    errors.push(`${label} has ${lineCount} lines; max is ${maxLines}.`);
  }
}

function requireText(content, text, message) {
  if (!content.includes(text)) {
    errors.push(message);
  }
}
