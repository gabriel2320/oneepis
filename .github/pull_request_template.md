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

## Canon budget

- [ ] Toca como maximo 1 documento canonico.
- [ ] Toca como maximo 1 registry/contrato.
- [ ] Toca como maximo 1 test/gate nuevo o modificado.
- [ ] Si excede el presupuesto, explica que dano clinico, seguridad rota, setup roto o claim falso evita.
- [ ] No abre PR separado de reconciliacion posterior.
- [ ] No edita manualmente tablas generadas; usa el generador correspondiente.

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
- [ ] `npm run check:contract` si cambia API/OpenAPI
- [ ] `npm run check:e2e` si toca UI/rutas/print
- [ ] `npm run check` para cambios transversales

## Aprendizaje / cierre

- [ ] Deje un test, gate, simplificacion, regla o pantalla menos ambigua.
- [ ] Revise archivos near-limit reportados por `check:size`.
- [ ] No cree documento nuevo si `CURRENT_STATE`, `GOVERNANCE`, `SCREEN_TREE` o `CODEX_PLAN` bastaban.
- [ ] Si es docs-only, corrige seguridad, claim clinico/legal, setup roto, permisos contradictorios o produccion/no-produccion.

- Regla aprendida:
- Riesgo residual:
- Codigo simplificado o deuda evitada:
- Proximo cambio minimo:
