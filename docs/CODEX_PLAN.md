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
- PR-041: Doctrina anti-inflacion como regla de gobierno canonica.
- PR-042: Gates oficiales y pocos comandos raiz.
- PR-043: Dieta backend de pacientes sin cambiar OpenAPI.
- PR-044: Retiro del barrel temporal frontend de paciente.
- PR-045: Papel serio como gate clinico con smoke print.
- PR-046: Preparar proximo crecimiento clinico minimo.
- PR-047: Alinear guias y gates oficiales.
- PR-048: Retiro de legacy demo frontend.
- PR-049: Dieta UI sin cambiar conducta.
- PR-050: Dieta IA backend sin cambiar endpoints.
- PR-051: Dieta tests API por dominio sin reducir cobertura.
- PR-052: Hoja diaria hospitalizada minima con PostgreSQL, API, auditoria, UI y print.
- PR-053: Edicion UI dedicada para hoja diaria hospitalizada.
- PR-054: Estado `draft/closed` y bloqueo de edicion en hoja diaria.
- PR-055: Reglas de fecha/encuentro para hoja diaria hospitalizada.
- PR-056: Rondas hospitalarias de lectura desde datos existentes.
- PR-057: Dieta tests hospitalizacion sin cambiar comportamiento.
- PR-058: Papel hospitalario de ronda desde datos existentes.
- PR-059: Fecha clinica local para hoja diaria hospitalizada.
- PR-060: Politica de indicaciones y receta sin producto nuevo.
- PR-061: Indicacion hospitalaria minima como borrador gobernado.
- PR-062: Consulta ambulatoria minima sobre encuentro y SOAP existentes.
- PR-063: Guardia local anti-contaminacion y entrada `/pacientes` como mesa clinica sobria.
- PR-064: Endurecimiento post-auditoria de print, build offline-safe y scripts Python reproducibles.

## Proximo bloque propuesto

Auditoria posterior a PR-064: la base clinica, consulta minima y papel quedaron
endurecidos. El siguiente bloque debe mejorar la experiencia visual sin crear
dashboard nuevo, dependencia nueva ni clinica core incompleta.

- PR-065: Temas visuales v2 y mesa `/pacientes`.
  - Pulir tokens, jerarquia visual y densidad clinica sin dependencia nueva.
  - Sostener paciente/ficha/papel como centro.
  - No crear dashboard nuevo.
- PR-066: Dieta de print antes de sumar mas papel.
  - Separar `clinical-print.tsx` si sigue creciendo.
  - Mantener rutas print como proyecciones, no fuente de verdad.
- PR-067: Evaluar read-model hospitalario.
  - Solo si rondas o indicaciones empiezan a duplicar consultas desde frontend.
  - No crear dashboard nuevo.

## Reglas no negociables

- No usar datos reales.
- No crear datos demo realistas.
- No implementar diagnostico autonomo.
- No firmar ni escribir ficha desde IA.
- No imprimir receta clinica valida sin firma, folio, actor, fecha clinica y permisos claros.
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

## Proximo crecimiento clinico

Despues del core sobrio, hospitalizacion puede crecer solo con una pieza por vez:

- hoja diaria o indicaciones, no ambas juntas
- PostgreSQL antes que estado inventado en UI
- API, permisos, auditoria y OpenAPI en el mismo PR
- UI minima con estados loading/error/empty
- print si el flujo clinico naturalmente termina en papel

Si una pieza no cumple ese flujo completo, queda fuera del core.
