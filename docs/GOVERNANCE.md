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

## Frontera Documental

No crear documentos nuevos si una fuente existente puede absorber la decision.

Responsabilidades canonicas:

- `README.md`: entrada operativa, stack, comandos y enlaces.
- `docs/CURRENT_STATE.md`: verdad operativa actual.
- `docs/ROADMAP.md`: historial y rumbo, no backlog detallado.
- `docs/GOVERNANCE.md`: criterios anti-inflacion y limites activos.
- `docs/PROGRESSIVE_DEVELOPMENT_PLAN.md`: fases AI-Chart.
- `docs/AI_CHART_CORE.md`: contrato conceptual de AI-Chart.
- `docs/VISUAL_INTELLIGENCE_COUPLING.md`: regla inteligencia -> UI visible.
- `docs/SCREEN_TREE.md`: rutas y estado por superficie.

Los documentos largos de vision son cantera conceptual. No son backlog directo
si no pasan antes por el plan progresivo y la escalera OneEpis.

## Politica de Pantallas

Toda pantalla clinica debe tener un estado explicito en `docs/SCREEN_TREE.md`:

- `completa`: tiene flujo humano minimo y, si escribe, API/PostgreSQL/permisos/auditoria/OpenAPI/tests.
- `completa/en expansion gobernada`: funciona, pero tiene un subdominio acotado en crecimiento con guardrails activos.
- `preparada`: existe como borde visible, declara que esta pendiente y no simula produccion.
- `bloqueada`: existe o se nombra para evitar uso clinico hasta completar requisitos legales/clinicos.
- `futura`: pertenece al mapa maestro, pero no tiene ruta o contrato listo.

Reglas:

- Ninguna pantalla nueva entra sin estado explicito en `docs/SCREEN_TREE.md`.
- Todo PR que agregue, quite o mueva una ruta visible bajo `apps/web/src/app` debe actualizar `docs/SCREEN_TREE.md`.
- Todo PR que agregue, quite o mueva una ruta visible bajo `apps/web/src/app` debe actualizar el Screen Capability Registry.
- El guard `npm run check:screens` debe fallar si una ruta visible queda sin fila documentada, sin `ScreenCapability` o duplicada en el mapa/registry.
- Una pantalla preparada debe mostrar su estado pendiente en UI y quedar cubierta por E2E si es visible.
- Una pantalla completa exige contrato backend antes de UI amplia si maneja datos clinicos nuevos.
- Una pantalla promovida a completa debe actualizar en el mismo PR: `docs/SCREEN_TREE.md`, Screen Capability Registry, E2E smoke y `docs/CURRENT_STATE.md`.
- Si escribe, debe tener permisos, auditoria, actor, `correlation_id`, OpenAPI y test API.
- Si produce documento clinico, debe tener papel carta o declarar explicitamente que no tiene papel aun.
- No se promueve una pantalla por apariencia: debe cerrar un acto clinico real.
- El orden del producto es `paciente -> episodio -> acto clinico -> documento -> firma/estado -> seguimiento`.
- Receta valida, firma clinica, folio, despacho, administracion de medicamentos, ordenes ejecutables, agenda productiva e IA externa siguen bloqueadas/futuras hasta cumplir su contrato clinico/legal.

Reglas IA por pantalla:

- Cada ruta clinica visible debe declarar IA permitida en el Screen Capability Registry.
- Las acciones IA permitidas son cerradas: lectura, resumen, busqueda, series, validacion, borrador y propuesta de patch.
- Una pantalla sin capacidad declarada no puede ejecutar comandos IA dirigidos.
- Si la UI no encuentra `ScreenCapability`, debe bloquear IA por defecto.
- Ollama solo puede apoyar redaccion/resumen cuando la pantalla lo permita; las reglas locales y datos estructurados mantienen autoridad.
- `ClinicalPatch` solo puede aparecer en pantallas que lo declaren y siempre requiere confirmacion humana y auditoria backend.

## Limites Activos

No construir ahora:

- dashboard central nuevo
- chat libre generico
- receta valida o firma clinica real
- indicaciones ejecutables
- agenda productiva
- RAG documental amplio
- IA externa identificada
- importador PDF completo

PR #1, AI-Chart Nivel 0 y `PROG-ASSISTANT-READ-01` ya quedaron cerrados en
`v0.4-assistant-read`. El proximo avance debe partir desde `main` verde y
volver al tronco clinico tradicional.

Programa activo permitido: `PROG-PATIENT-CORE-01`.

