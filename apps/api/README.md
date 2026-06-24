# OneEpis API

FastAPI service for the clinical record domain.

## Local Commands

```bash
.venv/bin/python -m pip install -e "apps/api[dev]"
.venv/bin/python -m alembic -c apps/api/alembic.ini upgrade head
npm run dev:api
npm run check:api
.venv/bin/python apps/api/scripts/export_openapi.py
```

En Windows/PowerShell usa `.venv\Scripts\python` para comandos Python
directos. Los scripts npm resuelven Python mediante `scripts/python-command.mjs`.

## Boundaries

- Routes validate and orchestrate request/response flow.
- Repositories own query details.
- Services own domain behavior such as audit events or AI provider selection.
- Models represent persisted clinical truth.
