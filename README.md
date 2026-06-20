# OneEpis

## Aviso de repositorio publico

Este repositorio esta publico temporalmente para desarrollo temprano. No contiene datos reales y no debe recibir informacion clinica sensible, secretos, dumps, logs con PHI ni documentos de pacientes.

OneEpis no esta listo para produccion sanitaria, no es consejo medico y no debe usarse como software clinico certificado.

Licencia: sin licencia open source por ahora. Ver `LICENSE.md`.

## Stack decidido

- **Next.js + Tailwind + shadcn/ui**: ficha clinica bella, rapida y modular.
- **FastAPI + Pydantic**: API clara, validada y entendible por agentes IA.
- **PostgreSQL + SQLAlchemy + Alembic**: verdad clinica estructurada y auditable.
- **OpenAPI**: contrato limpio entre frontend y backend.
- **Ollama local**: IA controlada, desacoplada de la escritura clinica.

## Estado actual

La fase 1 ya prioriza el flujo real:

`paciente -> ficha -> evolucion SOAP -> PostgreSQL -> auditoria -> UI`

La UI usa API real por defecto. Los datos demo quedan reservados para `NEXT_PUBLIC_DEMO_MODE=true`.

Dominios implementados:

- pacientes
- encuentros clinicos
- evoluciones clinicas SOAP
- estado de ficha, contexto asistencial y problemas activos
- alergias
- medicacion
- signos vitales
- auth local con roles basicos
- permisos clinicos por accion
- auditoria por escritura con actor autenticado, correlation ID y before/after
- estado y borrador IA local via Ollama

Rutas principales:

- `/login`
- `/pacientes`
- `/pacientes/nuevo`
- `/pacientes/[patientId]/estado`
- `/pacientes/[patientId]/ficha`
- `/pacientes/[patientId]/encuentros`
- `/pacientes/[patientId]/encuentros/nuevo`
- `/pacientes/[patientId]/evoluciones`
- `/pacientes/[patientId]/evoluciones/nueva`
- `/pacientes/[patientId]/problemas`
- `/pacientes/[patientId]/problemas/nuevo`
- `/pacientes/[patientId]/alergias`
- `/pacientes/[patientId]/medicacion`
- `/pacientes/[patientId]/signos-vitales`
- `/pacientes/[patientId]/ia`
- `/pacientes/[patientId]/auditoria`
- `/hospitalizacion`
- `/consulta`
- `/configuracion`
- `/print/pacientes/[patientId]/ficha`

## Requisitos

- Node.js 20+
- npm 10+
- Python 3.12+
- PostgreSQL 15+ o Docker
- Ollama opcional para IA local

## Desarrollo local

1. Copia variables locales:

```bash
cp .env.example .env
```

2. Levanta PostgreSQL:

```bash
docker compose -f infra/docker-compose.dev.yml up -d
```

Docker expone PostgreSQL en `localhost:5433` para no chocar con instalaciones locales en `5432`.

3. Instala dependencias:

```bash
npm install
python -m venv .venv
.venv/Scripts/python -m pip install -e "apps/api[dev]"
```

4. Ejecuta migraciones:

```bash
.venv/Scripts/python -m alembic -c apps/api/alembic.ini upgrade head
```

5. Inicia servicios:

```bash
npm run dev:web
npm run api:dev
```

Web: <http://localhost:3000>  
API: <http://localhost:8000/docs>

Credenciales locales iniciales:

- `admin@oneepis.local` / `admin`
- `medico@oneepis.local` / `medico`
- `enfermeria@oneepis.local` / `enfermeria`
- `lector@oneepis.local` / `lector`

Estas credenciales son solo para desarrollo local. Cambia `ONEEPIS_AUTH_SECRET` y
`ONEEPIS_AUTH_LOCAL_USERS` antes de cualquier entorno compartido.

## Ollama local

Variables recomendadas para una estacion con NVIDIA RTX 5070 12 GB:

```bash
ONEEPIS_AI_PROVIDER=ollama
ONEEPIS_OLLAMA_BASE_URL=http://localhost:11434
ONEEPIS_OLLAMA_MODEL=llama3.2:latest
ONEEPIS_OLLAMA_MODEL_SUMMARY=qwen3:8b
ONEEPIS_OLLAMA_MODEL_EMBEDDINGS=bge-m3
```

Estrategia:

- `llama3.2:latest`: modelo rapido de fallback.
- `qwen3:8b`: razonamiento/resumen clinico si latencia y VRAM son aceptables.
- `bge-m3`: embeddings futuros para RAG; no se usa hasta existir modulo RAG.

Guardrails:

- la IA no diagnostica
- la IA no firma
- la IA no escribe ficha sin confirmacion humana
- no se envian datos clinicos a terceros

## Contrato OpenAPI

Genera el contrato desde FastAPI:

```bash
.venv/Scripts/python apps/api/scripts/export_openapi.py
```

El archivo estable queda en `packages/contracts/openapi.json`.

## Gates

```bash
.venv/Scripts/python -m ruff check apps/api
.venv/Scripts/python -m pytest apps/api/tests
npm --workspace apps/web run typecheck
npm --workspace apps/web run lint
npm --workspace apps/web run build
.venv/Scripts/python apps/api/scripts/export_openapi.py
```

## Documentos clave

- `AGENTS.md`
- `SECURITY.md`
- `docs/ARCHITECTURE.md`
- `docs/GOVERNANCE.md`
- `docs/SECURITY_PRIVACY.md`
- `docs/SCREEN_TREE.md`
- `docs/VISUAL_SYSTEM.md`
- `docs/PRINT_SYSTEM.md`
- `docs/OLLAMA_AND_TOOLS.md`
- `docs/PERMISSIONS.md`
- `docs/AUDIT.md`

Regla central: crecer por modulos clinicos bien nombrados, no por acumulacion indiscriminada de codigo.
