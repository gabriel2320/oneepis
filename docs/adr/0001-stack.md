# ADR 0001: Stack inicial

## Decisión

Usar:

- Next.js + Tailwind + shadcn/ui para frontend.
- FastAPI + Pydantic para backend.
- PostgreSQL + SQLAlchemy + Alembic para persistencia.
- OpenAPI como contrato.
- Ollama como proveedor local futuro de IA.

## Contexto

La ficha clínica necesita rapidez de desarrollo, trazabilidad, validación fuerte y una superficie entendible para agentes IA.

## Consecuencias

- El contrato OpenAPI será el puente entre frontend y backend.
- Los cambios de datos deben pasar por migraciones Alembic.
- Las funciones de IA se implementarán por interfaz de proveedor para evitar acoplamiento temprano.
