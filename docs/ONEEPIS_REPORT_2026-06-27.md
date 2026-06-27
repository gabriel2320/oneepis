# OneEpis Report - 2026-06-27

Snapshot de auditoria fechado. No es documento canonico vivo; para decisiones
vigentes usar `docs/CURRENT_STATE.md`, `docs/GOVERNANCE.md` y
`docs/SCREEN_TREE.md`. Este reporte corrige y reemplaza la numeracion de PRs de
auditorias informales previas que estaban desfasadas respecto a
`docs/CURRENT_STATE.md`.

## Resumen ejecutivo

OneEpis dejo de ser solo limpieza de UX y entro en fundamentos HIS minimos:
auditoria de lecturas, logs PHI-safe backend, contrato auth/sesion ejecutable,
`ClinicalOrder` borrador y resultados de laboratorio con fuente. La direccion es
correcta, pero el repo volvio a rozar el limite de inflacion tecnica: los micro
PRs de UX funcionaron bien y los PRs de contrato HIS empezaron a crecer.

El riesgo dominante ya no es cosmetico, es semantico: mantener cerrado el camino
hacia CPOE, MAR, receta y firma mientras se construyen contratos de solo lectura
con fuente y auditoria.

## Numeracion canonica de PRs

Fuente: `docs/CURRENT_STATE.md` (Estado Real) y `docs/NO_PRODUCTION_CHECKLIST.md`.

| PR | Entrega |
| --- | --- |
| #98 | Ciclo correctivo UX (login sobrio, home mapa fisico, nota libre) |
| #99 | Preconsulta lateral compacta |
| #100 | `SECURITY.md` alineado (auth dev, RBAC minimo) |
| #102-#106 | Ambulatorio profundizado (cierre, contexto, feedback, cabecera, timeline) |
| #107-#109 | Base HIS minima (Vercel off, auditoria de lecturas, UI de auditoria) |
| #110 | Logs PHI-safe backend (sanitizador + filtro al arranque) |
| #111 | Contrato auth/sesion ejecutable |
| #112 | `ClinicalOrder` borrador backend (`draft\|cancelled\|entered_in_error`) |
| #113 | Orden borrador visible en ficha |
| #114 | Resultados de laboratorio con fuente |

HEAD actual: `6320e0a ...(#114)`. Cualquier auditoria que situe PHI logs en #108,
`ClinicalOrder` en #110 o lab source en #112 esta desfasada y no debe usarse.

## Diagnostico de desarrollo

Funciona: la cadena #98-#106 corrigio producto sin abrir rutas nuevas ni meter
macro HIS. Cada PR toco una superficie, un comportamiento y su test.

Empieza a tensarse: el bloque #107-#109 mezclo infraestructura (Vercel),
auditoria backend y UI de auditoria en una sola tanda. #112 (`ClinicalOrder`)
fue un contrato clinico grande y defendible, pero no debe volverse patron.

Lectura central: OneEpis cruzo de "limpieza de producto" a "zona clinica
sensible". El momento exige menos entusiasmo y mas friccion de ingenieria.

## Riesgos vivos (trazables)

Se referencian por ID versionado en `docs/NO_PRODUCTION_CHECKLIST.md` en vez de
repetir prosa:

- `NOPROD-SEC-005` Auditoria de accesos: en progreso; riesgo de volumen por
  commit en GET (ver Dev-117).
- `NOPROD-SEC-006` Logs PHI-safe: en progreso; falta cobertura de strings planos
  (ver Dev-116).
- `NOPROD-SEC-008` Auth productiva, `NOPROD-SEC-007` control contextual,
  `NOPROD-SEC-001..004` secretos/cifrado/backups/retencion: pendientes.
- `NOPROD-SEC-011` Firma/receta/orden ejecutable: bloqueada. Es el frente de
  mayor riesgo y la razon de Dev-115A.

## Errores de desarrollo y gate que los frena

