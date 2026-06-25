# Permisos y Acceso de Lectura

Reporte reproducible para comparar permisos backend, permisos frontend y matriz de pantallas.

Ejecutar:

```bash
npm run audit:permissions-read-access
```

Uso esperado:

- revisar roles antes de cambiar rutas de ficha, papel o IA;
- reportar gaps como warnings mientras no exista una politica de bloqueo mas fina;
- mantener `admin`, `medico`, `enfermeria`, `solo_lectura` y `dev` alineados entre FastAPI, frontend y `SCREEN_TREE`.

Estado inicial 2026-06-25: reporte informativo, sin bloqueo CI.

