# Screen Tree

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
/pacientes/[patientId]/encuentros
/pacientes/[patientId]/encuentros/nuevo
/pacientes/[patientId]/evoluciones
/pacientes/[patientId]/evoluciones/nueva
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

- `/pacientes`, `/pacientes/nuevo`, estado clinico, ficha, encuentros, evoluciones, problemas activos, alergias, medicacion, signos vitales, IA y auditoria estan conectadas a la base E2E.
- documentos existe como ruta preparada, sin backend definitivo.

## Hospitalizacion

```text
/hospitalizacion
/hospitalizacion/camas
/hospitalizacion/rondas
/hospitalizacion/pacientes/[patientId]/hoja-diaria
/hospitalizacion/pacientes/[patientId]/indicaciones
```

Estado:

- `/hospitalizacion` y `/hospitalizacion/camas` muestran encuentros `hospitalization` en curso.
- el tablero prefiere cama estructurada `sala / habitacion / cama` cuando existe.
- rondas, hoja diaria e indicaciones siguen preparadas, sin escrituras clinicas propias.

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
