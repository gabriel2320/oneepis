# Gobierno Técnico

Este repo debe ser fácil de desarrollar, mantener y corregir por agentes IA.

## Reglas de Crecimiento

- Agrega dependencias solo con motivo claro.
- Mantén los módulos enfocados en una responsabilidad clínica o técnica.
- Evita abstracciones genéricas hasta que haya dos usos reales.
- Actualiza OpenAPI cuando cambie la API.
- No aceptes fixtures con datos sensibles o realistas.

## Nuevas Dependencias

Antes de sumar una dependencia, registra:

- problema que resuelve
- alternativas consideradas
- costo de mantenimiento
- superficie de seguridad

Para cambios grandes, crea un ADR en `docs/adr`.

## Revisiones

Todo PR debe responder:

- Que cambia para el usuario clínico.
- Que cambia en el contrato API.
- Que migraciones o datos toca.
- Que riesgo de privacidad introduce.
- Que prueba cubre el comportamiento.

## Presupuesto de Complejidad

- Un archivo de aplicación no debería superar 300 lineas sin una razón clara.
- Un componente UI debe preferir composición antes que props infinitas.
- Un servicio backend debe expresar reglas de dominio, no consultas mezcladas con controladores grandes.
