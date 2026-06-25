# OneEpis Report - 2026-06-25

Snapshot de auditoria fechado. No es documento canonico vivo; para decisiones
vigentes usar `docs/CURRENT_STATE.md`, `docs/GOVERNANCE.md` y
`docs/SCREEN_TREE.md`.

## Resumen ejecutivo

OneEpis es un monorepo clinico en fase temprana, orientado a ficha clinica
modular, auditable y asistida por IA local. El repositorio mantiene una
direccion tecnica coherente: backend como fuente de verdad, contrato OpenAPI
estable, frontend con API real por defecto, IA sin escritura automatica y
auditoria en escrituras clinicas.

La base actual esta sana para desarrollo gobernado, pero no esta lista para
produccion sanitaria. Los principales bloqueos productivos siguen siendo
seguridad operacional, cumplimiento legal/clinico, cifrado, gestion de
secretos, politicas de respaldo/retencion y hardening de CI.

## Alcance revisado

- Aplicacion web: `apps/web`, Next.js, React, Tailwind y componentes clinicos.
- API: `apps/api`, FastAPI, Pydantic, SQLAlchemy y Alembic.
- Contratos: `packages/contracts/openapi.json`.
- Infra local: `infra/docker-compose.dev.yml`.
- Gobernanza: `docs/CURRENT_STATE.md`, `docs/GOVERNANCE.md`,
  `docs/SCREEN_TREE.md`, `docs/PERMISSIONS.md`, `SECURITY.md`.
- Seguridad de dependencias npm: nuevo scanner OSV en
  `scripts/check-npm-advisories.mjs`.

## Estado funcional

El flujo base declarado esta implementado y validado:

`paciente -> ficha -> evolucion SOAP -> PostgreSQL -> auditoria -> UI`

Superficies principales:

- `/pacientes`: entrada y lista clinica.
- `/pacientes/[patientId]/ficha`: centro longitudinal.
- `/pacientes/[patientId]/ai-chart`: lectura asistida, reglas y propuestas
  auditables.
- `/consulta`: flujo ambulatorio minimo.
- `/hospitalizacion`: flujo hospitalario minimo.
- `/print/*`: proyecciones imprimibles.

La UI usa API real por defecto. El modo demo queda reservado a
`NEXT_PUBLIC_DEMO_MODE=true`.

## Arquitectura

### Backend

El backend concentra la verdad clinica y la seguridad de escritura:

- FastAPI expone rutas versionadas bajo `/api/v1`.
- SQLAlchemy modela pacientes, encuentros, evoluciones, eventos, signos vitales,
  problemas, alergias, medicacion, laboratorio, riesgos clinicos, camas,
  indicaciones y hojas diarias.
- Alembic gestiona migraciones.
- Pydantic define contratos de lectura/escritura y OpenAPI.
- Auditoria se registra con `record_audit_event` y contexto de request.

Separaciones recientes:

- `ClinicalPatch` mantiene logica de confirmacion; la auditoria de patches vive
  en `services/clinical_patch_audit.py`.
- `ClinicalAppointment` y `VitalSign` fueron extraidos desde
  `models/clinical_record.py` a modulos propios, con reexports para no romper
  consumidores existentes.
- Las reglas de correlacion Assistant Read fueron extraidas a
  `patient_assistant_correlation_rules.py`; la ruta queda enfocada en carga de
  datos y respuesta HTTP.

### Frontend

El frontend esta organizado en superficies clinicas y componentes reutilizables:

- Next.js App Router.
- React Query para datos remotos.
- Contratos TypeScript derivados del contrato API.
- Screen capability registry en `apps/web/src/lib/screen-capabilities.ts`.
- Guards de pantalla/documentacion mediante `check:screens`.

El producto prioriza ficha/paciente/papel sobre dashboards amplios, consistente
con la gobernanza anti-inflacion.

### Contrato

OpenAPI es el contrato estable entre API y frontend. El gate
`npm run check:contract` exporta OpenAPI, valida Assistant Read y exige que
`packages/contracts/openapi.json` no tenga drift.

## Seguridad y privacidad

Estado actual:

