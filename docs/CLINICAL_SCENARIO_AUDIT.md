# Auditoria Clinica por Escenarios

Fecha: 2026-06-26

Este documento revisa flujos clinicos sinteticos desde producto, permisos,
papel, auditoria e IA. No reemplaza tests ni Screen Tree: fija que debe quedar
verificable antes de abrir nuevas pantallas.

## Decision

El proximo ciclo congela nuevas superficies visibles. La prioridad es
profundizar flujos existentes: ambulatorio minimo, hospitalizacion borrador,
ficha longitudinal, papel y seguridad clinica.

## Escenario 1: consulta ambulatoria

Recorrido esperado:

```text
/home -> Consultas ambulatorias -> /consulta/agenda -> atencion -> ficha longitudinal
```

Escritura permitida:

- `medico`, `admin` y `dev`: cita, encuentro ambulatorio, evolucion SOAP y cierre
  no firmado cuando el flujo lo permita.
- `enfermeria`: solo preconsulta ambulatoria minima con
  `workflow_kind=ambulatory_preconsult`, signos, evento clinico acotado y datos
  permitidos.
- `solo_lectura`: no escribe.

Papel:

- evolucion y resumen pueden proyectarse como hoja carta si existe fuente.
- no existe receta valida, orden ejecutable ni documento firmado.

Bloqueos:

- admision administrativa productiva.
- receta valida, firma legal, ordenes ambulatorias e interconsultas amplias.
- IA externa, chat libre, RAG y escritura automatica.

Auditoria:

- toda cita, encuentro, signo, evento y evolucion escrita debe registrar actor,
  paciente, fuente y correlation ID.
- los errores de pertenencia entre paciente/cita/encuentro deben terminar como
  404/403 segun contrato del endpoint.

IA permitida:

- lectura contextual, faltantes y borrador revisable donde el Screen Capability
  Registry lo declare.
- no diagnostica, no firma, no prescribe y no cierra automaticamente.

## Escenario 2: hospitalizacion con indicacion borrador

Recorrido esperado:

```text
/home -> Hospitalizacion -> camas/rondas -> paciente hospitalizado -> indicaciones
```

Escritura permitida:

- `medico`, `admin` y `dev`: cama, ingreso borrador, hoja diaria, epicrisis
  borrador e indicacion hospitalaria en estado `draft` o `closed`.
- `enfermeria`: lectura y funciones acotadas existentes; no crea indicaciones,
  no firma y no ejecuta medicamentos.
- `solo_lectura`: lectura solamente.

Papel:

- ingreso, hoja diaria, epicrisis, rondas e indicacion pueden imprimirse como
  hoja carta si existe fuente.
- todo papel no firmado debe mostrar estado de desarrollo/borrador y no uso
  clinico real cuando aplique.

Bloqueos:

- firma legal, alta formal, orden ejecutable, Kardex, MAR, administracion real
  de medicamentos, doble chequeo y receta valida.
- UCI, pabellon productivo y procedimientos quirurgicos.

Auditoria:

- cada escritura hospitalaria debe quedar vinculada al paciente y a un
  `ClinicalEncounter(type=hospitalization)`.
- indicaciones deben auditar before/after, estado y actor.

IA permitida:

- resumen o apoyo no ejecutable sobre fuentes existentes.
- no crea, firma, activa ni administra indicaciones.

## Escenario 3: paciente con riesgo, alergia y medicacion

Recorrido esperado:

```text
/home -> servicio autorizado -> seleccionar paciente -> ficha longitudinal
```

Escritura permitida:

- `medico`, `admin` y `dev`: alergias, problemas, medicacion y riesgos segun
  permisos actuales.
- `enfermeria`: riesgos, signos, eventos y preconsulta minima; no alergias,
  medicacion, problemas ni IA clinica.
- `solo_lectura`: lectura solamente.

Papel:

- ficha, resumen y evolucion pueden mostrar antecedentes existentes.
- receta valida y documentos firmados siguen bloqueados.

Bloqueos:

- scores automaticos, alertas opacas, farmacovigilancia automatica,
  interacciones amplias no curadas y decisiones autonomas.
- adjuntos externos y consentimientos productivos.

Auditoria:

- riesgos y correcciones deben usar estado, fuente inspeccionable, before/after
  y correlation ID.
- alergias y medicacion deben registrar actor y cambios clinicos relevantes.

IA permitida:

- resumir faltantes, fuentes y contexto.
- no calcula scores, no crea `ClinicalPatch` para riesgos, no prescribe y no
  reemplaza revision humana.

## Criterios de salida del ciclo

- Los tres escenarios quedan cubiertos por un walkthrough humano unico, sin
  datos reales y sin rutas nuevas.
- `npm run check:screens`, `npm run check:api`, `npm run check:web` y
  `npm run check:contract` pasan.
- Las rutas hospitalarias, documentales e IA minima declaran
  `completa/en expansion gobernada` cuando dependen de borradores o guardrails.
- No se agregan pantallas nuevas antes de cerrar los hallazgos del ciclo.
