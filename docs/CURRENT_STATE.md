# Current State

Fecha: 2026-06-29

Este documento es estado operativo vigente, no historial. El historial
cronologico vive en `docs/ROADMAP.md`; los reportes fechados son snapshots y no
fuente canonica viva.

## Estado Real Hoy

- OneEpis es una ficha clinica longitudinal con entrada por login limpio,
  `/home` como mapa fisico del hospital y mundos operativos separados para
  ambulatorio y hospitalizacion.
- Ciclo correctivo UX aplicado (#98): login sobrio, home mapa fisico estricto
  (servicios parciales visibles sin atajo generico a `/pacientes`), consulta con
  nota libre dominante y guard E2E de copy tecnico en rutas visibles.
- Preconsulta lateral compacta (#99): panel colapsado por defecto en atencion
  ambulatoria; la nota libre sigue siendo el registro principal.
- `SECURITY.md` alineado (#100): auth local de desarrollo y RBAC minimo, sin
  claim de ausencia total de autenticacion.
- E2E permisos real: `solo_lectura` lee atencion ambulatoria sin escritura;
  `enfermeria` abre preconsulta pero no guarda atencion medica (`DEMO_MODE=false`).
- Ambulatorio profundizado (#102-#106): cierre de consulta sin jerga tecnica,
  contexto longitudinal compacto, feedback de guardado, cabecera de ficha y timeline
  sobrio con fuente visible.
- Base HIS minima (#107-#109): Vercel git deploys desactivados en PRs;
  lecturas de ficha/paciente auditadas con `AuditEvent`, dedupe por ventana
  corta y auditoria UI que distingue lectura/escritura sin rutas nuevas.
- Auditoria de paciente reforzada: `/pacientes/[patientId]/auditoria` usa
  `audit_read`, no lectura clinica general; expone respuesta publica minimizada
  sin `extra_data` crudo y clasifica lectura/escritura con actor, ruta y
  `correlation_id`.
- Cobertura de auditoria de accesos: lecturas de paciente/ficha prueban actor,
  metodo, ruta y `correlation_id`; el dedupe de lectura ya no actualiza eventos
  existentes, sino que agrega eventos append-only `*.read_deduped`.
- Logs PHI-safe backend (#110): sanitizador reutilizable para estructuras y
  strings planos, con filtro de logging activo al arrancar la API; sin
  Sentry/OTel ni observabilidad productiva.
- Guard PHI-safe frontend/CI (Dev-130): `check:web` bloquea `console.*` en
  `apps/web/src`; CI bloquea OSV npm high/critical, mientras dependency review,
  CodeQL y `pip-audit` siguen report-only hasta politica especifica.
- Contrato auth/sesion ejecutable (#111): tests de revocacion en lecturas
  clinicas y gate OpenAPI sobre rutas auth y GET protegidos de paciente.
- ClinicalOrder borrador backend (#112): modelo, migracion, API y guards con
  estados `draft|cancelled|entered_in_error`; sin firma, ejecucion ni rutas web
  nuevas.
- Orden borrador visible en ficha (#113): panel en `/ficha` con leyenda
  borrador/no ejecutable/no firmado y lectura API; sin dashboard ni ruta nueva.
- Resultados con fuente (#114): cada `LabResultRead` expone bloque `source`
  (tipo, ref, label, ruta API); ficha muestra fuente declarada sin LIS/RIS/PACS.
- Medicacion segura (#120-#122): `MedicationRead` expone fuente y faltantes de
  dosis/via/frecuencia; la ficha muestra lectura clinica con fuente, faltantes y
  copy explicito de no receta/no dispensacion/no MAR. El E2E bloquea etiquetas
  positivas exactas de receta, firma, dispensacion, administracion, MAR y orden
  ejecutable fuera de contexto bloqueado/futuro.
- Vademecum local draft entro a `main`: candidatos, evidencia, reglas demo y
  validacion de dosis siguen siendo apoyo de borrador, no motor prescriptivo ni
  fuente de recetas, ordenes ejecutables o MAR.
- Ficha anti-dashboard compactada (#124): el resumen superior quedo como strip
  clinico sobrio; la linea clinica longitudinal sigue siendo el cuerpo principal.
- Ficha jerarquizada (Dev-127): la linea clinica sube como primer cuerpo real,
  el mapa longitudinal queda secundario, el header interno usa conteos y el rail
  oculta rutas/API y detalle tecnico primario en `<details>` nativo.
- Walkthrough clinico unico (Dev-128): el spec canonico atraviesa login, mapa
  hospitalario, consulta ambulatoria, ficha, documentos/papel, auditoria demo,
  hospitalizacion, indicaciones borrador y ficha hospitalizada sin rutas nuevas.
- La identidad clinica sigue siendo `Patient` unico; los contextos se separan
  con `ClinicalEncounter` y la ficha longitudinal reconcilia antecedentes,
  eventos, evoluciones, medicacion, alergias, riesgos, signos y resultados.
- Diagnosticos historicos curados ya existen como lectura separada de problemas
  activos en snapshot, ficha, Assistant Read, papel y resumenes. Siguen derivados
  de `ClinicalEvent` y deben conservar tipo de evento y contexto de encuentro.
- Ambulatorio minimo existe: agenda persistida, preconsulta minima gobernada,
  atencion ambulatoria, resumen de lectura y ficha comun.
- Hospitalizacion minima existe: camas, rondas, ingreso borrador, hoja diaria,
  indicaciones borrador y epicrisis borrador; no equivale a firma, alta legal,
  orden ejecutable ni MAR.
- Documentos/papel existe como proyeccion carta e indice de papel existente;
  adjuntos externos, consentimientos y firma real siguen fuera.
- AI-Chart/Assistant Read existe como apoyo contextual gobernado; la IA resume
  y propone borradores revisables, no decide, no firma y no escribe sin
  confirmacion humana/backend. AI-EVAL sintetico minimo cubre fuentes esperadas,
  falsos positivos y ausencia de consejo terapeutico autonomo.
- AI-Chart agrega candidatos diagnosticos revisables con SNOMED GPS plano,
  CIE-10/CIE-11 y referencias Farreras breves; no confirma diagnosticos.
- P1 clinicos post Dev-154 a Dev-183 quedaron cerrados: matriz de antecedentes,
  metadata de diagnostico historico, alertas completas de vademecum,
  `ended_on` en auditoria de medicacion, read-audit patient-scoped principal,
  minimizacion de auditoria por allowlists, barrido de snapshots completos en
  rutas clinicas y borrado logico de entradas/signos.
- Las superficies clinicas y papel muestran guard visible de desarrollo/no PHI/no
  uso clinico real.
- El registry estructurado de pantallas vive en
  `apps/web/src/lib/screen-capabilities.registry.json`; la tabla de rutas reales
  en `docs/SCREEN_TREE.md` se genera desde ese registry.

## Proximo Objetivo Unico

No ampliar modulos clinicos hasta mantener claro el limite pre-HIS. El siguiente
trabajo permitido debe reducir riesgo operacional o consolidar contrato, no
crear nuevas superficies.

Contrato minimo diferido para ABAC antes de cualquier piloto real:

- Institucion o tenant clinico como frontera obligatoria.
- Equipo/servicio tratante y relacion asistencial verificable.
- Motivo de acceso cuando no exista relacion asistencial activa.
- Break-glass auditado, justificado y revisable.
- Sin implementacion decorativa: primero contrato, tests y politica de uso.

Avance actual: existen stores y contratos para frontera institucional, equipo,
relacion paciente-equipo, membresia actor-equipo, dry-run de relacion
paciente/actor, entidad futura de break-glass, auditoria shadow
`access_context.passive_decision`, evento minimizado `access_context.denied`,
reporte agregado interno de observabilidad ABAC y enforcement dev-only para
`GET /api/v1/patients/{patient_id}`,
`GET /api/v1/patients/{patient_id}/record`, lecturas patient-scoped de
appointments, allergies, active problems, medications y medication drafting
context detras de
`ONEEPIS_ABAC_ENFORCEMENT_ENABLED=true`. Esto no habilita PHI real ni ABAC
productivo: `patient_scoping_enabled`, `abac_runtime_enforced` y
`break_glass_enabled` siguen desactivados en el contrato productivo.

Criterio de no-hacer:

- No crear nueva pantalla clinica.
- No crear modulo de IA nuevo.
- No promover receta, firma, orden ejecutable, UCI, pabellon, adjuntos o
  consentimientos productivos.
- No duplicar el carril farmaco local ya mergeado.
- No abrir PR docs-only salvo que evite dano clinico, seguridad rota, setup roto
  o claim publico falso.

## Gates Obligatorios

- Todo cambio: `npm run check:toolchain`.
- Pantallas/rutas/registry: `npm run check:screens`.
- API o permisos backend: `npm run check:api`.
- UI: `npm run check:web`.
- OpenAPI: `npm run check:contract`.
- Flujo visible o papel: `npm run check:e2e`.
- Cambios transversales: `npm run check`.

CI agrega:

- `security-report`: `gitleaks` y OSV npm high/critical bloqueantes;
  dependency review, CodeQL y `pip-audit` report-only hasta politica explicita.
- `postgres-alembic`: PostgreSQL 15, `alembic upgrade head` desde cero y smoke
  `downgrade -1`/`upgrade head`.

## Riesgos Vivos

- Produccion sanitaria: OneEpis no esta listo para uso clinico real ni software
  certificado.
- Seguridad: faltan secretos formales, cifrado, backups/restore, retencion,
  control contextual por institucion/equipo/relacion asistencial y
  observabilidad productiva PHI-safe formal.
- Identidad: auth local sirve para desarrollo; usuarios persistentes, sesiones
  productivas, revocacion y recuperacion institucional siguen pendientes.
- Permisos: RBAC global actual es minimo; ABAC contextual sigue futuro y debe
  incluir motivo de acceso y break-glass auditado antes de piloto real.
- Auditoria: read-audit, borrado logico y minimizacion de snapshots ya cubren
  las superficies P1 principales, pero falta politica medico-legal completa de
  retencion, exportacion, revision e inmutabilidad formal.
- IA externa: bloqueada hasta gateway PHI, anonimizacion, autorizacion, auditoria
  y politica explicita.
- Legal clinico: firma, receta valida, orden ejecutable, MAR, consentimientos y
  adjuntos productivos siguen bloqueados.

El checklist versionado de no-produccion vive en
`docs/NO_PRODUCTION_CHECKLIST.md`.

## Decisiones Activas

- Paciente une; encounter separa; timeline reconcilia; auditoria prueba; IA
  resume, no decide.
- `screen-capabilities.registry.json` es la fuente de verdad estructurada para
  rutas visibles; `docs/SCREEN_TREE.md` conserva narrativa clinica y la tabla
  generada.
- `docs/CLINICAL_SCENARIO_AUDIT.md` define el walkthrough clinico minimo:
  consulta ambulatoria, hospitalizacion con indicacion borrador y paciente con
  riesgo/alergia/medicacion.
- `npm` 11.13.0 es el package manager oficial; pnpm queda diferido a PR dedicado.
- Los estados validos de pantalla son `completa`,
  `completa/en expansion gobernada`, `preparada`, `bloqueada` y `futura`.
- Una pantalla completa no autoriza claims legales: si hay borrador, guardrail o
  flujo minimo, debe declararse `completa/en expansion gobernada`.
- La proxima mejora debe atravesar un paciente ficticio por un flujo real antes
  que agregar mapa, copy o canon narrativo.
