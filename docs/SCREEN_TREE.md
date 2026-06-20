# Screen Tree

## Pacientes

```text
/
  -> /pacientes

/pacientes
/pacientes/nuevo
/pacientes/[patientId]
/pacientes/[patientId]/ficha
/pacientes/[patientId]/evoluciones
/pacientes/[patientId]/evoluciones/nueva
/pacientes/[patientId]/problemas
/pacientes/[patientId]/alergias
/pacientes/[patientId]/medicacion
/pacientes/[patientId]/signos-vitales
/pacientes/[patientId]/documentos
/pacientes/[patientId]/ia
/pacientes/[patientId]/auditoria
```

Estado:

- `/pacientes`, `/pacientes/nuevo`, ficha, evoluciones, alergias, medicacion, signos vitales, IA y auditoria estan conectadas a la base E2E.
- problemas y documentos existen como rutas preparadas, sin backend definitivo.

## Hospitalizacion

```text
/hospitalizacion
/hospitalizacion/camas
/hospitalizacion/rondas
/hospitalizacion/pacientes/[patientId]/hoja-diaria
/hospitalizacion/pacientes/[patientId]/indicaciones
```

Estado:

- rutas creadas con widgets base: `BedBoard`, `RoundList`, `DailySheet`.
- no escriben datos clinicos todavia.

## Consulta

```text
/consulta
/consulta/agenda
/consulta/pacientes/[patientId]/atencion
/consulta/pacientes/[patientId]/resumen
```

Estado:

- rutas creadas con widgets base: `AppointmentList`, `VisitWorkspace`, resumen longitudinal preparado.

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
```

Estado:

- ficha, resumen y evolucion renderizan hoja imprimible.
- receta existe, pero queda bloqueada funcionalmente hasta firma, permisos y reglas de prescripcion.
