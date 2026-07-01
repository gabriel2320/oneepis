# OneEpis

> **Ownership Notice**
>
> OneEpis was created by Gabriel Tesser and is owned by EPIONE.
> Copyright © 2026 EPIONE. All rights reserved.
> Original creator: Gabriel Tesser.
> Commercial and copyright owner: EPIONE.
> No license or right of use is granted except by written agreement with EPIONE.

## Aviso de repositorio publico

Este repositorio esta publico temporalmente para desarrollo temprano. No contiene datos reales y no debe recibir informacion clinica sensible, secretos, dumps, logs con PHI ni documentos de pacientes.

OneEpis no esta listo para produccion sanitaria, no es consejo medico y no debe usarse como software clinico certificado.

Licencia: propietaria, sin licencia open source por ahora. Ver `LICENSE.md` y `OWNERSHIP.md`.

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

- `/home`: mapa fisico del hospital post-login.
- `/pacientes`: mesa clinica interna para seleccionar ficha cuando un servicio lo requiere.
- `/pacientes/[patientId]/ficha`: centro longitudinal.
- `/pacientes/[patientId]/ai-chart`: inteligencia clinica simulada y auditable.
- `/hospitalizacion`: flujo hospitalario minimo.
- `/consulta`: flujo ambulatorio minimo.
- `/print/*`: proyecciones en papel.

El arbol completo de rutas y estado por superficie vive en `docs/SCREEN_TREE.md`.

## Requisitos

- Node.js 22 (`.nvmrc` y `.node-version`)
- npm 11.13.0 (`packageManager`)
- Python 3.12.x
- PostgreSQL 15+ o Docker
- Ollama opcional para IA local

Package manager oficial: npm. pnpm fue evaluado y queda diferido a un PR de
migracion dedicado para no mezclar cambio funcional clinico con cambio de
lockfile, bootstrap, CI y auditoria de dependencias.

## Desarrollo local

0. Alinea toolchain:

```bash
nvm install 22
nvm use 22
npm i -g npm@11.13.0
npm run check:toolchain
```

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
python3.12 -m venv .venv
.venv/bin/python -m pip install -e "apps/api[dev]"
```

En Windows/PowerShell crea el entorno con `py -3.12 -m venv .venv` y usa
`.venv\Scripts\python` para comandos Python directos. Los scripts npm resuelven
Python de forma cross-platform mediante `scripts/python-command.mjs` y fallan si
`.venv` no usa Python 3.12.x.

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

## Ubuntu sin Cursor

OneEpis no depende de Cursor GUI. En Ubuntu, usa la terminal como flujo canonico:

```bash
nvm use
npm i -g npm@11.13.0
npm run bootstrap:ubuntu
```

El bootstrap verifica `node`, `npm`, `python3.12`, `docker` y `docker compose`,
copia `.env.example` a `.env` si falta, levanta PostgreSQL, crea `.venv`,
instala dependencias Python y npm, ejecuta migraciones y corre:

```bash
npm run check:toolchain
npm run check:api
npm run check:web
npm run check:contract
```

Para desarrollo diario despues del bootstrap:

```bash
npm run dev:api
npm run dev:web
```

## Windows PowerShell

En Windows, instala Node.js 22, npm 11.13.0, Python 3.12 y Docker Desktop.
Despues ejecuta:

```powershell
npm i -g npm@11.13.0
npm run bootstrap:windows
```

Si falta Python 3.12, instala con `py install 3.12` antes del bootstrap.

Para desarrollo diario:

```powershell
npm run dev:api
npm run dev:web
```

## IA local

Ollama es opcional. OneEpis debe seguir funcionando con reglas, plantillas y
auditoria aunque Ollama este apagado. Configuracion y modelos sugeridos viven en
`docs/OLLAMA_AND_TOOLS.md`.

## Contrato OpenAPI

Verifica que el contrato versionado coincida con FastAPI:

```bash
npm run check:contract
```

Para regenerar explicitamente el archivo estable en `packages/contracts/openapi.json`:

```bash
npm run export:openapi
```

## Gates

```bash
npm run check:toolchain
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
- `OWNERSHIP.md`: declaracion canonica de creador, titularidad y derechos reservados.

Regla central: crecer por modulos clinicos bien nombrados, no por acumulacion indiscriminada de codigo.
