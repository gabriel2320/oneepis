# Screen Tree

`lifecycle=complete` significa que la ruta existe y esta conectada a su flujo
tecnico esperado. No significa uso clinico real, firma legal, receta valida ni
orden ejecutable. La validez clinica se declara por separado en
`screen-capabilities.ts` mediante `clinicalUse`:

- `development-only`: visible para laboratorio/desarrollo; no uso clinico real.
- `draft-workflow`: flujo auditable de borrador o cerrado tecnico, sin firma legal.
- `clinically-valid`: reservado para flujos con politica legal/productiva completa.
- `blocked`: ruta presente pero no habilitada funcionalmente.

## Pacientes

```text
/
  -> /pacientes

/login

/pacientes
/pacientes/nuevo
/pacientes/[patientId]
/pacientes/[patientId]/estado
/pacientes/[patientId]/ficha
/pacientes/[patientId]/eventos
/pacientes/[patientId]/ai-chart
/pacientes/[patientId]/encuentros
/pacientes/[patientId]/encuentros/nuevo
/pacientes/[patientId]/evoluciones
/pacientes/[patientId]/evoluciones/nueva
/pacientes/[patientId]/evoluciones/desde-eventos
/pacientes/[patientId]/problemas
/pacientes/[patientId]/problemas/nuevo
/pacientes/[patientId]/alergias
/pacientes/[patientId]/alergias/nueva
/pacientes/[patientId]/medicacion
/pacientes/[patientId]/medicacion/nueva
/pacientes/[patientId]/signos-vitales
/pacientes/[patientId]/signos-vitales/nuevo
/pacientes/[patientId]/documentos
/pacientes/[patientId]/ia
/pacientes/[patientId]/auditoria
```

Estado:

- `/pacientes`, `/pacientes/nuevo`, estado clinico, ficha, eventos, AI-Chart, encuentros, evoluciones, problemas activos, alergias, medicacion, signos vitales, IA y auditoria estan conectadas a la base E2E.
- AI-Chart usa eventos clinicos, reglas locales, fuentes, faltantes, propuestas revisables y hoja SOAP con margen inteligente.
- documentos existe como ruta preparada, sin backend definitivo.

## Hospitalizacion

```text
/hospitalizacion
/hospitalizacion/camas
/hospitalizacion/camas/nueva
/hospitalizacion/rondas
/hospitalizacion/pacientes/[patientId]/hoja-diaria
/hospitalizacion/pacientes/[patientId]/hoja-diaria/[sheetId]/editar
/hospitalizacion/pacientes/[patientId]/indicaciones
```

Estado:

- `/hospitalizacion` y `/hospitalizacion/camas` muestran encuentros `hospitalization` en curso.
- el tablero prefiere cama estructurada `sala / habitacion / cama` cuando existe.
- `/hospitalizacion/camas/nueva` crea camas y puede asignar un ingreso activo sin cama.
- `/hospitalizacion/camas` permite asignar ingresos activos sin cama a una cama disponible.
- hoja diaria hospitalizada ya tiene escritura clinica propia con PostgreSQL, API, permisos, auditoria, OpenAPI, crear/listar/editar/cerrar UI y print.
- estado `closed` bloquea edicion posterior, pero no equivale a firma legal.
- la fecha de hoja diaria debe pertenecer a la ventana del ingreso hospitalario usando fecha clinica local `America/Santiago`.
- `/hospitalizacion/rondas` muestra una ronda de lectura desde ingresos activos, camas y ultimas hojas diarias.
- indicaciones ya entraron como borrador gobernado con PostgreSQL, API, permisos, auditoria, OpenAPI, UI y papel.
- no existen indicaciones firmadas ni ejecucion de orden hospitalaria.

## Consulta

```text
/consulta
/consulta/agenda
/consulta/pacientes/[patientId]/atencion
/consulta/pacientes/[patientId]/resumen
```

Estado:

- `/consulta/pacientes/[patientId]/atencion` crea atencion ambulatoria minima usando encuentro y SOAP vinculada.
- `/consulta/agenda` sigue preparada, sin agenda productiva.
- `/consulta/pacientes/[patientId]/resumen` sigue preparado; la ficha paciente mantiene el resumen longitudinal principal.

## Configuracion

```text
/configuracion
/configuracion/apariencia
/configuracion/ia
/configuracion/api
```

Estado:

- apariencia: dark mode + selector de template.
- IA: estado de Ollama.
- API: base URL + enlace OpenAPI.

## Print

```text
/print/pacientes/[patientId]/ficha
/print/pacientes/[patientId]/evolucion/[entryId]
/print/pacientes/[patientId]/resumen
/print/pacientes/[patientId]/receta
/print/hospitalizacion/rondas
/print/hospitalizacion/pacientes/[patientId]/hoja-diaria/[sheetId]
/print/hospitalizacion/pacientes/[patientId]/indicacion/[indicationId]
```

Estado:

- ficha, resumen y evolucion renderizan hoja imprimible.
- ronda hospitalaria renderiza hoja imprimible desde ingresos activos y ultimas hojas diarias.
- hoja diaria hospitalizada renderiza hoja imprimible con footer de desarrollo.
- indicacion hospitalaria renderiza borrador imprimible y explicita que no es orden firmada.
- receta existe, pero queda bloqueada funcionalmente hasta firma, folio, actor, fecha clinica, permisos y reglas de prescripcion.
