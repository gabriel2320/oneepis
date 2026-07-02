import { readdirSync, readFileSync, statSync } from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const routeRoot = path.join(repoRoot, "apps/api/src/oneepis_api/api/v1/routes");

export function findAuditSnapshotAllowlistViolations(files) {
  const errors = [];
  for (const file of files) {
    const content = file.content;
    for (const call of auditSnapshotCalls(content)) {
      const args = splitTopLevelArgs(call.args);
      if (args.length < 2 || args[1].trim() === "") {
        errors.push(`${file.path}:${call.line} audit_snapshot must include an explicit fields allowlist.`);
      }
    }
  }
  return errors;
}

function main() {
  const files = walk(routeRoot).map((filePath) => ({
    path: toRepoPath(filePath),
    content: readFileSync(filePath, "utf8"),
  }));
  const errors = findAuditSnapshotAllowlistViolations(files);

  if (errors.length > 0) {
    console.error("Audit snapshot allowlist guard failed.");
    for (const error of errors) {
      console.error(`- ${error}`);
    }
    process.exit(1);
  }

  console.log(`Audit snapshot allowlist guard passed: ${files.length} route files checked.`);
}

function auditSnapshotCalls(content) {
  const calls = [];
  const marker = "audit_snapshot(";
  let index = content.indexOf(marker);
  while (index >= 0) {
    const openParenIndex = index + "audit_snapshot".length;
    const closeParenIndex = matchingParenIndex(content, openParenIndex);
    if (closeParenIndex < 0) {
      calls.push({
        args: "",
        line: lineNumber(content, index),
      });
      index = content.indexOf(marker, index + marker.length);
      continue;
    }
    calls.push({
      args: content.slice(openParenIndex + 1, closeParenIndex),
      line: lineNumber(content, index),
    });
    index = content.indexOf(marker, closeParenIndex + 1);
  }
  return calls;
}

function matchingParenIndex(content, openParenIndex) {
  let depth = 0;
  let quote = null;
  let escaped = false;

  for (let index = openParenIndex; index < content.length; index += 1) {
    const char = content[index];
    if (quote) {
      if (escaped) {
        escaped = false;
        continue;
      }
      if (char === "\\") {
        escaped = true;
        continue;
      }
      if (char === quote) {
        quote = null;
      }
      continue;
    }
    if (char === "\"" || char === "'") {
      quote = char;
      continue;
    }
    if (char === "(" || char === "[" || char === "{") {
      depth += 1;
      continue;
    }
    if (char === ")" || char === "]" || char === "}") {
      depth -= 1;
      if (depth === 0 && char === ")") {
        return index;
      }
    }
  }
  return -1;
}

function splitTopLevelArgs(argsText) {
  const args = [];
  let depth = 0;
  let quote = null;
  let escaped = false;
  let start = 0;

  for (let index = 0; index < argsText.length; index += 1) {
    const char = argsText[index];
    if (quote) {
      if (escaped) {
        escaped = false;
        continue;
      }
      if (char === "\\") {
        escaped = true;
        continue;
      }
      if (char === quote) {
        quote = null;
      }
      continue;
    }
    if (char === "\"" || char === "'") {
      quote = char;
      continue;
    }
    if (char === "(" || char === "[" || char === "{") {
      depth += 1;
      continue;
    }
    if (char === ")" || char === "]" || char === "}") {
      depth -= 1;
      continue;
    }
    if (char === "," && depth === 0) {
      args.push(argsText.slice(start, index).trim());
      start = index + 1;
    }
  }

  const finalArg = argsText.slice(start).trim();
  if (finalArg) {
    args.push(finalArg);
  }
  return args;
}

function walk(root) {
  return readdirSync(root).flatMap((name) => {
    const fullPath = path.join(root, name);
    const stats = statSync(fullPath);
    if (stats.isDirectory()) {
      return walk(fullPath);
    }
    if (!stats.isFile() || !name.endsWith(".py")) {
      return [];
    }
    return [fullPath];
  });
}

function toRepoPath(file) {
  return path.relative(repoRoot, file).split(path.sep).join("/");
}

function lineNumber(content, index) {
  return content.slice(0, index).split(/\r?\n/).length;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main();
}
