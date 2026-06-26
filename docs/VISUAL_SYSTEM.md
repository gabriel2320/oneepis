# Visual System

## Templates

OneEpis tiene tres templates visuales persistentes en `localStorage`:

- `clinical-sober`: default, neutro claro, teal/azul clinico, densidad media.
- `hospital-night`: dark-first, alto contraste, alertas visibles.
- `ambulatory-warm`: superficies mas calidas para lectura longitudinal.

Implementacion:

- tokens CSS en `apps/web/src/app/globals.css`
- selector en `components/theme/template-selector.tsx`
- dark mode con `next-themes`
- toggle en `components/theme/theme-toggle.tsx`

## Tokens

Ademas de los tokens shadcn base, existen:

- `success`
- `warning`
- `info`
- `clinical-critical`
- `clinical-stable`
- `clinical-pending`
- `clinical-draft`
- `clinical-readonly`
- `paper-background`
- `paper-line`
- `paper-margin`
- `ai-source`
- `ai-missing`

Estan registrados en `apps/web/tailwind.config.ts`.

## Reglas de composicion clinica

1. Una pantalla tiene una accion clinica principal.
2. La ficha del paciente es el centro; no se crean dashboards centrales.
3. La IA vive como riel contextual, no como protagonista.
4. Todo dato inferido muestra fuente, faltante o limite.
5. Cada formulario debe tener titulo clinico, contexto paciente, campos esenciales, accion primaria, accion secundaria y estado de permisos.
6. Toda pantalla clinica debe tener empty/error/loading.
7. El modo papel es espejo de confianza, no export decorativo.

## Componentes base

Ubicacion: `apps/web/src/components/clinical`.

- `ClinicalSectionCard`
- `AlertCard`
- `MetricCard`
- `TimelineCard`
- `PrintableSection`
- `EmptyState`
- `ErrorState`
- `LoadingRows`

Widgets clinicos:

- `VitalsStrip`
- `AllergyList`
- `MedicationList`
- `ProblemList`
- `ClinicalTimeline`
- `AuditTimeline`
- `AiSafetyPanel`
- `PrintActions`
- `LatestVitalsTrend`

Widgets por contexto:

- hospitalizado: `BedBoard`, `RoundList`, `DailySheet`, `CriticalAlerts`, `LatestVitalsTrend`
- ambulatorio: `AmbulatoryCommandCenter`, `AppointmentList`, `PatientLongitudinalSummary`, `QuickSoapEditor`

## Criterios UI

- No ocultar estados: cada flujo debe tener loading, error y empty.
- Botones sin accion real deben estar deshabilitados o ir a una ruta preparada.
- Mantener densidad clinica: informacion escaneable, sin hero marketing.
- No agregar cards anidadas salvo items repetidos o herramientas contenidas.
