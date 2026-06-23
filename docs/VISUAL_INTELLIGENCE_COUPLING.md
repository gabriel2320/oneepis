# Visual Intelligence Coupling

## Decision

Toda mejora de inteligencia debe tener correlato visual inmediato:

```text
capacidad inteligente -> estado visible -> accion humana -> auditoria
```

Si una capacidad no puede verse, corregirse, confirmarse y auditarse en una
pantalla clinica existente, no entra al core.

## Formas visuales permitidas

Cada accion inteligente debe aparecer como al menos una de estas formas:

- texto editable en hoja
- chip de estado
- margen de fuente, faltante o certeza
- tarjeta de propuesta
- accion confirmable
- entrada de auditoria

## Zonas AI-Chart

Cada pantalla AI-Chart importante debe tender a:

1. identidad clinica del paciente
2. hoja, ficha o documento principal
3. margen inteligente: fuentes, faltantes, certeza, alertas
4. barra conversacional clinica
5. acciones humanas: editar, guardar, confirmar, firmar, auditar

La conversacion no reemplaza la ficha. La conversacion mueve la ficha.

## Mapa inteligencia -> interfaz

| Inteligencia | Interfaz obligatoria |
| --- | --- |
| resumen del paciente | bloque de resumen clinico vivo |
| cambios 24 h | panel "Que cambio desde ayer" |
| problemas activos | lista visual priorizada |
| datos faltantes | margen de faltantes |
| borrador SOAP | hoja carta editable |
| fuente usada | cita, enlace o fuente visible |
| baja certeza | badge de revision |
| propuesta estructurada | tarjeta revisable |
| decision medica | aceptar/rechazar/editar |
| IA apagada | estado de modo estructurado |
| IA externa | gateway visual de privacidad |
| confirmacion | guardado/firma/auditoria |

## Estado implementado

OneEpis ya muestra en AI-Chart:

- eventos clinicos como fuente
- contexto, fuentes, faltantes y certeza
- comparacion 24 h con `rule_findings`
- grupos visuales por signos vitales, examenes, medicacion y revision
- estado por hallazgo: `mejora`, `empeora`, `revisar`, `observado`
- fuente por hallazgo con fallback estructurado
- `review_items` aceptables/rechazables
- historial de decisiones con actor, fecha y evento de auditoria
- hoja SOAP editable con margen inteligente
- trazabilidad S/O/A/P por seccion del borrador
- acciones propuestas como tarjetas confirmables
- decision de acciones propuestas con auditoria y sin mutacion automatica
- enlace desde accion propuesta hacia flujo estructurado existente
- prellenado de eventos/pendientes desde accion propuesta revisable
- prellenado de problema activo desde accion propuesta revisable
- acciones directas del router abren formularios existentes con origen AI-Chart visible
- barra conversacional dirigida que mueve el AI-Chart al ejecutar intenciones
- intencion de evolucion abre hoja SOAP editable desde fuentes visibles
- panel compacto de cambios 24 h en el cuerpo principal de la respuesta
- guardado de hoja SOAP generado bloqueado hasta revision humana explicita
- metadata de revision humana persistida al guardar el borrador AI-Chart
- estado IA generativa activa/degradada/apagada
- AI-Chart dividido en componentes por responsabilidad para evitar inflado
- propuestas de eventos desde evolucion escrita como tarjetas revisables
- operaciones principales de `ClinicalPatch` antes de confirmar escritura
- estado de propuesta visible: `pendiente`, `registrando`, `registrada en ficha` o `rechazada`
- guardado de SOAP generado como `ClinicalPatch target=evolution`, siempre borrador no firmado
- bloqueos de AI-Chart con condicion o rol habilitante visible

## Pendiente visual inmediato

Fase 1 queda cubierta para el flujo AI-Chart minimo. El siguiente avance permitido
es Fase 2 Context Builder, siempre dentro de la pantalla existente:

- mantener visibles fuentes, limites y destino del patch
- cubrir estados de propuesta/patch en prueba E2E o componente
- explicar inferencias nuevas por problema, fuente y regla

No crear otra pantalla ni aplicar datos clinicos finales desde una respuesta IA.

## Regla post R-01

El acoplamiento inteligencia -> interfaz debe mantenerse dentro de componentes
AI-Chart separados. Si una nueva inteligencia necesita visualizacion:

1. primero decidir que acto clinico cierra;
2. luego elegir componente existente;
3. si no cabe, extraer subpanel dentro de `ai-chart/`;
4. nunca recrear un dashboard ni un panel IA paralelo.
