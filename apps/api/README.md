# OneEpis API

FastAPI service for the clinical record domain.

## Local Commands

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -e "apps/api[dev]"
.venv/bin/python -m alembic -c apps/api/alembic.ini upgrade head
npm run dev:api
npm run check:api
npm run export:openapi
```

En Windows/PowerShell crea `.venv` con `py -3.12 -m venv .venv` y usa
`.venv\Scripts\python` para comandos Python directos. Los scripts npm resuelven
Python mediante `scripts/python-command.mjs` y exigen Python 3.12.x.

## Boundaries

- Routes validate and orchestrate request/response flow.
- Repositories own query details.
- Services own domain behavior such as audit events or AI provider selection.
- Models represent persisted clinical truth.
