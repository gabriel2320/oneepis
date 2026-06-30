# Audit Trail

OneEpis registra auditoria por cada escritura clinica.

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

## Before / after

Las creaciones guardan snapshot `after`.

Las actualizaciones guardan snapshots de campos cambiados:

```json
{
  "fields": ["last_name"],
  "before": { "last_name": "Paciente" },
  "after": { "last_name": "Auditado" }
}
```

Las eliminaciones logicas o fisicas guardan `before` y, cuando aplica, `after`.

## Reglas

- La auditoria no reemplaza control de permisos.
- Todo evento debe tener actor autenticado salvo modo dev explicito.
- No se deben guardar secretos ni tokens en `extra_data`.
- Antes de usar datos reales, se debe revisar minimizacion de PHI y retencion.

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
