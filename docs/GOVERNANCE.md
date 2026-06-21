# Gobierno Tecnico

Este repo debe ser facil de desarrollar, mantener y corregir por humanos y agentes IA sin crecimiento descontrolado.

## Doctrina Anti-Inflacion

OneEpis debe crecer como ficha clinica sobria, no como capas acumuladas de dashboard, labs, IA y modulos incompletos.

La columna vertebral es:

- paciente
- ficha
- papel serio
- API clara
- PostgreSQL
- auditoria
- permisos
- OpenAPI
- IA local opcional

Evita explicitamente:

- inflacion de modulos sin flujo clinico completo
- legacy temprano: barrels eternos, pantallas puente y rutas placeholder
- tres capas superpuestas: core clinico, dashboard operacional y laboratorio IA compitiendo entre si
- dashboard como centro del producto
- labs pegados al core
- IA protagonista o capaz de escribir/firma ficha automaticamente
- modo papel secundario
- pantallas abarrotadas
- scripts, docs y gates infinitos que nadie entiende

## Escalera OneEpis

Antes de crear una feature, pantalla, endpoint, dependencia o documento, responde en orden:

1. Debe existir?
2. Pertenece al flujo paciente/ficha/papel?
3. Ya lo cubre API/PostgreSQL/auditoria/permisos?
4. Puede entrar como una pantalla o accion minima?
5. Solo entonces implementa lo minimo verificable.

Si una respuesta es "no" o "todavia no", no lo agregues al core. Dejale una nota breve en el plan vivo si realmente importa.

## Politica de Indicaciones y Receta

Indicaciones y recetas son escritura clinica de alto riesgo. No entran al core como pantalla suelta, laboratorio IA ni impresion decorativa.

Reglas base:

- Una indicacion debe pertenecer a un paciente y, si aplica, a un encuentro clinico.
- La fuente de verdad debe ser PostgreSQL via API; la UI y el papel son proyecciones.
- Toda escritura debe tener permisos, actor autenticado, auditoria, `correlation_id` y OpenAPI.
- IA puede ayudar a revisar texto como borrador, pero no crea, firma ni activa indicaciones o recetas.
- Una receta no se genera automaticamente desde medicacion activa.

Estados permitidos:

- `draft`: borrador editable, no ejecutable, no firmado y visible como tal en UI y papel.
- `closed`: bloquea edicion posterior para preservar trazabilidad, pero no equivale a firma legal.
- `signed`: estado futuro; requiere regla explicita de firma, identidad del profesional, sello temporal, folio y documento inmutable.

Hasta implementar firma real, OneEpis solo puede aceptar indicaciones como borrador gobernado. La ruta de receta puede existir como papel bloqueado de desarrollo, pero no debe emitir receta clinica valida.

Permisos futuros minimos:

- `admin`, `medico` y `dev` pueden crear/editar borradores si existe backend.
- `enfermeria` puede leer indicaciones cuando el flujo lo necesite, pero no crearlas ni firmarlas.
- `solo_lectura` solo lee.
- Nadie firma recetas o indicaciones mientras no exista modulo de firma gobernado.

Papel obligatorio:

- Todo papel de indicacion o receta debe mostrar estado (`draft`, `closed` o `signed` futuro).
- Todo papel no firmado debe decir `Documento de desarrollo / no uso clinico real.`
- El papel no puede ocultar que una indicacion es borrador.
- Si no hay folio, actor, fecha clinica y permisos claros, no se imprime como documento clinico valido.

## Reglas de Crecimiento

- Agrega dependencias solo si remueven complejidad real y no duplican capacidades existentes.
- Manten los modulos enfocados en una responsabilidad clinica o tecnica.
- Evita abstracciones genericas hasta que haya dos usos reales.
- No aceptes fixtures con datos sensibles o realistas.
- No aceptes fixtures, seeds o pacientes de desarrollo con nombres de proyectos previos.
- No crees un documento nuevo si puedes actualizar uno existente.
- No agregues scripts nuevos si un comando existente puede expresar el gate.
- Actualiza OpenAPI cuando cambie la API.

## Nuevas Dependencias

Antes de sumar una dependencia, registra en el PR:

- problema que resuelve
- alternativas consideradas
- costo de mantenimiento
- superficie de seguridad

Para cambios grandes, crea un ADR solo si una decision quedaria opaca sin ese registro.

## Revisiones

Todo PR debe responder:

- Que cambia para el usuario clinico.
- Que cambia en el contrato API.
- Que migraciones o datos toca.
- Que riesgo de privacidad introduce.
- Que prueba cubre el comportamiento.
- Como evita inflacion, legacy temprano o capas superpuestas.

## Presupuesto de Complejidad

- Un archivo de aplicacion no deberia superar 300 lineas sin una razon clara.
- Un componente UI debe preferir composicion antes que props infinitas.
- Un servicio backend debe expresar reglas de dominio, no consultas mezcladas con controladores grandes.
- Si un modulo queda a medias, no entra: debe tener flujo humano minimo, permisos, auditoria si escribe y estado empty/error/loading cuando aplique.
