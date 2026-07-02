import { readdirSync, readFileSync, statSync } from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const sourceRoot = path.join(repoRoot, "apps/web/src");
const checkedExtensions = new Set([".js", ".jsx", ".ts", ".tsx"]);

const forbiddenPatterns = [
  {
    pattern: /\bAUTH_TOKEN_STORAGE_KEY\b/,
    message: "remove bearer token storage keys from the web client",
  },
  {
    pattern: /\bgetStoredBearerToken\b/,
    message: "do not read bearer tokens from web storage",
  },
  {
    pattern:
      /localStorage\.getItem\([^)]*(?:oneepis\.auth\.token|AUTH_TOKEN_STORAGE_KEY|LEGACY_BEARER_STORAGE_KEY)[^)]*\)/,
    message: "do not read the legacy bearer token from localStorage",
  },
  {
    pattern: /headers\.set\(\s*["']Authorization["']\s*,\s*`Bearer\b/,
    message: "apiFetch must rely on HttpOnly cookies instead of setting bearer headers",
  },
  {
    pattern: /headers\.set\(\s*["']Authorization["']\s*,\s*["']Bearer\s+/,
    message: "apiFetch must rely on HttpOnly cookies instead of setting bearer headers",
  },
];

export function findWebAuthContractViolations(files) {
  const violations = [];
  for (const file of files) {
    const lines = file.content.split(/\r?\n/);
    for (const [index, line] of lines.entries()) {
      for (const check of forbiddenPatterns) {
        if (check.pattern.test(line)) {
          violations.push(`${file.path}:${index + 1} ${check.message}.`);
        }
      }
    }
  }
  return violations;
}

function main() {
  const files = walk(sourceRoot).map((filePath) => ({
    path: toRepoPath(filePath),
    content: readFileSync(filePath, "utf8"),
  }));
  const violations = findWebAuthContractViolations(files);

  if (violations.length > 0) {
    console.error("Web auth contract guard failed.");
    for (const violation of violations) {
      console.error(`- ${violation}`);
    }
    process.exit(1);
  }

  console.log(`Web auth contract guard passed: ${files.length} source files checked.`);
}

function walk(root) {
  return readdirSync(root).flatMap((name) => {
    const fullPath = path.join(root, name);
    const stats = statSync(fullPath);
    if (stats.isDirectory()) {
      return walk(fullPath);
    }
    if (!stats.isFile() || !checkedExtensions.has(path.extname(fullPath))) {
      return [];
    }
    return [fullPath];
  });
}

function toRepoPath(file) {
  return path.relative(repoRoot, file).split(path.sep).join("/");
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main();
}
