# Print System

## Rutas

- `/print/pacientes/[patientId]/ficha`
- `/print/pacientes/[patientId]/evolucion/[entryId]`
- `/print/pacientes/[patientId]/resumen`
- `/print/pacientes/[patientId]/receta`
- `/print/hospitalizacion/rondas`
- `/print/hospitalizacion/pacientes/[patientId]/hoja-diaria/[sheetId]`
- `/print/hospitalizacion/pacientes/[patientId]/indicacion/[indicationId]`

## Componentes

Ubicaciones:

- `apps/web/src/components/print/clinical-print.tsx`
- `apps/web/src/components/print/hospital-indication-print.tsx`
- `apps/web/src/components/print/hospital-round-print.tsx`

- `PrintPage`
- `PrintHeader`
- `PrintFooter`
- `ClinicalPaperSheet`
- `SoapPrintSheet`
- `PatientSummaryPrintSheet`
- `PrintHospitalIndicationPage`
- `PrintHospitalRoundPage`

## CSS

Ubicacion: `apps/web/src/app/globals.css`.

Reglas:

- `@page` usa carta por defecto.
- navegacion y acciones se ocultan con `data-print-hidden="true"`.
- se evita cortar secciones con `.print-section`.
- las hojas usan `.print-sheet`.

## Footer obligatorio

Cada documento debe incluir:

- fecha de emision
- folio demo
- pagina
- texto: `Documento de desarrollo / no uso clinico real.`

## Indicaciones y Receta

- `/print/pacientes/[patientId]/receta` existe como ruta bloqueada de desarrollo.
- Una receta no puede imprimirse como documento clinico valido hasta tener firma, folio, actor, fecha clinica y permisos claros.
- Una indicacion hospitalaria solo puede imprimirse como `draft` o `closed` mientras no exista firma real.
- El papel debe mostrar el estado del documento y no puede ocultar que un texto viene de borrador o revision IA.

## Pendiente

- soporte A5 real por ruta o preferencia.
- numeracion de paginas multihoja.
- folios firmados cuando exista modulo de firma.