- Auth local habilitada por defecto.
- Fuera de `development`, la API rechaza:
  - secreto default,
  - usuarios locales default,
  - `ONEEPIS_AUTH_ALLOW_DEV_ACTOR_HEADER=true`,
  - `ONEEPIS_AUTH_ENABLED=false`.
- Roles actuales: `admin`, `medico`, `enfermeria`, `solo_lectura`, `dev`.
- Permisos finos para lectura/escritura de paciente y dominios clinicos.
- Auditoria por escritura clinica.
- IA clinica requiere rol autorizado y no escribe sin confirmacion humana.
- Repositorio publico: prohibidos datos reales, PHI, identificadores, secretos,
  dumps y logs sensibles.

Riesgos pendientes antes de produccion:

- No hay diseno completo de cifrado en reposo.
- No hay politica productiva de backup, restore y retencion.
- No hay gestion formal de secretos.
- CI security sigue parcialmente report-only.
- No hay revision legal/clinica ni certificacion sanitaria.
- No hay modelo productivo de observabilidad PHI-safe.

## IA clinica

La IA esta correctamente acotada para fase temprana:

- Ollama local como proveedor first-class, opcional.
- Reglas y plantillas funcionan aunque Ollama este apagado.
- Assistant Read es solo lectura.
- ClinicalPatch exige confirmacion humana.
- Evoluciones generadas por AI-Chart se guardan como borrador, no firmadas.
- Propuestas rechazadas, bloqueadas y aceptadas quedan auditadas.

No se debe abrir chat libre, diagnostico autonomo, escritura automatica ni
proveedores externos sin una politica explicita de seguridad clinica.

## CI y gates

Gates oficiales:

```bash
npm run check:api
npm run check:web
npm run check:contract
npm run check:e2e
npm run check:npm-advisories
```

Resultado de validacion local reciente:

- `npm run check:api`: pasa, `102 passed`.
- `npm run check:web`: pasa, typecheck, lint y build con Next `16.2.9`.
- `npm run check:contract`: pasa, OpenAPI sin drift.
- `npm run check:e2e`: pasa, `41 passed`, `7 skipped`, mas `2 passed` del
  flujo Assistant Read.
- `npm run check:npm-advisories`: pasa en `high+`, reportando waiver explicito
  para PostCSS anidado en Next.

El job `security-report` mantiene:

- Gitleaks bloqueante.
- Dependency review report-only.
- CodeQL report-only.
- OSV npm advisory check report-only.
- `pip-audit` report-only.

## Seguridad de dependencias npm

`npm audit` no fue confiable en este entorno por errores de red contra
`registry.npmjs.org`. Se agrego una alternativa directa contra OSV:

```bash
npm run check:npm-advisories
```

Comportamiento:

- Lee `package-lock.json`.
- Consulta OSV `querybatch`.
- Obtiene detalle por vulnerabilidad.
- Falla por defecto en `high+`.
- Permite endurecer con:

```bash
ONEEPIS_NPM_ADVISORY_LEVEL=medium npm run check:npm-advisories
```

Advisory conocido:

- `GHSA-qx2v-qp2m-jg93`
- `postcss@8.4.31`
- Severidad: medium/moderate.
- Origen: dependencia anidada exacta de `next@16.2.9`.
- Estado: waiver exacto y visible, porque Next 16 hasta `16.2.9` declara
  `postcss: 8.4.31` y los overrides de npm no reemplazaron esa dependencia
  anidada.

Hardening del scanner:

- La severidad se lee desde `database_specific.severity`.
- Si falta, se interpreta el mayor score CVSS disponible en `severity[]`.
- Si una vulnerabilidad queda como `unknown` y no tiene waiver exacto, bloquea
  el check para forzar triage.

## Deuda tecnica

El guard de tamano pasa. Near-limit restante:

- `apps/api/src/oneepis_api/services/clinical_intent.py`: `328/350` lineas,
  watchlist no bloqueante; ya no requiere excepcion explicita.

Deuda reducida en esta pasada:

- `clinical_patch.py`: fuera de near-limit tras extraer auditoria.
- `clinical_record.py`: fuera de near-limit tras extraer citas y signos vitales.
- `patient_assistant_correlation.py`: fuera de near-limit tras extraer reglas.
- `clinical-intent-result-panel.tsx`: fuera de near-limit tras extraer paneles de soporte.
- `patient-ai-chart-pages.tsx`: fuera de near-limit tras extraer secciones de intencion, evidencia y borrador.
- `clinical_intent.py`: reducido tras extraer router, acciones, reglas de
  cambios, reglas de examenes y medicacion; la excepcion de tamano fue retirada.
