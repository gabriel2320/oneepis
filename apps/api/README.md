# OneEpis API

FastAPI service for the clinical record domain.

## Local Commands

```bash
python -m pip install -e "apps/api[dev]"
python -m alembic -c apps/api/alembic.ini upgrade head
python -m uvicorn oneepis_api.main:app --reload --app-dir apps/api/src
python -m pytest apps/api/tests
python apps/api/scripts/export_openapi.py
```

## Boundaries

- Routes validate and orchestrate request/response flow.
- Repositories own query details.
- Services own domain behavior such as audit events or AI provider selection.
- Models represent persisted clinical truth.
