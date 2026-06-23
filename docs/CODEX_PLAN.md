# Codex Plan

Guia breve para cambios hechos por agentes. El historial vive en
`docs/ROADMAP.md`; el estado operativo vive en `docs/CURRENT_STATE.md`; la
decision anti-inflacion vive en `docs/GOVERNANCE.md`.

## Regla madre

Construir OneEpis por ladrillos clinicos verificables:

```text
1 objetivo clinico
1 cambio acotado
tests/gates
OpenAPI actualizado si cambia API
docs minimas
sin datos reales
```

## No negociable

- No usar datos reales ni datos demo realistas.
- No implementar diagnostico autonomo.
- No firmar ni escribir ficha desde IA.
- No imprimir receta clinica valida sin firma, folio, actor, fecha clinica y permisos claros.
- No agregar dependencias sin justificacion.
- No dejar TypeScript roto.
- No dejar endpoints sin tests.
- Toda escritura clinica debe tener actor, permisos, auditoria y `correlation_id`.
- Todo cambio de API debe actualizar `packages/contracts/openapi.json`.
- Los contratos Assistant Read deben pasar `scripts/check-assistant-read-contract.mjs` hasta reemplazar tipos manuales por generacion completa.
- Frontend no debe usar datos demo salvo `NEXT_PUBLIC_DEMO_MODE=true`.
- Ninguna ruta clinica o print con ID en URL puede mostrar un primer registro como fallback.
- Ningun archivo clinico nuevo debe superar 350 lineas sin excepcion explicita en `scripts/check-file-size.mjs`.

## Loop de trabajo

1. Leer `docs/CURRENT_STATE.md`, `docs/GOVERNANCE.md` y el doc del dominio tocado.
2. Entender cambios existentes en el working tree sin revertir trabajo ajeno.
3. Implementar solo el objetivo.
4. Ejecutar gates proporcionales al cambio.
5. Actualizar docs solo si cambia comportamiento o decision.
6. Entregar resumen, pruebas y riesgos.

## Criterio de producto

OneEpis debe sentirse como mesa clinica viva:

- paciente al centro
- ficha y papel como proyecciones clinicas serias
- auditoria visible
- IA local util, silenciosa y trazable
- dashboards, chat libre y modulos incompletos fuera del core

## AI-Chart despues de v0.4

AI-Chart esta separado en `apps/web/src/components/clinical/ai-chart/`.
Reglas para nuevos cambios:

- mantener `patient-ai-chart-pages.tsx` como orquestador
- no agregar bloques UI inline grandes en la pagina
- preferir componentes existentes antes de crear rutas nuevas
- mantener subpaneles de AI-Chart bajo presupuesto; si crecen, extraer secciones antes de sumar conducta
- no sumar reglas clinicas al frontend; si una regla interpreta datos, vive en API
- todo nuevo output debe tener fuente, faltante/limite, accion humana y auditoria
- no tocar Ollama/API externa durante `PROG-PATIENT-CORE-01`
- crecimiento IA conversacional entra primero por el `AI Bridge` compartido; no crear Route Handlers paralelos sin necesidad
- propuestas de escritura deben converger a `ClinicalPatch` revisable antes de persistir

Foco actual:

- `v0.4-assistant-read` queda cerrado, tagueado y con walkthrough humano aprobado
- el avance activo es `PROG-PATIENT-CORE-01`
- priorizar nucleo paciente tradicional, antecedentes leidos desde fuentes existentes y laboratorio sobrio
- si se toca Context Builder, debe ser solo mantenimiento o explicacion puntual, no nueva IA
- mantener `ClinicalPatch` simple: `clinical_event` y `evolution`
- no aceptar `ClinicalPatch` sin confirmacion humana obligatoria ni evoluciones que no sean borrador
- tratar estados de propuesta como flujo local + auditoria hasta decidir persistencia propia
- no crear editor generico de patches
- no extraer `packages/ai-core` hasta que haya duplicacion real
- no ampliar a RAG, documentos ni IA externa antes de completar nucleo paciente tradicional

Cola de ejecucion automatica:

1. Cerrar `PROG-DIET-01`: primera dieta quirurgica ya saco `patient-list-pages.tsx` del near-limit.
2. `PROG-PATIENT-CORE-POLISH-01`: pulir nucleo paciente de solo lectura, sin entidad nueva.
3. `PROG-AMB-PRECONSULTA-PERMISSIONS-00`: decision docs-only sobre `enfermeria`/`admision`.
4. `PROG-CLINICAL-RISK-01`: implementar riesgos clinicos solo si el contrato sigue aprobado.

Reglas para avanzar:

- partir desde `main` limpio
- una rama y un PR por bloque
- no mezclar contrato docs-only con implementacion
- no agregar UI amplia antes de contrato, permisos, auditoria y pruebas
- preconsulta debe seguir reutilizando cita, encuentro, signos y eventos antes de crear tabla o endpoint compuesto
- la implementacion minima usa permisos existentes `medico/admin/dev`; no prometer flujo `admision` o `enfermeria` sin PR backend
- riesgos clinicos deben mostrar fuente, severidad, estado y accion humana; no scores automaticos ni `ClinicalPatch`
- no ampliar IA durante esta cola
- usar la tabla operativa de `docs/PROGRESSIVE_DEVELOPMENT_PLAN.md` para branch, titulo, gates y criterio de merge

Semaforo de cambio:

- Verde: reutiliza entidades, no crea ruta, no cambia permisos, no agrega dependencia y tiene test claro. Puede entrar como micro-PR unico.
- Amarillo: agrega endpoint, escritura, OpenAPI o UI nueva. Requiere tests API/contrato/E2E proporcionales.
- Rojo: firma, receta valida, orden ejecutable, IA externa, RAG, adjuntos reales, datos sensibles o arquitectura nueva. Requiere contrato primero y nunca implementacion directa.
