# Arquitectura

OneEpis usa un monorepo pequeño para mantener juntas las piezas que cambian en pareja.

## Capas

- `apps/web`: experiencia clínica, componentes shadcn/ui, composición visual y consumo de OpenAPI.
- `apps/api`: dominio clínico, validación Pydantic, persistencia SQLAlchemy, migraciones Alembic y auditoría.
- `packages/contracts`: contrato OpenAPI exportado desde FastAPI.
- `infra`: dependencias locales de desarrollo.

## Principios

- El backend define la verdad clínica.
- El frontend optimiza la lectura y captura, pero no inventa estructuras clínicas no representadas en la API.
- La IA es un módulo auxiliar, no una autoridad clínica.
- Cada feature nueva debe entrar por un contrato explícito: modelo, schema, ruta, prueba y documentación mínima.

## Flujo de Datos

```mermaid
flowchart LR
  Clinician["Usuario clínico"] --> Web["Next.js clinical workspace"]
  Web --> Contract["OpenAPI contract"]
  Contract --> API["FastAPI + Pydantic"]
  API --> Domain["Servicios de dominio"]
  Domain --> DB["PostgreSQL"]
  Domain --> Audit["Audit events"]
  Domain --> AI["AI provider interface"]
  AI -. futuro .-> Ollama["Ollama local"]
```

## Dominios Iniciales

- Pacientes: datos mínimos y trazables.
- Ficha clínica: entradas clínicas, signos vitales, alergias y medicación.
- Auditoría: eventos de cambios relevantes.
- IA: contratos de resumen/asistencia, inicialmente deshabilitados o determinísticos.
