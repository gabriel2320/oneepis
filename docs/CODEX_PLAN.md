# Codex Plan

Guia breve para cambios hechos por agentes. El historial vive en
`docs/ROADMAP.md`; el estado operativo vive en `docs/CURRENT_STATE.md`; la
decision anti-inflacion vive en `docs/GOVERNANCE.md`.

## Regla madre

Construir OneEpis por ladrillos clinicos verificables:

```text
1 objetivo clinico
1 cambio acotado
tests/gates
OpenAPI actualizado si cambia API
docs minimas
sin datos reales
```

## No negociable

- No usar datos reales ni datos demo realistas.
- No implementar diagnostico autonomo.
- No firmar ni escribir ficha desde IA.
- No imprimir receta clinica valida sin firma, folio, actor, fecha clinica y permisos claros.
- No agregar dependencias sin justificacion.
- No dejar TypeScript roto.
- No dejar endpoints sin tests.
- Toda escritura clinica debe tener actor, permisos, auditoria y `correlation_id`.
- Todo cambio de API debe actualizar `packages/contracts/openapi.json`.
- Frontend no debe usar datos demo salvo `NEXT_PUBLIC_DEMO_MODE=true`.

## Loop de trabajo

1. Leer `docs/CURRENT_STATE.md`, `docs/GOVERNANCE.md` y el doc del dominio tocado.
2. Entender cambios existentes en el working tree sin revertir trabajo ajeno.
3. Implementar solo el objetivo.
4. Ejecutar gates proporcionales al cambio.
5. Actualizar docs solo si cambia comportamiento o decision.
6. Entregar resumen, pruebas y riesgos.

## Criterio de producto

OneEpis debe sentirse como mesa clinica viva:

- paciente al centro
- ficha y papel como proyecciones clinicas serias
- auditoria visible
- IA local util, silenciosa y trazable
- dashboards, chat libre y modulos incompletos fuera del core

## Expansion formal de ficha

La ficha crece por microprocesos seriales. Cada microproceso debe cerrar una
pieza completa antes de abrir la siguiente:

```text
auditoria -> contrato -> tabla duena -> API -> OpenAPI -> cliente TS -> pantalla -> papel -> permisos -> auditoria -> gates
```

Reglas de avance:

- Un microproceso toca un solo dominio clinico.
- No se crea pantalla si la ruta no existe en `docs/SCREEN_TREE.md`.
- No se crea tabla si el dato ya tiene tabla duena.
- No se agrega dependencia salvo que quite complejidad real y quede justificada.
- Si hay escritura clinica, backend decide permisos y registra auditoria.
- Si hay papel, debe usar la misma fuente que la pantalla y mostrar estado legal.
- Si no hay firma, folio, actor y regla documental, el papel declara desarrollo/no uso clinico real.
- Si el dominio no puede pasar gates proporcionales, se reduce alcance.

### MP-00 Trazabilidad base

Objetivo: mantener mapa vivo antes de crecer.

Alcance:

- Ejecutar `npm run audit:variables` para variables de paciente.
- Ejecutar `npm run audit:traceability` para dominios clinicos.
- Resolver solo brechas de contrato o documentar brechas de tabla duena.

Gates:

```bash
npm run audit:variables
npm run audit:traceability
npm run check:web
npm run check:api
```

Salida: reporte actualizado y siguiente microproceso elegido.

### MP-01 Identidad y contacto paciente

Objetivo: cerrar drift entre backend y frontend para identidad/contacto sin
crear nuevas pantallas.

Tablas:

- `patients`

Pantallas autorizadas:

- `/pacientes`
- `/pacientes/nuevo`
- `/pacientes/[patientId]`
- `/pacientes/[patientId]/ficha`
- `/pacientes/[patientId]/estado`

Trabajo permitido:

- Alinear tipos TS con `PatientRead` si el backend ya expone el campo.
- Mostrar contacto/emergencia solo si no aumenta riesgo de privacidad visual.
- Mantener `document_id_hash` fuera de UI salvo decision explicita.

