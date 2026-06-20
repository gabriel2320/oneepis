## Resumen

- Objetivo clinico unico:
- Rutas/pantallas afectadas:
- Riesgo principal:

## Cambios clinicos

- [ ] No usa datos reales ni PHI.
- [ ] No agrega datos demo realistas.
- [ ] No deja botones muertos.
- [ ] Toda escritura clinica crea auditoria.

## IA local / Ollama

- [ ] No diagnostica.
- [ ] No firma.
- [ ] No escribe ficha automaticamente.
- [ ] Respuestas IA son borrador y requieren revision humana.
- [ ] Tests mockean Ollama si se toca IA.

## API / OpenAPI

- [ ] No cambia API.
- [ ] Cambia API y actualiza `packages/contracts/openapi.json`.

## Datos y migraciones

- [ ] No requiere migracion.
- [ ] Incluye migracion Alembic y prueba.

## Pruebas

- [ ] `.venv/Scripts/python -m ruff check apps/api`
- [ ] `.venv/Scripts/python -m pytest apps/api/tests`
- [ ] `npm --workspace apps/web run typecheck`
- [ ] `npm --workspace apps/web run lint`
- [ ] `npm --workspace apps/web run build`
- [ ] `python apps/api/scripts/export_openapi.py` si cambia API
