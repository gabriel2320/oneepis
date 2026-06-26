import { spawnSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { resolvePython } from "./python-command.mjs";

const expectedNodeMajor = 22;
const expectedNpmVersion = "11.13.0";
const expectedPackageManager = `npm@${expectedNpmVersion}`;
const errors = [];

const nodeVersion = process.versions.node;
const nodeMajor = Number(nodeVersion.split(".")[0]);
if (nodeMajor !== expectedNodeMajor) {
  errors.push(`Node ${nodeVersion} detectado; usa Node 22.x para reproducir CI.`);
}

const packageManager = packageManagerFromManifest();
if (packageManager !== expectedPackageManager) {
  errors.push(
    `packageManager ${packageManager || "no declarado"} detectado; usa ${expectedPackageManager}.`,
  );
}

const invokedPackageManager = invokedPackageManagerName();
if (invokedPackageManager && invokedPackageManager !== "npm") {
  errors.push(
    `Comando invocado con ${invokedPackageManager}; este repo usa npm. pnpm queda diferido a un PR de migracion dedicado.`,
  );
}

const npmVersion = npmCliVersion();
if (npmVersion !== expectedNpmVersion) {
  errors.push(
    npmVersion
      ? `npm ${npmVersion} detectado; usa npm ${expectedNpmVersion}.`
      : `npm no detectado; usa npm ${expectedNpmVersion}.`,
  );
}

if (errors.length > 0) {
  console.error("Toolchain guard failed.");
  for (const error of errors) {
    console.error(`- ${error}`);
  }
  console.error("");
  console.error("Correccion sugerida:");
  console.error("- nvm install 22 && nvm use 22");
  console.error(`- npm i -g npm@${expectedNpmVersion}`);
  console.error("- npm run check:toolchain");
  process.exit(1);
}

const python = resolvePython();

console.log(
  `Toolchain guard passed: Node ${nodeVersion}, npm ${npmVersion}, Python ${python.version}.`,
);

function npmCliVersion() {
  const userAgentVersion = process.env.npm_config_user_agent?.match(/^npm\/([^\s]+)/)?.[1];
  if (userAgentVersion) {
    return userAgentVersion;
  }
  return commandOutput("npm", ["--version"]);
}

function invokedPackageManagerName() {
  const userAgent = process.env.npm_config_user_agent;
  return userAgent?.match(/^([^/]+)\//)?.[1] ?? "";
}

function packageManagerFromManifest() {
  try {
    const manifest = JSON.parse(readFileSync(new URL("../package.json", import.meta.url), "utf8"));
    return typeof manifest.packageManager === "string" ? manifest.packageManager : "";
  } catch {
    return "";
  }
}

function commandOutput(command, args) {
  const spawnCommand = process.platform === "win32" ? "cmd.exe" : command;
  const spawnArgs =
    process.platform === "win32" ? ["/d", "/s", "/c", [command, ...args].join(" ")] : args;
  const result = spawnSync(spawnCommand, spawnArgs, {
    encoding: "utf8",
    shell: false,
  });
  if (result.status !== 0 || result.error) {
    return "";
  }
  return `${result.stdout}${result.stderr}`.trim();
}
