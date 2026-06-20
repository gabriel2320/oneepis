# OneEpis

Ficha clínica inteligente, bella, rápida y modular.

OneEpis parte con una base limpia:

- **Next.js + Tailwind + shadcn/ui** para una experiencia clínica clara y mantenible.
- **FastAPI + Pydantic** para una API validada, explícita y fácil de entender por agentes IA.
- **PostgreSQL + SQLAlchemy + Alembic** como verdad clínica estructurada y auditable.
- **OpenAPI** como contrato entre frontend y backend.
- **Ollama después** mediante una interfaz de proveedores de IA local, sin acoplar la ficha clínica al modelo.

## Estado Inicial

Este repo contiene un primer esqueleto funcional y deliberadamente acotado:

- workspace clínico en `apps/web`
- API clínica en `apps/api`
- migración inicial Alembic
- contratos exportables en `packages/contracts`
- guía para agentes en `AGENTS.md`
- documentos de arquitectura, seguridad, gobierno y roadmap en `docs`

## Requisitos

- Node.js 20+
- npm 10+
- Python 3.12+
- PostgreSQL 15+ o Docker

## Desarrollo Local

1. Copia variables locales:

```bash
cp .env.example .env
```

2. Levanta PostgreSQL:

```bash
docker compose -f infra/docker-compose.dev.yml up -d
```

3. Instala dependencias web:

```bash
npm install
```

4. Instala la API:

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -e "apps/api[dev]"
```

5. Ejecuta migraciones:

```bash
.venv/Scripts/python -m alembic -c apps/api/alembic.ini upgrade head
```

6. Inicia servicios:

```bash
npm run dev:web
npm run api:dev
```

Web: <http://localhost:3000>  
API: <http://localhost:8000/docs>

## Contrato OpenAPI

Genera el contrato desde FastAPI:

```bash
python apps/api/scripts/export_openapi.py
```

El archivo estable para revisión queda en `packages/contracts/openapi.json`.

## Gobierno Técnico

Antes de ampliar el producto, lee:

- `docs/ARCHITECTURE.md`
- `docs/GOVERNANCE.md`
- `docs/SECURITY_PRIVACY.md`
- `docs/ROADMAP.md`

La regla central: crecer por módulos clínicos bien nombrados, no por acumulación de código.
