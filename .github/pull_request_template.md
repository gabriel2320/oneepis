## Resumen

- Objetivo clinico unico:
- Rutas/pantallas afectadas:
- Riesgo principal:

## Anti-inflacion

- [ ] El cambio tiene flujo humano completo o no entra al core.
- [ ] No agrega dashboard/lab/IA como capa paralela al paciente/ficha/papel.
- [ ] IA, si aplica, es opcional, lateral y no escribe/firma ficha.
- [ ] Papel, auditoria, permisos y OpenAPI fueron considerados.
- [ ] Usa los comandos minimos necesarios para validar el cambio.

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

- [ ] `npm run check:api`
- [ ] `npm run check:web`
- [ ] `npm run check:architecture` si toca pantallas, permisos, papel, contratos frontend o trazabilidad
- [ ] `npm run check:contract` si cambia API/OpenAPI
- [ ] `npm run check:e2e` si toca UI/rutas/print
- [ ] `npm run check` para cambios transversales

## Aprendizaje / cierre

- [ ] Deje un test, gate, simplificacion, regla o pantalla menos ambigua.
- [ ] Revise archivos near-limit reportados por `check:size`.
- [ ] No cree documento nuevo si `CURRENT_STATE`, `GOVERNANCE`, `SCREEN_TREE` o `CODEX_PLAN` bastaban.

- Regla aprendida:
- Riesgo residual:
- Codigo simplificado o deuda evitada:
- Proximo cambio minimo:
