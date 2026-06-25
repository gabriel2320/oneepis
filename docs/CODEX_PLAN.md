# Codex Plan

Guia breve para cambios hechos por agentes.

Fuentes canonicas:

- Historial: `docs/ROADMAP.md`
- Estado operativo: `docs/CURRENT_STATE.md`
- Decision anti-inflacion: `docs/GOVERNANCE.md`
- Rutas y capacidades: `docs/SCREEN_TREE.md`
- Fases AI-Chart: `docs/PROGRESSIVE_DEVELOPMENT_PLAN.md`

## Regla Madre

Construir OneEpis por ladrillos clinicos verificables:

```text
1 objetivo clinico
1 cambio acotado
tests/gates
OpenAPI actualizado si cambia API
docs minimas
sin datos reales
```

## No Negociable

- No usar datos reales ni datos demo realistas.
- No implementar diagnostico autonomo.
- No firmar ni escribir ficha desde IA.
- No imprimir receta clinica valida sin firma, folio, actor, fecha clinica y permisos claros.
- No agregar dependencias sin justificacion.
- No dejar TypeScript roto.
- No dejar endpoints sin tests.
- Toda escritura clinica debe tener actor, permisos, auditoria y `correlation_id`.
- Todo cambio de API debe actualizar `packages/contracts/openapi.json`.
- Frontend no debe usar datos demo salvo `NEXT_PUBLIC_DEMO_MODE=true`.
- Ninguna ruta clinica o print con ID en URL puede mostrar un primer registro como fallback.
- Ningun archivo clinico nuevo debe superar 350 lineas sin excepcion explicita en `scripts/check-file-size.mjs`.

## Loop De Trabajo

1. Leer `docs/CURRENT_STATE.md`, `docs/GOVERNANCE.md` y el doc del dominio tocado.
2. Entender cambios existentes en el working tree sin revertir trabajo ajeno.
3. Implementar solo el objetivo.
4. Ejecutar gates proporcionales al cambio.
5. Actualizar docs solo si cambia comportamiento o decision.
6. Entregar resumen, pruebas y riesgos.

## Criterio De Producto

OneEpis debe sentirse como mesa clinica viva:

- paciente al centro
- ficha y papel como proyecciones clinicas serias
- auditoria visible
- IA local util, silenciosa y trazable
- dashboards, chat libre y modulos incompletos fuera del core

## AI-Chart

AI-Chart vive en `apps/web/src/components/clinical/ai-chart/`.

Reglas para nuevos cambios:

- mantener `patient-ai-chart-pages.tsx` como orquestador
- no agregar bloques UI inline grandes en la pagina
- preferir componentes existentes antes de crear rutas nuevas
- no sumar reglas clinicas al frontend; si una regla interpreta datos, vive en API
- todo nuevo output debe tener fuente, faltante/limite, accion humana y auditoria
- propuestas de escritura deben converger a `ClinicalPatch` revisable antes de persistir

Para foco actual, cola activa y limites detallados, usar `docs/CURRENT_STATE.md`
y `docs/GOVERNANCE.md`. Este archivo no es backlog.
