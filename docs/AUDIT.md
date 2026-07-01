# Audit Trail

OneEpis registra auditoria de escritura clinica y lecturas patient-scoped
sensibles. La auditoria es evidencia y trazabilidad; no reemplaza permisos,
ABAC ni validacion clinica.

## Contexto por request

Cada request recibe un `correlation_id`:

- si el cliente envia `X-OneEpis-Correlation-ID`, se respeta;
- si no, la API genera `oneepis-{uuid}`;
- la respuesta devuelve `X-OneEpis-Correlation-ID`.

El evento de auditoria guarda:

- `action`
- `entity_type`
- `entity_id`
- `actor_id`
- `correlation_id`
- `request_method`
- `request_path`
- `created_at`
- `extra_data`

## Read audit

Las lecturas patient-scoped deben registrar evento de lectura con actor,
paciente, ruta y correlacion cuando exponen contexto clinico longitudinal,
medicacion, alergias, problemas, agenda patient-scoped, signos, resultados,
ordenes borrador, AI/Assistant, hospitalizacion o documentos derivados.

Las lecturas patient-scoped gobernadas por ABAC dev-only deben ejecutar
`enforce_patient_scope_for_read` antes de construir snapshots, respuestas IA,
series, busquedas, correlaciones o consultas clinicas. `record_patient_scoped_read`
solo audita la lectura y la decision pasiva; no autoriza por si mismo.

Cuando `ONEEPIS_ABAC_ENFORCEMENT_ENABLED=true`, una denegacion por falta de
relacion asistencial debe emitir `access_context.denied` con metadata minimizada
por claves de requisito, sin retener IDs de equipo, textos libres, valores de
headers ni datos clinicos crudos.

## Access context audit

La auditoria ABAC actual es pre-productiva:

- `access_context.passive_decision` documenta que habria pasado bajo ABAC sin
  bloquear runtime cuando el enforcement no aplica a esa ruta o el flag esta
  apagado.
- `access_context.denied` documenta denegaciones activas del enforcement
  dev-only.
- Los headers contextuales no soportados se rechazan y auditan por nombre de
  header, nunca por valor.

Esto no habilita PHI real, piloto clinico ni ABAC productivo. Antes de uso real
faltan institucion/tenant obligatorio, equipo o servicio tratante, motivo de
acceso operativo, break-glass revisable, retencion medico-legal e identidad
productiva.

## Before / after

Las creaciones guardan snapshot `after` solo con campos permitidos por allowlist.

Las actualizaciones guardan snapshots de campos cambiados:

```json
{
  "fields": ["last_name"],
  "before": { "last_name": "Paciente" },
  "after": { "last_name": "Auditado" }
}
```

Las eliminaciones logicas o fisicas guardan `before` y, cuando aplica, `after`.

Los snapshots de auditoria deben mantenerse minimizados. Campos libres, razones
de override, notas clinicas, textos de indicacion, resultados completos,
prompts, respuestas IA y valores de headers no deben entrar a `extra_data` salvo
contrato explicito, minimizacion y test.

## Reglas

- La auditoria no reemplaza control de permisos.
- Todo evento debe tener actor autenticado salvo modo dev explicito.
- Toda escritura clinica debe tener actor, permisos, auditoria y
  `correlation_id`.
- Toda lectura patient-scoped sensible debe tener auditoria de lectura; si la
  ruta esta en alcance ABAC, tambien debe tener enforcement antes de leer.
- No se deben guardar secretos, tokens, PHI crudo, texto clinico libre, prompts
  o respuestas IA completas en `extra_data`.
- AI/Assistant debe auditar fuente, conteos, decision humana y limites, no texto
  clinico bruto ni diagnostico autonomo.
- Antes de usar datos reales, se debe revisar minimizacion de PHI, retencion,
  integridad e inmutabilidad medico-legal.

## Retencion

La retencion productiva de auditoria no esta implementada. Hasta que exista
politica medico-legal aprobada, OneEpis no debe incorporar purga runtime de
`AuditEvent`.

El contrato ejecutable vive en
`apps/api/src/oneepis_api/core/audit_retention_contract.py` y exige, antes de
produccion o purga, al menos:

- politica de retencion versionada;
- exportacion controlada del log;
- inmutabilidad o evidencia de manipulacion;
- legal hold;
- procedimiento de purga revisado, autorizado y auditado.

## Integridad

La integridad medico-legal productiva de auditoria no esta implementada. El
contrato ejecutable vive en
`apps/api/src/oneepis_api/core/audit_integrity_contract.py`.

Antes de produccion sanitaria, la auditoria debe definir y probar:

- serializacion canonica de cada `AuditEvent`;
- enlace al digest anterior o almacenamiento WORM equivalente;
- version explicita de algoritmo/canonicalizacion;
- anclaje externo a la base mutable o infraestructura WORM;
- procedimiento de verificacion que detecte el primer enlace roto.
