# Permissions Matrix

OneEpis usa roles locales en desarrollo. Esta matriz es el contrato minimo de PR-027.

## Roles

- `admin`: operacion completa de desarrollo.
- `medico`: escritura clinica medica y uso de IA clinica.
- `enfermeria`: lectura y registro acotado de signos vitales, eventos clinicos,
  laboratorio minimo, riesgos clinicos y preconsulta ambulatoria minima.
- `solo_lectura`: lectura clinica sin escrituras.
- `dev`: bypass local gobernado para desarrollo.

Roles clinicos ampliados como estudiante, supervisor/docente, matroneria,
odontologia, farmacia, laboratorio, admision o facturacion siguen pendientes de
contrato propio. No se exponen en login ni se seleccionan manualmente antes de
autenticar.

## Acciones

| Accion | admin | medico | enfermeria | solo_lectura | dev |
| --- | --- | --- | --- | --- | --- |
| Ver pacientes/ficha/auditoria | si | si | si | si | si |
| Crear/editar paciente | si | si | no | no | si |
| Editar estado ficha/contexto | si | si | no | no | si |
| Crear/editar encuentros clinicos generales | si | si | no | no | si |
| Completar preconsulta ambulatoria minima | si | si | si | no | si |
| Crear/editar/cerrar hoja diaria hospitalizada | si | si | no | no | si |
| Crear/editar evolucion SOAP | si | si | no | no | si |
| Crear/editar eventos clinicos de contexto | si | si | si | no | si |
| Crear/editar problemas activos | si | si | no | no | si |
| Crear/editar alergias | si | si | no | no | si |
| Crear/editar medicacion | si | si | no | no | si |
| Registrar signos vitales | si | si | si | no | si |
| Registrar laboratorio minimo | si | si | si | no | si |
| Registrar/corregir riesgos clinicos | si | si | si | no | si |
| Usar IA clinica contextual | si | si | no | no | si |
| Crear/editar/cerrar borrador de indicacion hospitalaria | si | si | no | no | si |
| Firmar indicacion o receta | no | no | no | no | no |

## Reglas

- La UI debe ocultar o deshabilitar acciones no permitidas.
- El backend siempre debe hacer cumplir la matriz aunque la UI oculte botones.
- Toda escritura permitida debe registrar `audit_event` con actor autenticado.
- `X-OneEpis-Actor` solo puede usarse si `ONEEPIS_AUTH_ALLOW_DEV_ACTOR_HEADER=true`.
- Ningun permiso habilita diagnostico autonomo, firma automatica ni escritura IA directa.
- Enfermeria puede completar la preconsulta ambulatoria minima existente:
  encuentro ambulatorio `in_progress` marcado como preconsulta, signos
  opcionales y evento clinico de contexto.
- Ese permiso no abre gestion general de encuentros: enfermeria no puede crear
  hospitalizaciones, encuentros ambulatorios comunes ni actualizar/cancelar
  encuentros.
- Cerrar una hoja diaria bloquea edicion posterior, pero no equivale a firma legal.
- Las indicaciones hospitalarias actuales son borradores auditables con estado `draft` o `closed`; no son orden firmada.
- La receta impresa queda bloqueada hasta tener firma, folio, actor, fecha clinica y politica de prescripcion.
- Estudiantes de salud no tienen rol propio en esta V1. Si se agregan, sus
  acciones clinicas que requieran validacion deben quedar como borrador o
  pre-firma y solo un supervisor/profesional autorizado podra validar o firmar
  cuando exista contrato de firma.

## Acceso inicial

- `/` y `/login` no deben mostrar perfiles, roles, datos clinicos ni accesos a
  modulos antes de iniciar sesion.
- El login exitoso dirige a `/home`, donde cada lugar fisico o servicio se
  habilita segun permisos efectivos ya autenticados.
- La sesion web usa cookie `HttpOnly`; no se guarda bearer productivo en
  `localStorage`.
- Las sesiones nuevas se registran server-side y `logout` revoca el `sid`.
- `refresh` rota el token vigente y reemplaza el hash server-side de la sesion.
- Las mutaciones con cookie requieren header `X-OneEpis-CSRF` pareado con la
  cookie CSRF no HttpOnly.
- Intentos fallidos, bloqueos, recuperacion y desbloqueo se registran como
  eventos de seguridad sin guardar contrasenas, tokens ni datos clinicos.
- Recuperacion y desbloqueo mantienen respuesta generica y limitan solicitudes
  por ventana temporal para reducir abuso sin enumerar usuarios.
- La confirmacion de desbloqueo por token consume el token una sola vez y limpia
  el bloqueo temporal sin revelar si el token era valido.
- El envio de enlaces queda tras `ONEEPIS_AUTH_NOTIFICATION_PROVIDER`; por
  defecto esta deshabilitado y `development_log` solo se permite en desarrollo.