Trabajo prohibido:

- Nueva tabla de contacto.
- Nueva ruta de identidad.
- Busqueda por documento real.

Gates:

```bash
npm run audit:variables
npm run check:web
npm run check:api
```

### MP-02 Encuentro como eje de episodio

Objetivo: asegurar que atencion ambulatoria, hospitalizacion y actos clinicos
usen `clinical_encounters` cuando corresponde.

Tablas:

- `clinical_encounters`
- referencias existentes desde `clinical_entries`
- referencias existentes desde `clinical_events`

Pantallas autorizadas:

- `/pacientes/[patientId]/encuentros`
- `/pacientes/[patientId]/encuentros/nuevo`
- `/consulta/pacientes/[patientId]/atencion`
- `/hospitalizacion`
- `/hospitalizacion/camas`

Trabajo permitido:

- Mejorar seleccion visible de encuentro activo.
- Mostrar cuando un acto queda sin encuentro.
- Bloquear asociaciones inconsistentes paciente/encuentro.

Trabajo prohibido:

- Agenda productiva.
- Dashboard central.
- Nuevo modulo de episodios fuera de ficha.

Gates:

```bash
npm run check:api
npm run check:web
npm run check:contract
```

### MP-03 Evolucion SOAP formal

Objetivo: consolidar la evolucion como documento narrativo primario,
vinculado a paciente y encuentro cuando exista.

Tablas:

- `clinical_entries`

Pantallas autorizadas:

- `/pacientes/[patientId]/evoluciones`
- `/pacientes/[patientId]/evoluciones/nueva`
- `/pacientes/[patientId]/evoluciones/desde-eventos`
- `/print/pacientes/[patientId]/evolucion/[entryId]`

Trabajo permitido:

- Estados claros `draft`, `signed` futuro y `amended`.
- Papel carta que indique estado y fuente.
- Mantener entrada escrita solo via API con permisos y auditoria.

Trabajo prohibido:

- Firma real.
- Edicion libre despues de cierre/firma futura.
- IA escribiendo evolucion sin `ClinicalPatch` confirmado.

Gates:

```bash
npm run check:api
npm run check:web
npm run check:contract
npm run check:e2e
```

### MP-04 Eventos longitudinales

Objetivo: usar `clinical_events` como linea comun para hechos clinicos,
timeline, IA y papel.

Tablas:

- `clinical_events`

Pantallas autorizadas:

- `/pacientes/[patientId]/eventos`
- `/pacientes/[patientId]/evoluciones/desde-eventos`
- `/pacientes/[patientId]/ai-chart`

Trabajo permitido:

- Exigir `source_type` y `source_ref` cuando el evento nace de otra entidad.
- Mostrar fuente y destino antes de confirmar.
- Reducir duplicacion entre texto SOAP y hechos estructurados.

Trabajo prohibido:

- Evento autonomo generado por IA sin revision humana.
- Timeline como dashboard paralelo.

Gates:

```bash
npm run audit:traceability
npm run check:api
npm run check:web
npm run check:contract
```

### MP-05 Listas clinicas activas

Objetivo: cerrar alergias, medicacion, problemas activos y signos vitales como
listas estructuradas de ficha.

Tablas:

- `allergies`
- `medications`
- `active_problems`
- `vital_signs`

Pantallas autorizadas:

- `/pacientes/[patientId]/alergias`
- `/pacientes/[patientId]/alergias/nueva`
- `/pacientes/[patientId]/medicacion`
- `/pacientes/[patientId]/medicacion/nueva`
- `/pacientes/[patientId]/problemas`
- `/pacientes/[patientId]/problemas/nuevo`
- `/pacientes/[patientId]/signos-vitales`
- `/pacientes/[patientId]/signos-vitales/nuevo`

Trabajo permitido:

- Mantener altas/cambios/anulaciones auditadas.
- Crear `ClinicalEvent` solo cuando el dato deba entrar al timeline.
- Mostrar estado activo/resuelto/error sin duplicar verdad.

Trabajo prohibido:

