import { runPython } from "./python-command.mjs";

runPython([
  "-m",
  "uvicorn",
  "oneepis_api.main:app",
  "--reload",
  "--app-dir",
  "apps/api/src",
]);
