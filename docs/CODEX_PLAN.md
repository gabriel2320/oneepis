# Codex Plan

## Regla madre

Codex debe construir OneEpis por ladrillos clinicos verificables:

```text
1 rama
1 objetivo clinico
1 PR pequeno
tests
OpenAPI actualizado si cambia API
docs minimas
sin datos reales
```

## Programa activo

Mesa clinica viva con Ollama first-class y seguridad local:

- PR-018: Ollama first-class local.
- PR-019: IA acoplada a ficha paciente.
- PR-020: Patient Clinical Shell.
- PR-021: Ficha resumen tipo mesa clinica.
- PR-022: Una accion = una pantalla.
- PR-023: SOAP con asistente Ollama.
- PR-024: Modo papel v2.
- PR-025: QA visual + Ollama.
- PR-026: Auth local + roles + actor auditado.
- PR-027: Permisos clinicos por accion.
- PR-028: Auditoria fuerte con correlation ID y before/after.
- PR-029: Estado de ficha, contexto asistencial y problemas activos auditados.
- PR-030: Pantalla gobernada para editar estado clinico y contexto asistencial.
- PR-031: Encuentros clinicos auditados como puente para consulta y hospitalizacion.
- PR-032: Evoluciones SOAP vinculables a encuentros clinicos.
- PR-033: Tablero hospitalario simple desde encuentros de hospitalizacion activos.
- PR-034: Camas hospitalarias estructuradas con asignacion auditada.
- PR-035: Administracion UI de camas y creacion dedicada.
- PR-036: Asignacion de ingresos activos a camas existentes.
- PR-037: CI real con gates backend, frontend, OpenAPI y Playwright.
- PR-038: Seguridad fail-closed fuera de development.
- PR-039: Dieta inicial de pantallas paciente sin cambiar comportamiento.
- PR-040: Playwright fresco por defecto para evitar servidores locales obsoletos.

## Reglas no negociables

- No usar datos reales.
- No crear datos demo realistas.
- No implementar diagnostico autonomo.
- No firmar ni escribir ficha desde IA.
- No agregar dependencias sin justificacion.
- No hacer PR gigante.
- No dejar TypeScript roto.
- No dejar endpoints sin tests.
- Toda escritura clinica debe crear `audit_event`.
- Toda escritura clinica debe tener actor autenticado; `X-OneEpis-Actor` es solo fallback dev explicito.
- Toda accion protegida debe estar en `docs/PERMISSIONS.md` y tener test backend.
- Toda escritura debe quedar trazable por `correlation_id` y request path.
- Todo cambio de API debe actualizar `packages/contracts/openapi.json`.
- Frontend no debe usar `demoRecords` salvo `NEXT_PUBLIC_DEMO_MODE=true`.

## Loop de trabajo

1. Leer estado actual y docs relevantes.
2. Confirmar que el working tree esta limpio o entender cambios existentes.
3. Implementar solo el objetivo del PR.
4. Ejecutar gates.
5. Actualizar docs de estado si cambia comportamiento.
6. Entregar resumen, pruebas y riesgos.

## Criterio de producto

OneEpis debe sentirse como mesa clinica viva:

- paciente al centro
- cabecera clinica persistente
- navegacion obvia
- evoluciones SOAP simples
- auditoria visible
- modo papel serio
- IA local silenciosa, util y trazable