Objetivo: completar nucleo paciente como ficha tradicional antes de ampliar IA:
antecedentes leidos desde fuentes existentes, linea clinica, laboratorio sobrio,
eventos curados y preparacion contractual de ambulatorio/hospitalizacion.

Trabajo permitido inmediato:

- conciliar documentos canonicos post `v0.4`
- mostrar antecedentes de solo lectura dentro de la ficha existente
- curar eventos clinicos como antecedentes/diagnosticos/procedimientos sin crear tabla nueva
- consolidar laboratorio minimo en ficha y AI-Chart con fuentes especificas
- documentar contratos futuros antes de crear agenda, ingreso medico o epicrisis

Trabajo no permitido inmediato:

- nueva IA, chat libre, RAG, IA externa o paquetes/agentes nuevos
- dashboard central o pantalla dedicada de laboratorio
- receta valida, firma clinica, folio, despacho, orden ejecutable o administracion de medicamentos
- agenda productiva, ingreso medico o epicrisis sin contrato backend previo
- otro PR grande que mezcle frontend, backend, contratos y roadmap sin particion clara

Regla para el siguiente bloque clinico tradicional:

- elegir una sola superficie de `docs/SCREEN_TREE.md` -> `Contratos minimos antes de UI amplia`
- implementar primero el contrato backend o reutilizacion explicita de entidades existentes
- recien despues agregar UI minima y papel si la superficie produce documento clinico
- no mezclar agenda, ingreso medico y epicrisis en el mismo PR
- si la superficie no cumple su contrato, permanece `preparada`, `futura` o `bloqueada`

## Lecciones Post #15-#17

Los avances de agenda, resumen ambulatorio e indice de papel mostraron errores
evitables que no deben repetirse:

- no promover una ruta sin reconciliar todos los documentos canonicos afectados
- no dejar textos de pantalla preparada cuando la UI ya muestra datos reales
- no usar selectores E2E ambiguos si el mismo texto aparece en badges,
  descripciones o listas; usar `exact: true` o scope por card/region
- no seguir agregando comportamiento a archivos entre 300 y 350 lineas; primero
  extraer componentes pequenos y luego agregar funcionalidad
- no contar adjuntos, firma, receta valida o consentimientos como completos solo
  porque exista un indice de papel

## Seguridad CI Report-Only

- El job `security-report` debe entregar senales de secretos, dependencias y analisis estatico sin bloquear el piloto por ruido inicial.
- Gitleaks, dependency review, CodeQL, `npm audit` y `pip-audit` quedan en modo reporte hasta que se establezca una politica de bloqueo explicita.
- Un secreto real o PHI real detectado debe tratarse como incidente aunque el job este en modo report-only.

## Escalera OneEpis

Antes de crear una feature, pantalla, endpoint, dependencia o documento, responde en orden:

1. Debe existir?
2. Pertenece al flujo paciente/ficha/papel?
3. Ya lo cubre API/PostgreSQL/auditoria/permisos?
4. Puede entrar como una pantalla o accion minima?
5. Solo entonces implementa lo minimo verificable.

Si una respuesta es "no" o "todavia no", no lo agregues al core. Dejale una nota breve en el plan vivo si realmente importa.

## Algoritmo Anti-Engorda

Usa este algoritmo antes de cualquier avance automatico de fase:

1. Identifica la fase activa en `docs/PROGRESSIVE_DEVELOPMENT_PLAN.md`.
2. Elige un solo incremento que mejore esa fase sin abrir otra superficie.
3. Rechaza el incremento si necesita dashboard, chat libre, RAG, IA externa, documento nuevo o modulo nuevo.
4. Rechaza el incremento si no puede verse, revisarse o auditarse en una pantalla existente.
5. Reusa API, componentes, servicios y tests existentes antes de crear archivos.
6. Si un archivo existente supera el presupuesto, extrae primero una pieza pequena y luego agrega comportamiento.
7. Si la feature escribe ficha, debe pasar por API, permisos, auditoria, OpenAPI y confirmacion humana.
8. Si la feature solo infiere, debe mostrar fuente, razon, faltante o limite.
9. Si no hay prueba enfocada posible, reduce el alcance hasta que exista.
10. Actualiza solo los documentos canonicos afectados.

Salida obligatoria de cada incremento:

- un cambio funcional pequeno
- una prueba o gate que cubra el comportamiento
- diff sin archivos ajenos
- contrato actualizado solo si cambio la API
- plan vivo actualizado solo si cambia el estado real