| Error | Patron | Gate / memoria ejecutable |
| --- | --- | --- |
| 1 | PRs con varias intenciones (#107-#109) | Presupuesto por PR en `docs/CODEX_PLAN.md` (<=4 archivos, 1 comportamiento) |
| 2 | Contratos clinicos demasiado grandes (#112) | Reglas de tamano en `docs/GOVERNANCE.md`; `npm run check:size` (350 lineas) |
| 3 | `CURRENT_STATE.md` como changelog | Limite 180 lineas y regla anti-canonitis en `docs/GOVERNANCE.md` |
| 4 | Exceso de confianza en guards de copy | Guard de enum backend (Dev-115A) + revision humana clinica |
| 5 | Falsa seguridad | Cada PR de seguridad declara alcance cubierto / fuera de alcance en `docs/NO_PRODUCTION_CHECKLIST.md` |

Nota sobre el Error 4: los terminos `orden ejecutable`, `administrar`,
`dispensar`, `MAR` y `orden firmada` aparecen y deben aparecer en copy como
estado bloqueado/negado. Un guard de subcadena prohibida romperia la UI legitima;
por eso el invariant fuerte vive en el enum de backend y en aserciones positivas
de badge, no en una lista de palabras prohibidas global. Dev-115A no debe
extender `FORBIDDEN_CLINICAL_COPY` con esos terminos clinicos negados.

## Invariant clave: ordenes no ejecutables

`ClinicalOrder` es la puerta hacia CPOE, laboratorio, enfermeria y farmacia. La
obligacion es mantener esa puerta cerrada por memoria ejecutable, no por copy:

- Enum de estado bloqueado a `draft|cancelled|entered_in_error`
  (`apps/api/src/oneepis_api/models/clinical_order.py`).
- `ClinicalOrderCreate` no expone `status`; Dev-115A no endurece POST con
  cambios productivos de validacion extra-field.
- `ClinicalOrderUpdate` rechaza cualquier otro estado con 422
  (`apps/api/src/oneepis_api/schemas/clinical_order.py`).
- UI muestra siempre `Borrador / No ejecutable / No firmado`
  (`apps/web/src/components/clinical/clinical-orders-preview.tsx`).

Distincion importante: `ClinicalOrder` usa `draft|cancelled|entered_in_error`;
la politica de indicaciones/receta de `docs/GOVERNANCE.md` usa
`draft|closed|signed`. Son maquinas de estado distintas y los guards deben
apuntar al modelo correcto.

## Plan de desarrollo corregido (Dev-115A..123)

- Dev-115A: sellar `ClinicalOrder` como borrador no ejecutable con gates (enum
  lock + create sin `status` + PATCH 422 en estado prohibido + aserciones de
  badge). Solo tests. Es el paso inmediato antes de medicacion.
- Dev-115B: medicacion segura de solo lectura (nombre, dosis, frecuencia, via,
  estado, fuente; faltantes declarados; leyenda no receta / no dispensacion /
  no MAR). Debe enganchar la politica "Vademecum y Dosis" de `docs/GOVERNANCE.md`
  y la politica "Indicaciones y Receta". Si la fuente no existe en el read model,
  dividir en PR API y PR UI.
- Dev-116: PHI-safe logging para strings planos; cierra el residual de
  `NOPROD-SEC-006`. Solo tests; sin Sentry/OTel/frontend.
- Dev-117: dedupe/control de volumen de auditoria de lecturas
  (`NOPROD-SEC-005`); sin tabla nueva.
- Dev-118: guard anti-LIS/RIS/PACS para resultados (lectura con fuente, no LIS).
- Dev-119: ficha anti-dashboard-creep; compactar paneles si hace falta.
- Dev-120: filtros minimos de auditoria lectura/escritura sin dashboard.
- Dev-121: reconciliar claims de `NO_PRODUCTION_CHECKLIST.md` con la realidad.
- Dev-122: contrato de documentos externos como `bloqueada/futura`, sin upload.
- Dev-123: preparacion ABAC; analisis ejecutable de rutas/roles, sin
  implementacion completa.

No abrir todavia: CPOE real, farmacia, MAR, receta valida, firma, UCI, pabellon,
portal paciente, ERP, facturacion, inventario, OpenSearch, OCR, FHIR, TipTap,
LIS/RIS/PACS.

## Plan en una frase

OneEpis debe consolidar cada contrato clinico como borrador, fuente y auditoria
antes de permitir cualquier ejecucion.

---

Snapshot, no fuente canonica viva (`docs/GOVERNANCE.md`, Frontera Documental).
