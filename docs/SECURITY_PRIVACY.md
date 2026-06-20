# Seguridad y Privacidad

OneEpis maneja información clínica sensible. Este scaffold no debe considerarse listo para producción sanitaria sin revisión legal, operacional y de seguridad.

## Reglas Iniciales

- No guardar identificadores nacionales en claro. Usar hashes o identificadores internos.
- No escribir datos clínicos en logs.
- No enviar datos clínicos a servicios externos de IA.
- Mantener IA local y auditable cuando se habilite Ollama.
- Registrar eventos relevantes en auditoría.
- Cifrado, control de acceso granular y retención documental quedan como hitos antes de producción.

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
