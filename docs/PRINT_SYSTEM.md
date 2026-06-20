# Print System

## Rutas

- `/print/pacientes/[patientId]/ficha`
- `/print/pacientes/[patientId]/evolucion/[entryId]`
- `/print/pacientes/[patientId]/resumen`
- `/print/pacientes/[patientId]/receta`

## Componentes

Ubicacion: `apps/web/src/components/print/clinical-print.tsx`.

- `PrintPage`
- `PrintHeader`
- `PrintFooter`
- `ClinicalPaperSheet`
- `SoapPrintSheet`
- `PatientSummaryPrintSheet`

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

## Pendiente

- soporte A5 real por ruta o preferencia.
- numeracion de paginas multihoja.
- folios firmados cuando exista modulo de firma.