- Receta valida desde medicacion activa.
- Orden ejecutable desde medicacion.
- Nueva tabla por resumen derivado.

Gates:

```bash
npm run audit:traceability
npm run check:api
npm run check:web
npm run check:contract
```

### MP-06 Papel formal de ficha

Objetivo: hacer que la salida imprimible sea proyeccion seria, no nueva fuente.

Tablas:

- ninguna nueva por defecto

Pantallas autorizadas:

- `/print/pacientes/[patientId]/ficha`
- `/print/pacientes/[patientId]/resumen`
- `/print/pacientes/[patientId]/evolucion/[entryId]`
- `/print/hospitalizacion/rondas`
- `/print/hospitalizacion/pacientes/[patientId]/hoja-diaria/[sheetId]`
- `/print/hospitalizacion/pacientes/[patientId]/indicacion/[indicationId]`

Trabajo permitido:

- Mostrar IDs fuente, estado documental y fecha clinica.
- Reusar clientes/API existentes.
- Separar componentes si `clinical-print.tsx` crece mas.

Trabajo prohibido:

- Papel que inventa datos.
- Fallback silencioso a otro documento.
- Receta clinica valida.

Gates:

```bash
npm run check:web
npm run check:e2e
```

### MP-07 Hospitalizacion gobernada

Objetivo: expandir hospitalizacion solo desde flujos ya reales: cama,
hoja diaria e indicacion borrador.

Tablas:

- `hospital_beds`
- `hospital_daily_sheets`
- `hospital_indications`
- `clinical_encounters`

Pantallas autorizadas:

- `/hospitalizacion`
- `/hospitalizacion/camas`
- `/hospitalizacion/camas/nueva`
- `/hospitalizacion/rondas`
- `/hospitalizacion/pacientes/[patientId]/hoja-diaria`
- `/hospitalizacion/pacientes/[patientId]/hoja-diaria/[sheetId]/editar`
- `/hospitalizacion/pacientes/[patientId]/indicaciones`

Trabajo permitido:

- Mejorar cierre, bloqueo y papel de borrador.
- Reforzar fecha clinica local y ventana de ingreso.
- Mantener indicaciones como borrador/cerrado, no firmado.

Trabajo prohibido:

- Orden ejecutable.
- Firma clinica.
- Administracion de medicamentos.
- Nuevo dashboard hospitalario.

Gates:

```bash
npm run check:api
npm run check:web
npm run check:contract
npm run check:e2e
```

### MP-08 Consulta ambulatoria minima

Objetivo: consolidar atencion ambulatoria como encuentro + SOAP, no como
agenda ni modulo paralelo.

Tablas:

- `clinical_encounters`
- `clinical_entries`

Pantallas autorizadas:

- `/consulta`
- `/consulta/pacientes/[patientId]/atencion`
- `/consulta/pacientes/[patientId]/resumen`

Trabajo permitido:

- Mejorar flujo de creacion de encuentro ambulatorio y SOAP vinculado.
- Mostrar resumen como lectura de ficha.

Trabajo prohibido:

- Agenda productiva.
- Caja de cobro.
- Scheduling real.

Gates:

```bash
npm run check:api
npm run check:web
npm run check:contract
```

### MP-09 IA de lectura y contexto

Objetivo: avanzar solo en lectura longitudinal explicable, sin escritura
automatica.

Tablas:

- ninguna nueva por defecto
- usa `clinical_entries`, `clinical_events`, listas activas y auditoria como fuentes

Pantallas autorizadas:

- `/pacientes/[patientId]/ai-chart`
- `/pacientes/[patientId]/ia`
- `/pacientes/[patientId]/ficha`
- `/pacientes/[patientId]/contexto` solo si queda habilitada por gobierno, backend, OpenAPI y tests

Trabajo permitido:

- Fuentes visibles.
- Faltantes visibles.
- Razonamiento deterministico local explicable.
- Acciones de escritura solo via `ClinicalPatch` y confirmacion humana.

Trabajo prohibido:

- Chat libre generico.
- RAG documental.
- IA externa identificada.
- Diagnostico autonomo.
- Escritura directa desde endpoint assistant.

Gates:

```bash
npm run check:api
npm run check:web
npm run check:contract
npm run check:e2e
```

### MP-10 Laboratorio y riesgo clinico

Objetivo: no expandir laboratorio ni riesgo hasta cerrar tabla duena o regla de
proyeccion.

Estado actual:

- `LabResult` no tiene tabla duena dedicada.
- `ClinicalRisk` no tiene tabla duena dedicada.
- Pueden aparecer como `ClinicalEntry`, `ClinicalEvent` o resumen derivado.

Decision requerida antes de implementar:

- Si son documentos/eventos: usar `clinical_entries` o `clinical_events`.
- Si son datos estructurados editables: proponer modelo, migracion, API,
  permisos, auditoria, OpenAPI, pantalla y papel en un microproceso propio.

Trabajo prohibido:

- Crear pantalla productiva de laboratorio sin tabla duena.
- Crear score de riesgo editable sin fuente.
- Agregar librerias de calculo clinico sin ADR o justificacion en gobierno.

Gates minimos antes de autorizar:

```bash
npm run audit:traceability
npm run check:api
npm run check:web
```

### MP-11 Dependencias y librerias

Objetivo: mantener compatibilidad sin inflar stack.

Estado actual:

- La expansion serial MP-00 a MP-10 no agrego dependencias npm ni Python.
- El unico cambio en `package.json` fue el script `audit:traceability`.
- `package-lock.json`, `apps/web/package.json` y `apps/api/pyproject.toml` no deben cambiar si el microproceso no justifica una dependencia.

Regla:

- Por defecto, no agregar dependencias.
- Si una dependencia es inevitable, debe tener PR propio o seccion explicita en
  el PR del dominio.

Checklist obligatorio:

```text
problema concreto
alternativas sin dependencia
superficie de seguridad
costo de mantenimiento
impacto en Windows/Linux/CI
gate que la valida
```

Dependencias prohibidas por defecto:

- frameworks IA/orquestadores
- librerias RAG
- paquetes de dashboard
- paquetes de firma/receta sin politica legal
- terminologias clinicas copiadas completas al repo

### Orden serial recomendado

```text
MP-00 trazabilidad base
MP-01 identidad/contacto paciente
MP-02 encuentro como episodio
MP-03 evolucion SOAP formal
MP-04 eventos longitudinales
MP-05 listas clinicas activas
MP-06 papel formal
MP-07 hospitalizacion gobernada
MP-08 consulta ambulatoria minima
MP-09 IA lectura/contexto
MP-10 laboratorio/riesgo solo con decision de tabla duena
MP-11 dependencias solo cuando un MP las justifique
```

Ningun microproceso posterior puede compensar una brecha abierta en uno
anterior. Si un gate falla, el siguiente paso es reparar el gate, no abrir otra
pantalla.

### Cierre de ciclo 1

Estado esperado despues de ejecutar MP-00 a MP-11:

- trazabilidad de variables y dominios generada
- ficha muestra vinculo con episodios y encuentros
- SOAP muestra estado documental y papel formal
- eventos muestran fuente y referencia
- listas clinicas muestran estado, ID y fecha/fuente
- papel de ficha/resumen/evolucion/receta bloqueada muestra estado y limites
- hospitalizacion distingue borrador/cerrado sin firma legal
- consulta ambulatoria declara encuentro + SOAP vinculados
- AI-Chart declara fuentes, limites y escritura por `ClinicalPatch`
- laboratorio y riesgo quedan bloqueados por falta de tabla duena
- no hay dependencias nuevas

Gates de cierre:

```bash
npm run audit:variables
npm run audit:traceability
npm run check:web
npm run check:api
```

Si se quiere publicar el ciclo, correr tambien:

```bash
npm run check:contract
npm run check:e2e
```

### Ciclo 2: endurecimiento antes de crecer

El siguiente ciclo no agrega dominios nuevos. Solo endurece invariantes que el
ciclo 1 dejo visibles.

