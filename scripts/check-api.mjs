import { runPython } from "./python-command.mjs";

runPython(["-m", "ruff", "check", "apps/api"]);
runPython(["-m", "pytest", "apps/api/tests"]);
