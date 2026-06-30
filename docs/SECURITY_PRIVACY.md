# Seguridad y Privacidad

## Repositorio Publico

Mientras el repositorio este publico:

- no abrir issues o PRs con datos reales
- no subir capturas con informacion clinica
- no publicar logs, dumps, archivos `.env` ni secretos
- no usar datos que parezcan pertenecer a una persona real
- reportar vulnerabilidades sensibles por canal privado

OneEpis maneja información clínica sensible. Este scaffold no debe considerarse listo para producción sanitaria sin revisión legal, operacional y de seguridad.

El checklist versionado de gates no productivos vive en
`docs/NO_PRODUCTION_CHECKLIST.md`.

## Reglas Iniciales

- No guardar identificadores nacionales en claro. Usar hashes o identificadores internos.
- No escribir datos clínicos en logs.
- No enviar datos clínicos a servicios externos de IA.
- Mantener IA local y auditable con Ollama.
- Registrar eventos relevantes en auditoría.
- Cifrado, control de acceso granular y retención documental quedan como hitos antes de producción.
- Backups, restore, auditoría de accesos, logs PHI-safe, gestión formal de
  secretos y gobernanza legal/clínica son gates explícitos antes de producción.

## Secretos

La gestion formal de secretos sigue pendiente antes de produccion sanitaria.
El contrato ejecutable vive en
`apps/api/src/oneepis_api/core/secret_management_contract.py`.

Antes de cualquier entorno productivo se requiere, como minimo:

- almacenamiento externo de secretos, fuera del repo y archivos locales;
- owners y mantenedores autorizados por secreto;
- politica de rotacion normal, emergencia y revocacion;
- procedimiento de incidente ante filtracion;
- aislamiento entre secretos de desarrollo, staging y produccion.

## Configuracion fuera de Desarrollo

Si `ONEEPIS_ENVIRONMENT` no es `development`, la API rechaza el arranque con:

- `ONEEPIS_AUTH_SECRET` default
- usuarios locales default
- `ONEEPIS_AUTH_ALLOW_DEV_ACTOR_HEADER=true`
- `ONEEPIS_AUTH_ENABLED=false`

## IA Clínica

La IA inicial solo puede:

- resumir texto entregado por el usuario
- ordenar información
- sugerir próximos pasos administrativos o de documentación

La IA no debe:

- diagnosticar de forma autónoma
- reemplazar criterio clínico
- modificar la ficha sin confirmación humana
- usar proveedores externos sin aprobación explícita

## Datos de Desarrollo

Usa pacientes ficticios obvios. Nunca uses nombres, RUT, correos, teléfonos o documentos reales.