#### C2-00 Congelar evidencia

Objetivo: cerrar el diff actual antes de abrir otra superficie.

Trabajo permitido:

- revisar `reports/variable-map.*`
- revisar `reports/traceability-map.*`
- correr gates de cierre
- preparar commit unico o PR pequeno

Trabajo prohibido:

- nueva pantalla
- nuevo endpoint
- nueva dependencia

#### C2-01 Contrato paciente y privacidad

Objetivo: decidir tratamiento de `document_id_hash`, hoy tipado pero no visible.

Opciones permitidas:

- mantenerlo como campo backend tipado y no visible
- moverlo a read model restringido futuro
- ocultarlo del read model publico con cambio de API y OpenAPI

Trabajo prohibido:

- mostrar identificadores reales
- buscar pacientes por documento real
- agregar datos sensibles de ejemplo

#### C2-02 Invariante de fuente en eventos

Objetivo: pasar de advertencia UI a regla backend para eventos derivados.

Regla candidata:

```text
si source_type != manual entonces source_ref debe existir
```

Trabajo requerido si se implementa:

- validacion FastAPI/Pydantic o ruta
- test API
- OpenAPI actualizado si cambia contrato
- UI conserva advertencia previa

#### C2-03 Encuentro activo en snapshot

Objetivo: evitar que la ficha infiera episodio activo solo desde evoluciones.

Opcion minima:

- agregar al snapshot un read model de encuentros recientes o activo

Trabajo requerido:

- schema backend
- repositorio/query
- endpoint `GET /patients/{patient_id}/record`
- tipo TS
- UI ficha
- OpenAPI y test API

No hacerlo si basta con la pantalla `/encuentros`.

#### C2-04 Papel y complejidad

Objetivo: evitar que `clinical-print.tsx` siga creciendo.

Trabajo permitido:

- extraer subcomponentes internos de papel si el archivo supera presupuesto
- mantener rutas print actuales
- no cambiar contenido clinico

Trabajo prohibido:

- crear nuevo sistema de documentos
- firma real
- receta valida

#### C2-05 E2E smoke de trazabilidad

Objetivo: cubrir navegacion minima de ficha expandida.

Escenarios:

- ficha muestra episodio clinico
- evolucion muestra boton papel
- eventos muestran fuente
- signos vitales muestran control registrado
- receta sigue bloqueada

Gates:

```bash
npm run check:e2e
npm run check:web
```

#### C2-06 Publicacion limpia

Objetivo: preparar salida a rama/PR sin mezclar siguiente feature.

Checklist:

- diff sin dependencias nuevas
- reportes regenerados
- gates declarados
- resumen de riesgos: `document_id_hash`, `LabResult`, `ClinicalRisk`
- siguiente PR empieza despues de merge o commit limpio

## AI-Chart despues de R-01

AI-Chart esta separado en `apps/web/src/components/clinical/ai-chart/`.
Reglas para nuevos cambios:

- mantener `patient-ai-chart-pages.tsx` como orquestador
- no agregar bloques UI inline grandes en la pagina
- preferir componentes existentes antes de crear rutas nuevas
- no sumar reglas clinicas al frontend; si una regla interpreta datos, vive en API
- todo nuevo output debe tener fuente, faltante/limite, accion humana y auditoria
- no tocar Ollama/API externa hasta cerrar Fase 1 del plan progresivo
- crecimiento IA conversacional entra primero por el `AI Bridge` compartido; no crear Route Handlers paralelos sin necesidad
- propuestas de escritura deben converger a `ClinicalPatch` revisable antes de persistir

Foco actual:

- Fase 1 queda cerrada; el siguiente avance debe ser Fase 2 Context Builder explicable
- mantener `ClinicalPatch` simple: `clinical_event` y `evolution`
- tratar estados de propuesta como flujo local + auditoria hasta decidir persistencia propia
- no crear editor generico de patches
- no extraer `packages/ai-core` hasta que haya duplicacion real
- no ampliar a RAG, documentos ni IA externa antes de cerrar Fase 1
