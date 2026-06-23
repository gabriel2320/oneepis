# Changelog

## v0.4-assistant-read - 2026-06-23

Estado: aprobado para demo gobernada tras walkthrough humano.

Cambios principales:

- Assistant Read queda integrado en AI-Chart como capa clinica de solo lectura.
- Timeline, busqueda, series y correlacion muestran fuentes, limites y faltantes.
- Laboratorio estructurado minimo aporta lectura reciente en AI-Chart y ficha.
- La ficha muestra una linea de tiempo completa minima con eventos y evoluciones.
- Las intenciones IA quedan bloqueadas por defecto si la pantalla no declara `ScreenCapability`.
- Los scripts API/contrato/dev API usan wrappers Python cross-platform.
- CI agrega seguridad report-only: gitleaks, dependency review, CodeQL, `npm audit` y `pip-audit`.

Validacion:

- Walkthrough humano aprobado el 2026-06-23.
- Validacion automatizada local reciente: `check:size`, `check:api`, `check:contract`, `check:web`, E2E demo y E2E Assistant Read.

Restricciones mantenidas:

- Sin chat libre.
- Sin RAG amplio.
- Sin IA externa activa.
- Sin escritura automatica desde Assistant Read.
- Sin receta valida, firma clinica, orden ejecutable ni administracion de medicamentos.
- OneEpis sigue siendo piloto/demo gobernado, no produccion sanitaria.

Rollback:

- Desactivar la superficie web Assistant Read si se detecta riesgo clinico.
- Mantener endpoints de lectura y laboratorio minimo porque no escriben ficha ni migran historicos automaticamente.
