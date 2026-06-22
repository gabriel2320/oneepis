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

El estado operativo canonico vive en `docs/CURRENT_STATE.md` y el criterio de
decision anti-inflacion en `docs/GOVERNANCE.md`.

Flujo base:

`paciente -> ficha -> evolucion SOAP -> PostgreSQL -> auditoria -> UI`

La UI usa API real por defecto. Los datos demo quedan reservados para `NEXT_PUBLIC_DEMO_MODE=true`.

Superficies principales:

- `/pacientes`: mesa clinica de entrada.
- `/pacientes/[patientId]/ficha`: centro longitudinal.
- `/pacientes/[patientId]/ai-chart`: inteligencia clinica simulada y auditable.
- `/hospitalizacion`: flujo hospitalario minimo.
- `/consulta`: flujo ambulatorio minimo.
- `/print/*`: proyecciones en papel.

El arbol completo de rutas y estado por superficie vive en `docs/SCREEN_TREE.md`.

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
.venv/bin/python -m pip install -e "apps/api[dev]"
```

En Windows/PowerShell usa `.venv\Scripts\python` para los comandos Python
directos. Los scripts npm del repo usan `.venv/bin/python`.

4. Ejecuta migraciones:

```bash
.venv/bin/python -m alembic -c apps/api/alembic.ini upgrade head
```

5. Inicia servicios:

```bash
npm run dev:web
npm run dev:api
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

## IA local

Ollama es opcional. OneEpis debe seguir funcionando con reglas, plantillas y
auditoria aunque Ollama este apagado. Configuracion y modelos sugeridos viven en
`docs/OLLAMA_AND_TOOLS.md`.

## Contrato OpenAPI

Genera el contrato desde FastAPI:

```bash
.venv/bin/python apps/api/scripts/export_openapi.py
```

El archivo estable queda en `packages/contracts/openapi.json`.

## Gates

```bash
npm run check:api
npm run check:web
npm run check:contract
npm run check:e2e
```

El gate completo local es:

```bash
npm run check
```

## Documentos clave

- `docs/CURRENT_STATE.md`: estado operativo.
- `docs/GOVERNANCE.md`: reglas anti-inflacion.
- `docs/PROGRESSIVE_DEVELOPMENT_PLAN.md`: fases AI-Chart.
- `docs/SCREEN_TREE.md`: rutas y superficies.
- `docs/ROADMAP.md`: historial.

Regla central: crecer por modulos clinicos bien nombrados, no por acumulacion indiscriminada de codigo.