- `ambulatory-appointment-pages.tsx`: fuera de near-limit tras extraer lista y panel de creacion.
- `assistant-read-sections.tsx`: fuera de near-limit tras extraer paneles de laboratorio.
- `ambulatory-visit-pages.tsx`: fuera de near-limit tras extraer el formulario SOAP ambulatorio.
- `demo-record.ts`: fuera de near-limit tras extraer fixtures demo hospitalarios.
- `patient-record-workspaces.tsx`: fuera de near-limit tras extraer sugerencias IA.

## Riesgos principales

1. Produccion sanitaria no habilitada.
   Faltan cifrado, secretos, backup/restore, retencion, observabilidad PHI-safe,
   revision legal y gobernanza clinica formal.

2. Seguridad CI incompleta.
   Gitleaks bloquea, pero dependency review, CodeQL, OSV npm y `pip-audit`
   siguen report-only.

3. Dependencia vulnerable anidada en Next.
   `next@16.2.9` pinnea `postcss@8.4.31`, afectado por
   `GHSA-qx2v-qp2m-jg93`. El waiver es explicito, pero debe retirarse cuando
   Next publique una version que actualice PostCSS.

4. Deuda concentrada en IA clinica.
   `clinical_intent.py` sigue en watchlist no bloqueante. Cualquier feature de
   IA debe empezar por extraccion o aislamiento de reglas.

5. Reportes y escaneos externos dependen de red.
   OSV y `pip-audit` requieren salida a internet. CI debe ser la fuente
   autoritativa cuando el entorno local falle por DNS/rate limits.

## Recomendaciones priorizadas

### Proximo paso minimo

Continuar con deuda near-limit restante antes de nuevas features. El scanner
OSV ya quedo endurecido con fallback CVSS y bloqueo de vulnerabilidades unknown
sin waiver, y AI-Chart web/API volvieron a quedar bajo presupuesto.

### Siguiente bloque tecnico

Reducir deuda backend near-limit restante antes de nuevas features:

- seguir extrayendo dominios de `clinical_intent.py` si se agrega IA nueva;
- evitar nuevas reglas inline en el orquestador de intenciones;
- mantener datos demo y pantallas ambulatorias bajo presupuesto antes de sumar comportamiento.

### Seguridad

- Definir politica para convertir OSV high/critical en bloqueante.
- Definir manejo de waivers con expiracion o condicion de retiro.
- Instalar y validar `pip-audit` en CI con salida revisable.
- Agregar checklist de secretos/PHI antes de PR.

### Producto clinico

- Mantener foco en paciente/ficha/papel.
- No abrir IA nueva hasta cerrar deuda de `clinical_intent.py`.
- No promover pantallas preparadas a completas sin permisos, auditoria, papel y
  E2E correspondiente.

## Estado de trabajo actual

Cambios propios pendientes:

- CI cambia `npm audit` por OSV npm advisory check.
- Docs de seguridad/gobernanza actualizan esa decision.
- API extrae reglas y modelos para bajar deuda near-limit.
- Se agrega `scripts/check-npm-advisories.mjs`.

Instrucciones de agente web revisadas:

- `apps/web/AGENTS.md`: conservar y versionar tal cual; es el bloque generado por Next para agentes.
- `apps/web/CLAUDE.md`: no aporta reglas propias, solo apunta a `AGENTS.md`; queda tratado como archivo local especifico de herramienta mediante `.gitignore`.

## Conclusion

OneEpis esta bien encaminado como plataforma clinica temprana y auditable. Los
gates principales pasan, el contrato esta estable y las extracciones recientes
reducen deuda sin cambiar comportamiento. El proyecto debe seguir creciendo por
modulos clinicos pequeños, con backend como fuente de verdad, auditoria
obligatoria y CI cada vez mas estricto.

La prioridad no es agregar superficie nueva; es endurecer seguridad, cerrar
deuda de IA, formalizar waivers y mantener el mapa de pantallas/contratos como
fuente de gobernanza ejecutable.
