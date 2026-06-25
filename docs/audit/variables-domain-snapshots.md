# Variables, Dominios y Snapshots

Reporte reproducible para revisar deriva entre schemas API, contratos TS y `SCREEN_TREE`.

Ejecutar:

```bash
npm run audit:variables-domain-snapshots
```

Uso esperado:

- inspeccionar cambios grandes antes de abrir un PR de dominio nuevo;
- detectar crecimiento de rutas o estados sin inflar CI;
- copiar hallazgos relevantes a `CURRENT_STATE`, `GOVERNANCE` o issues, no crear documentos paralelos.

Estado inicial 2026-06-25: reporte informativo, sin bloqueo CI.

