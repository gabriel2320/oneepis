# Progressive Development Plan

## Decision

OneEpis avanza por fases progresivas. Cada fase debe dejar una ficha usable, auditable y menos dependiente de IA generativa.

Cada fase debe cumplir `docs/VISUAL_INTELLIGENCE_COUPLING.md`: toda inteligencia nueva requiere correlato visual inmediato, accion humana clara y auditoria.

La secuencia obligatoria es:

```text
Fase 0: Simulated Clinical Intelligence
Fase 1: AI-Chart Core estable
Fase 2: Context Builder serio
Fase 3: Chat dirigido y preferencias
Fase 4: Medicamentos, examenes y pendientes
Fase 5: Documentos y propuestas estructuradas
Fase 6: Alta y epicrisis
Fase 7: Ollama local como mejora
Fase 8: Gateway externo opcional
```

No se avanza a una fase si la anterior no conserva:

- fuentes visibles
- datos faltantes
- certeza o limite declarado
- confirmacion humana para escribir ficha
- auditoria
- degradacion sin Ollama
- correlato visual editable o confirmable

## Fase 0: Simulated Clinical Intelligence

Objetivo: que la ficha se comporte como IA clinica sin depender de LLM.

Componentes:

- `ClinicalIntentRouter`
- reglas locales
- plantillas
- timeline
- eventos clinicos
- validadores de faltantes
- auditoria

Implementado hasta ahora:

- eventos clinicos, timeline y borrador SOAP desde eventos
- `ClinicalIntent` con fuentes, faltantes, certeza, evidencia y acciones
- router deterministico con barra dirigida y fallback seguro
- reglas 24 h para signos vitales, examenes, medicacion y eventos no asociados
- `review_items` aceptables/rechazables con auditoria e historial visual
- hallazgos agrupados por dominio, estado y fuente
- hoja SOAP editable con margen inteligente persistente
- trazabilidad S/O/A/P por seccion del borrador SOAP
- acciones propuestas con `action_id`, descripcion y etiqueta de confirmacion
- decisiones de acciones propuestas auditadas sin aplicar cambios automaticos
- acciones propuestas conectadas a flujos estructurados existentes
- prellenado de evento/pendiente desde accion auditada sin guardado automatico
- barra clinica dirigida que ejecuta la intencion reconocida
- prellenado de problema activo desde accion propuesta sin guardado automatico
- fallback de barra clinica resuelto por `action_id`, no por texto visible
- intencion `draft_soap` genera hoja SOAP editable desde fuentes de eventos sin guardar
- panel compacto de cambios 24 h visible antes del margen detallado
- reglas de examenes aceptan payload estructurado `results[]` sin leer texto libre
- guardado de SOAP generado exige marca visual de revision humana

Siguiente incremento:

- ampliar prellenado solo cuando exista acto clinico completo y formulario real

## Fase 1: AI-Chart Core estable

Objetivo: consolidar paciente -> eventos -> contexto -> borrador -> confirmacion -> auditoria.

Ya implementado:

- `clinical_events`
- timeline
- borrador SOAP desde eventos
- guardado humano como borrador
- `ClinicalIntent`
- fuentes, certeza, faltantes, acciones
- marcas de evidencia
- contexto por problema
- baseline de evolucion previa

Pendiente:

- pulir UI de revision antes de guardar
- permitir crear eventos desde una evolucion ya escrita
- reforzar permisos y estados clinicos por modo

## Fase 2: Context Builder serio

Objetivo: pasar de listas utiles a contexto clinico explicable.

Trabajo:

- asociacion semantica local por problema
- reglas explicitas para mejoria/empeoramiento
- faltantes por tipo de atencion
- comparacion 24 h con datos estructurados
- evidencia vinculada a fuente

Regla: toda inferencia debe mostrar por que se hizo.

## Fase 3: Chat dirigido y preferencias

Objetivo: hacer la ficha conversable sin abrir chat libre inseguro.

Trabajo:

- router de intenciones ampliado
- decisiones auditadas por accion propuesta
- preferencias de estilo confirmadas
- plantillas editables
- memoria de correcciones/rechazos

Regla: una preferencia aprendida no se aplica como verdad sin confirmacion.

## Fase 4: Medicamentos, examenes y pendientes

Objetivo: ampliar la inteligencia simulada a dominios clinicos frecuentes.

Trabajo:

- revisar cambios de medicamentos
- detectar medicamentos sin dosis o frecuencia
- detectar tratamientos sin problema asociado
- resumir tendencias de examenes
- crear pendientes clinicos auditables

Regla: el sistema advierte y ordena; no prescribe autonomamente.

## Fase 5: Documentos y propuestas estructuradas

Objetivo: convertir texto/documentos en propuestas revisables.

Trabajo:

- importar documento como fuente
- extraer antecedentes como propuesta
- crear eventos desde texto libre
- aceptar/rechazar items individualmente

Regla: un documento importado no modifica la ficha hasta confirmacion humana.

## Fase 6: Alta y epicrisis

Objetivo: cerrar casos con documentos utiles y seguros.

Trabajo:

- checklist de alta
- epicrisis preliminar
- diagnosticos de egreso
- indicaciones y controles
- pendientes antes de alta

Regla: todo documento de egreso parte como borrador no firmado.

## Fase 7: Ollama local como mejora

Objetivo: mejorar lenguaje, extraccion y resumen sin cambiar la autoridad clinica.

Trabajo:

- redaccion natural
- extraccion desde texto libre
- RAG local con fuentes
- resumen documental

Regla: Ollama enriquece; no reemplaza reglas, fuentes ni confirmacion.

## Fase 8: Gateway externo opcional

Objetivo: permitir IA externa solo bajo privacidad, autorizacion y auditoria.

Trabajo:

- anonimizado
- vista previa del payload
- autorizacion explicita
- proveedor configurable
- auditoria de envio y respuesta

Regla: nunca enviar ficha completa identificada por defecto.
