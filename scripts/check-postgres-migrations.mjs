import { runPython } from "./python-command.mjs";

if (!process.env.ONEEPIS_DATABASE_URL) {
  console.error("ONEEPIS_DATABASE_URL debe apuntar a PostgreSQL para validar migraciones.");
  process.exit(1);
}

runPython(["-m", "alembic", "-c", "apps/api/alembic.ini", "upgrade", "head"]);
