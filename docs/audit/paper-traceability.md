# Papel y Trazabilidad

Check bloqueante incremental para evitar regresiones en documentos imprimibles.

Ejecutar:

```bash
npm run check:paper-traceability
```

Reglas iniciales:

- no mostrar `Firmada demo`;
- no mostrar `Folio demo`;
- no exponer `entry.status` crudo en papel;
- no presentar `signed` como firma legal.

El baseline solo debe crecer si se acepta deuda explicita y acotada. Un nuevo documento clinico debe mostrar estado humano, fuente/actor/fecha disponible y limites de uso.

