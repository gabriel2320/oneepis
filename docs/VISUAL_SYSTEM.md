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

Estan registrados en `apps/web/tailwind.config.ts`.

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
- ambulatorio: `AppointmentList`, `VisitWorkspace`, `PatientLongitudinalSummary`, `QuickSoapEditor`

## Criterios UI

- No ocultar estados: cada flujo debe tener loading, error y empty.
- Botones sin accion real deben estar deshabilitados o ir a una ruta preparada.
- Mantener densidad clinica: informacion escaneable, sin hero marketing.
- No agregar cards anidadas salvo items repetidos o herramientas contenidas.
