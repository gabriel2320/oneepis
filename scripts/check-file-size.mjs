import { readdirSync, readFileSync, statSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const defaultLimit = 350;
const nearLimitThreshold = 300;
const scanRoots = ["apps/api/src/oneepis_api", "apps/web/src"];
const extensions = new Set([".py", ".ts", ".tsx"]);
const ignoredSegments = new Set([".next", "node_modules"]);
const exceptions = new Map();

const files = scanRoots.flatMap((root) => walk(path.join(repoRoot, root)));
const offenders = [];
const nearLimitFiles = [];

for (const file of files) {
  const relativePath = toRepoPath(file);
  const exception = exceptions.get(relativePath);
  const limit = exception?.limit ?? defaultLimit;
  const lines = countLines(file);
  if (lines > limit) {
    offenders.push({
      path: relativePath,
      lines,
      limit,
      reason: exception?.reason ?? "Sin excepcion explicita.",
    });
  }
  if (lines >= nearLimitThreshold && lines <= limit) {
    nearLimitFiles.push({
      path: relativePath,
      lines,
      limit,
    });
  }
  if (exception && lines <= defaultLimit) {
    offenders.push({
      path: relativePath,
      lines,
      limit: defaultLimit,
      reason: "La excepcion ya no es necesaria; retirarla.",
    });
  }
}

for (const exceptionPath of exceptions.keys()) {
  if (!files.some((file) => toRepoPath(file) === exceptionPath)) {
    offenders.push({
      path: exceptionPath,
      lines: 0,
      limit: defaultLimit,
      reason: "Excepcion apunta a un archivo inexistente.",
    });
  }
}

if (offenders.length > 0) {
  console.error(`File size guard failed. Default limit: ${defaultLimit} lines.`);
  for (const offender of offenders) {
    console.error(
      `- ${offender.path}: ${offender.lines}/${offender.limit} lines. ${offender.reason}`,
    );
  }
  process.exit(1);
}

console.log(
  `File size guard passed: ${files.length} files scanned, ${exceptions.size} explicit exceptions.`,
);

if (nearLimitFiles.length > 0) {
  console.log(
    `Near-limit files (non-blocking, ${nearLimitThreshold}+ lines; extract before adding behavior):`,
  );
  for (const file of nearLimitFiles.sort((a, b) => b.lines - a.lines)) {
    console.log(`- ${file.path}: ${file.lines}/${file.limit} lines`);
  }
}

function walk(root) {
  return readdirSync(root).flatMap((name) => {
    if (ignoredSegments.has(name)) {
      return [];
    }
    const fullPath = path.join(root, name);
    const stats = statSync(fullPath);
    if (stats.isDirectory()) {
      return walk(fullPath);
    }
    if (!stats.isFile() || !extensions.has(path.extname(name))) {
      return [];
    }
    return [fullPath];
  });
}

function countLines(file) {
  const normalized = readFileSync(file, "utf8").replace(/\r\n/g, "\n").replace(/\r/g, "\n");
  const withoutTrailingNewline = normalized.endsWith("\n") ? normalized.slice(0, -1) : normalized;
  return withoutTrailingNewline.length === 0 ? 0 : withoutTrailingNewline.split("\n").length;
}

function toRepoPath(file) {
  return path.relative(repoRoot, file).split(path.sep).join("/");
}
