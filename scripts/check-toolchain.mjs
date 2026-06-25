import { spawnSync } from "node:child_process";
import { resolvePython } from "./python-command.mjs";

const expectedNodeMajor = 22;
const expectedNpmVersion = "11.13.0";
const errors = [];

const nodeVersion = process.versions.node;
const nodeMajor = Number(nodeVersion.split(".")[0]);
if (nodeMajor !== expectedNodeMajor) {
  errors.push(`Node ${nodeVersion} detectado; usa Node 22.x para reproducir CI.`);
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