Reglas duras de no engorda:

- No crear carpeta nueva para una sola funcion.
- No crear componente nuevo si el bloque entra limpio en un componente existente.
- No crear endpoint nuevo si una intencion o ruta existente puede expresar el caso.
- No crear documento nuevo si `CURRENT_STATE`, `GOVERNANCE`, `PROGRESSIVE_DEVELOPMENT_PLAN` o `AI_CHART_CORE` pueden absorber la decision.
- No sumar dependencia para reglas, parsing o UI que el stack actual ya resuelve.
- No mover codigo a paquete compartido hasta que existan dos consumidores reales.
- No dejar placeholders, pantallas puente ni rutas vacias.
- No mezclar refactor grande con feature clinica.
- No usar fallback silencioso al primer paciente, documento o registro cuando la ruta trae un ID concreto.

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

## Politica de Vademecum y Dosis

El vademecum ayuda a registrar medicacion activa; no convierte OneEpis en motor de prescripcion.

Reglas:

- El catalogo operativo es local, versionado y curado por humanos.
- FDA/openFDA, Drugs@FDA, FAERS, enforcement e ISP/ANAMED pueden citarse como evidencia, pero no autorizan reglas automaticas sin revision local.
- La UI clinica no consulta FDA/openFDA en vivo.
- Ningun rango de dosis entra sin fuente, version, estado de revision y responsable curador.
- Si no hay regla aplicable, la UI debe decir que no hay regla segura disponible.
- Alertas de dosis fuera de rango bloquean el guardado hasta que exista justificacion humana.
- El override debe quedar auditado con snapshot de regla, fuente, severidad y razon.
- Reglas pediatricas, embarazo, funcion renal/hepatica, interacciones y alergias cruzadas quedan fuera salvo regla explicita curada.
- Favoritos, sugeridos e historial son apoyo de borrador; no crean receta valida, orden ejecutable, firma, folio ni despacho.

## Reglas de Crecimiento

- Agrega dependencias solo si remueven complejidad real y no duplican capacidades existentes.
- Manten los modulos enfocados en una responsabilidad clinica o tecnica.
- Evita abstracciones genericas hasta que haya dos usos reales.
- No aceptes fixtures con datos sensibles o realistas.
- No aceptes fixtures, seeds o pacientes de desarrollo con nombres de proyectos previos.
- No copies releases completos de SNOMED CT dentro del repo; usa codigos en ficha y repositorios/servidores terminologicos externos licenciados.
- No crees un documento nuevo si puedes actualizar uno existente.
- No agregues scripts nuevos si un comando existente puede expresar el gate.
- Actualiza OpenAPI cuando cambie la API.
- Mientras los tipos TS sigan manuales, todo cambio Assistant Read debe pasar el drift check de contrato.
- Route Handlers de Next pueden actuar como BFF de interaccion/streaming IA, pero no deben duplicar permisos, auditoria ni escritura clinica de FastAPI.
- Toda propuesta IA que pueda escribir ficha debe pasar por `ClinicalPatch` y confirmacion backend.
- Todo patch aceptado debe declarar confirmacion humana obligatoria; las evoluciones AI-Chart solo pueden persistir como borrador no firmado.

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
- El gate `npm run check:size` aplica un limite duro de 350 lineas en `apps/api/src/oneepis_api` y `apps/web/src`.
- El reporte near-limit de `check:size` no bloquea CI; cualquier archivo listado debe entrar a watchlist y extraerse antes de agregarle comportamiento nuevo.
- Toda excepcion al limite debe vivir en `scripts/check-file-size.mjs` con razon y tope explicito; no se aceptan excepciones implicitas en PR.
- Un componente UI debe preferir composicion antes que props infinitas.
- Un servicio backend debe expresar reglas de dominio, no consultas mezcladas con controladores grandes.
- Si un modulo queda a medias, no entra: debe tener flujo humano minimo, permisos, auditoria si escribe y estado empty/error/loading cuando aplique.

### Presupuesto AI-Chart

AI-Chart debe crecer por componentes pequenos y actos clinicos cerrados.

- La pagina `patient-ai-chart-pages.tsx` es solo orquestador.
- Los componentes AI-Chart no deben transformarse en mini paginas.
- Si un componente supera el presupuesto, extraer subpaneles antes de agregar comportamiento.
- `ai-chart-utils.ts` es soporte visual; no debe acumular reglas clinicas de dominio.
- Nuevas intenciones deben pasar por API, tests y correlato visual antes de llegar a UI.
