# Codex Plan

Guia corta para agentes. No es backlog, roadmap ni changelog completo.

Fuentes vivas:

- Estado operativo: `docs/CURRENT_STATE.md`
- Reglas de gobierno: `docs/GOVERNANCE.md`
- No-produccion: `docs/NO_PRODUCTION_CHECKLIST.md`
- Rutas visibles: `docs/SCREEN_TREE.md`
- Historial cronologico: `docs/ROADMAP.md`
- Fases AI-Chart: `docs/PROGRESSIVE_DEVELOPMENT_PLAN.md`

## Regla Madre

```text
1 objetivo clinico
1 cambio acotado
tests/gates
OpenAPI actualizado si cambia API
docs vivas sincronizadas si cambia estado
sin datos reales
```

## Contexto Minimo Por PR

1. Leer `docs/CURRENT_STATE.md`.
2. Leer `docs/GOVERNANCE.md`.
3. Leer el archivo o contrato del dominio tocado.
4. Revisar diff actual y tests cercanos.
5. No cargar docs historicos salvo que el cambio sea historico.

## No Negociable

- No usar datos reales, PHI, secretos, dumps ni logs clinicos.
- No implementar diagnostico autonomo.
- No firmar, recetar, ejecutar ordenes ni escribir ficha desde IA.
- No abrir rutas, pantallas, dependencias o documentos nuevos sin necesidad
  ejecutable.
- Toda escritura clinica debe tener actor, permisos, auditoria y
  `correlation_id`.
- Todo cambio de API debe actualizar `packages/contracts/openapi.json`.
- Ninguna ruta clinica o print con ID puede mostrar un primer registro como
  fallback.
- Ningun archivo clinico nuevo debe superar 350 lineas sin excepcion explicita.

## Carriles De Validacion

- `fast`: bug acotado. Usar `npm run check:toolchain` y test dirigido.
- `clinical`: permisos, auditoria, IA, medicacion, diagnosticos, escritura
  clinica o seguridad. Usar `npm run check:toolchain`, `npm run check:api` y
  `npm run check:contract` si aplica.
- `surface`: ruta, copy visible, papel, registry o flujo E2E. Usar
  `npm run check:toolchain`, `npm run check:web`, `npm run check:screens` y E2E
  dirigido si aplica.
- `release`: barrido completo. Usar `npm run check`.

CI debe quedar verde antes de mergear.

## Sincronizacion Documental Obligatoria

Al final de cada PR que cambie plan, avance, estado, seguridad o no-produccion,
actualizar en conjunto los documentos vivos afectados:

- `docs/CURRENT_STATE.md`: solo estado vigente y siguiente objetivo.
- `docs/CODEX_PLAN.md`: solo handoff inmediato para agentes.
- `docs/NO_PRODUCTION_CHECKLIST.md`: solo gates/evidencia no-produccion.
- `docs/SCREEN_TREE.md`: solo si cambia registry/rutas/pantallas.
- Doc de dominio: solo si cambia una regla persistente de ese dominio.

No mantener una segunda lista de estado en `ROADMAP`, reportes fechados ni docs
de vision. No crear snapshots nuevos.

## Handoff 2026-07-02

- `main` sincronizado con `origin/main`.
- Ultimo PR sincronizado: #292, write ABAC dev-only para clinical events
  confirmado en GitHub.
- Commits directos post-#292 en `origin/main`: `962162d` consolida seguridad,
  contratos, auth web y print audit policy; `2635a58` corrige dependencias del
  carril contracts; `52cdc4d` actualiza CodeQL a v4. Estos commits no consumen
  numeracion de PR en GitHub.
- PR #293-#300 quedan como draft/stack de seguridad, operaciones y catalogos.
  El trabajo local actual apilado corresponde a PR #301, Screen-Service Matrix.
- Read ABAC dev-only cubre el core patient-scoped declarado en
  `docs/CURRENT_STATE.md`.
- Write ABAC dev-only cubre `vital_signs`, `clinical_risks`,
  `clinical_entries`, `clinical_events`, `clinical_orders`, `encounters`,
  `medications`, `allergies`, `active_problems`, `appointments`,
  `lab_panels_results`, `hospital_daily_sheets` y `hospital_indications`.
- El inventario patient-scoped se verifica contra OpenAPI para toda operacion
  `GET/POST/PATCH/DELETE` con `{patient_id}`.
- `audit_snapshot` exige allowlist explicita; `npm run check:audit-snapshots`
  bloquea llamadas sin fields en rutas API.
- Las rutas print patient-scoped declaran `read_audit`; `npm run check:screens`
  falla si un print con `[patientId]` queda con `auditPolicy: none`.
- La web ya no lee bearer desde `localStorage`; usa cookie `HttpOnly` + CSRF y
  `npm run check:web-auth-contract` bloquea regresiones.
- Con auth habilitada, un token firmado sin `sid` activo se rechaza antes de
  acceder a rutas patient-scoped.
- Ninguna escritura tiene ABAC runtime productivo.
- `security-report` bloquea Gitleaks, OSV npm high/critical y `pip-audit`
  high/critical; dependency review y CodeQL siguen report-only con baseline y
  waiver versionados.
- Observabilidad PHI-safe formal queda en contrato ejecutable: `correlation_id`,
  logs JSON sin PHI, labels de metricas permitidos y exportadores/dashboards
  productivos deshabilitados.
- SEC-001/002/003 quedan atados a contratos ejecutables de secretos, cifrado y
  backups/restore, sin habilitar runtime productivo ni PHI real.
- Auth productiva queda definida como contrato OIDC/SAML/MFA/claims/sesion sin
  tocar login runtime ni usuarios productivos.
- Integridad medico-legal de auditoria queda como contrato para hash-chain,
  version de algoritmo, verificacion, legal hold y export control, sin runtime.
- Reproducibilidad Python usa `apps/api/requirements.lock`, validado desde
  `check:toolchain`, y la cache CI de Python depende del lock.
- HIS Service Catalog v0 nombra servicios y bloquea runtime ABAC/IA externa.
- Clinical Act Catalog v0 mapea actos humanos a servicios HIS y bloquea IA autonoma.
- Screen-Service Matrix v0 conecta pantallas escribibles con servicio, acto,
  backend y madurez.

Secuencia recomendada desde el arbol local post-#301:

1. PR #302: AI Capability Catalog local, sin IA externa ni escritura autonoma.
2. PR #303: Unit of Work para un acto clinico compuesto.

No avanzar a runtime write ABAC, break-glass runtime, firma, receta valida ni
orden ejecutable sin plan clinico/legal separado.

## Fuera De Alcance

- PHI real o piloto clinico.
- Receta valida, firma, MAR u orden ejecutable.
- Adjuntos/consentimientos productivos.
- IA externa.
- Dashboard o macro-HIS.
- Headers contextuales aceptados.
- Break-glass runtime.
