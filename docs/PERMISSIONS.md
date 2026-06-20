# Permissions Matrix

OneEpis usa roles locales en desarrollo. Esta matriz es el contrato minimo de PR-027.

## Roles

- `admin`: operacion completa de desarrollo.
- `medico`: escritura clinica medica y uso de IA clinica.
- `enfermeria`: lectura y registro de signos vitales.
- `solo_lectura`: lectura clinica sin escrituras.
- `dev`: bypass local gobernado para desarrollo.

## Acciones

| Accion | admin | medico | enfermeria | solo_lectura | dev |
| --- | --- | --- | --- | --- | --- |
| Ver pacientes/ficha/auditoria | si | si | si | si | si |
| Crear/editar paciente | si | si | no | no | si |
| Crear/editar evolucion SOAP | si | si | no | no | si |
| Crear/editar alergias | si | si | no | no | si |
| Crear/editar medicacion | si | si | no | no | si |
| Registrar signos vitales | si | si | si | no | si |
| Usar IA clinica contextual | si | si | no | no | si |

## Reglas

- La UI debe ocultar o deshabilitar acciones no permitidas.
- El backend siempre debe hacer cumplir la matriz aunque la UI oculte botones.
- Toda escritura permitida debe registrar `audit_event` con actor autenticado.
- `X-OneEpis-Actor` solo puede usarse si `ONEEPIS_AUTH_ALLOW_DEV_ACTOR_HEADER=true`.
- Ningun permiso habilita diagnostico autonomo, firma automatica ni escritura IA directa.
