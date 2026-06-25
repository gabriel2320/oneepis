# Progressive Development Plan

Este documento conserva solo la secuencia progresiva de AI-Chart. No es
historial, roadmap ni estado operativo general.

- Estado operativo actual: `docs/CURRENT_STATE.md`
- Historial cronologico: `docs/ROADMAP.md`
- Reglas anti-inflacion: `docs/GOVERNANCE.md`
- Contrato AI-Chart: `docs/AI_CHART_CORE.md`
- Regla inteligencia -> UI: `docs/VISUAL_INTELLIGENCE_COUPLING.md`

## Decision

OneEpis avanza por fases progresivas. Cada fase debe dejar una ficha usable,
auditable y menos dependiente de IA generativa.

Toda inteligencia nueva requiere:

- fuentes visibles
- datos faltantes
- certeza o limite declarado
- confirmacion humana para escribir ficha
- auditoria
- degradacion sin Ollama
- correlato visual editable o confirmable

## Algoritmo

Cada ciclo debe complejizar solo una dimension:

```text
leer estado -> elegir fase activa -> escoger una brecha -> reducir alcance
-> implementar en superficie existente -> validar -> documentar estado real
```

Selector de brecha:

1. Tomar el primer item de trabajo de la fase activa que pueda resolverse sin nueva superficie.
2. Si requiere API nueva, verificar antes que no quepa en una ruta existente.
3. Si requiere UI nueva, verificar antes que no quepa en un panel existente.
4. Si requiere modelo nuevo, verificar antes que no pueda expresarse como evento, patch, evidencia, pendiente o fuente.
5. Si requiere dependencia nueva, detenerse y justificarla antes de implementar.

Reglas de alcance por ciclo:

- maximo una conducta clinica nueva
- maximo una superficie UI tocada
- maximo una familia de tests tocada
- cero rutas placeholder
- cero documentos nuevos salvo decision arquitectonica imposible de absorber
- cero escritura clinica sin `ClinicalPatch` o endpoint canonico con auditoria

Orden de preferencia:

1. Mejorar explicacion de inferencias existentes.
2. Vincular inferencias con fuentes visibles.
3. Reducir falsos positivos o ambiguedad clinica.
4. Agregar faltantes contextuales por dominio.
5. Ampliar reglas deterministicas con datos ya modelados.
6. Solo despues agregar nuevo contrato API.

## Secuencia

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

## Fase 0: Simulated Clinical Intelligence

Objetivo: que la ficha se comporte como inteligencia clinica util sin depender
de LLM.

Componentes:

- `ClinicalIntentRouter`
- reglas locales
- plantillas
- timeline
- eventos clinicos
- validadores de faltantes
- auditoria

Estado: implementado como base Nivel 0. La ficha ya puede explicar fuentes,
faltantes, reglas 24 h, borrador SOAP, `review_items`, AI Bridge inicial y
`ClinicalPatch` sin depender de Ollama.

## Fase 1: AI-Chart Core Estable

Objetivo: consolidar `paciente -> eventos -> contexto -> borrador ->
confirmacion -> auditoria`.

Estado: cerrado como minimo producto verificable.

Implementado:

- `clinical_events`
- timeline
- borrador SOAP desde eventos
- guardado humano como borrador
- `ClinicalIntent`
- fuentes, certeza, faltantes y acciones
- marcas de evidencia
- contexto por problema
- baseline de evolucion previa
- `ClinicalPatch` v0 para `clinical_event` y `evolution`

Mantenimiento permitido:

- mantener `patient-ai-chart-pages.tsx` como orquestador
- sostener estados visuales, permisos y fuentes al sumar inferencias
- no crear chat libre, RAG ni nueva superficie IA

## Fase 2: Context Builder Serio

Objetivo: pasar de listas utiles a contexto clinico explicable.

Estado: iniciada con explicaciones deterministicas por problema.

Implementado inicial:

- `problem_contexts` con explicaciones visibles de asociacion
- eventos recientes sin problema asociado agrupados para revision humana
- `missing_data` contextual por atencion ambulatoria, hospitalizada o desconocida
- curso clinico narrativo por dominios iniciales
- asociaciones por vocabulario local y negaciones obvias
- prioridad SNOMED CT cuando existe codigo/payload externo licenciado
- pendientes por problema activo segun dominio probable
- resultados `lab_results` como evidencia explicable por dominio

Trabajo permitido:

- ampliar vocabulario local por dominio
- conectar repositorio SNOMED CT externo/licenciado sin versionar releases en el repo
- ampliar reglas explicitas de mejoria/empeoramiento
- ampliar faltantes por dominio con fuentes estructuradas existentes
- ampliar comparacion 24 h con datos ya modelados

Regla: toda inferencia debe mostrar por que se hizo.

## Fase 3: Chat Dirigido y Preferencias

Objetivo: hacer la ficha conversable sin abrir chat libre inseguro.

Trabajo futuro:

- router de intenciones ampliado
- decisiones auditadas por accion propuesta
- preferencias de estilo confirmadas
- plantillas editables
- memoria de correcciones/rechazos

Regla: una preferencia aprendida no se aplica como verdad sin confirmacion.

## Fase 4: Medicamentos, Examenes y Pendientes

Objetivo: ampliar inteligencia simulada a dominios clinicos frecuentes.

Trabajo futuro:

- revisar cambios de medicamentos
- detectar medicamentos sin dosis o frecuencia
- detectar tratamientos sin problema asociado
- resumir tendencias de examenes
- crear pendientes clinicos auditables

Regla: el sistema advierte y ordena; no prescribe autonomamente.

## Fase 5: Documentos y Propuestas Estructuradas

Objetivo: convertir texto/documentos en propuestas revisables.

Trabajo futuro:

- importar documento como fuente
- extraer antecedentes como propuesta
- crear eventos desde texto libre
- aceptar/rechazar items individualmente

Regla: un documento importado no modifica la ficha hasta confirmacion humana.

## Fase 6: Alta y Epicrisis

Objetivo: cerrar casos con documentos utiles y seguros.

Trabajo futuro:

- checklist de alta
- epicrisis preliminar
- diagnosticos de egreso
- indicaciones y controles
- pendientes antes de alta

Regla: todo documento de egreso parte como borrador no firmado.

## Fase 7: Ollama Local Como Mejora

Objetivo: mejorar lenguaje, extraccion y resumen sin cambiar la autoridad clinica.

Trabajo futuro:

- redaccion natural
- extraccion desde texto libre
- RAG local con fuentes
- resumen documental

Regla: Ollama enriquece; no reemplaza reglas, fuentes ni confirmacion.

## Fase 8: Gateway Externo Opcional

Objetivo: permitir IA externa solo bajo privacidad, autorizacion y auditoria.

Trabajo futuro:

- anonimizado
- vista previa del payload
- autorizacion explicita
- proveedor configurable
- auditoria de envio y respuesta

Regla: nunca enviar ficha completa identificada por defecto.
