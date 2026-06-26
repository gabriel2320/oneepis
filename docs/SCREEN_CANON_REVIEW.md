# Screen Canon Review

OneEpis crece desde el arbol clinico, no desde pantallas sueltas. Cada cambio de
UI debe conservar esta secuencia:

```text
login -> mapa fisico -> lugar de trabajo -> paciente longitudinal -> episodio -> acto clinico -> documento -> seguimiento
```

Regla de producto:

```text
Patient une. Encounter separa. Timeline reconcilia. Auditoria prueba. Contexto canonico explica.
```

## Algoritmo de revision

Para cada ruta visible, seguir este orden antes de agregar comportamiento:

1. Clasificar la pantalla.
   - Acceso/login.
   - Mapa fisico o lugar de trabajo.
   - Ficha longitudinal tradicional.
   - Mundo ambulatorio.
   - Mundo hospitalizado.
   - Documento/papel.
   - IA contextual.
   - Configuracion/administracion.

2. Validar el canon.
   - La pantalla responde una sola pregunta de trabajo.
   - La Home muestra lugares fisicos, no acciones.
   - Ambulatorio y hospitalizacion no duplican pacientes.
   - La ficha longitudinal no se transforma en dashboard.
   - Los modulos futuros o bloqueados no navegan ni simulan produccion.

3. Validar fuente de verdad.
   - Lecturas: API, snapshot, Assistant Read o contexto canonico.
   - Escrituras: backend, permisos, auditoria, OpenAPI y tests.
   - IA: fuente, limites, faltantes y accion humana visibles.
   - Papel: documento fuente especifico; sin fallback silencioso.

4. Limpiar interfaz.
   - Remover texto tecnico, accesos residuales, placeholders y datos demo fuera de lugar.
   - Usar el shell canonico del dominio.
   - Mantener lenguaje clinico humano y estados visibles.
   - Evitar cards anidadas, dashboards decorativos y acciones rapidas fuera de contexto.

5. Limpiar codigo.
   - No crear una capa nueva si basta un helper, config o componente existente.
   - Extraer por responsabilidad antes de superar el limite de tamano.
   - Reusar `screen-capabilities`, permisos y contratos tipados.
   - No duplicar listas de rutas ni reglas de permiso.

6. Cerrar con tests.
   - Render minimo de la ruta.
   - Permisos si navega o escribe.
   - Auditoria si escribe.
   - Bloqueo si esta futura/bloqueada.
   - E2E solo para flujos principales.

## Orden canonico

1. Login y cuenta.
   - `/login`, recuperar y desbloquear.
   - No mostrar perfiles, roles, pacientes ni modulos.

2. Mapa fisico.
   - `/home` y alias `/mapa`.
   - Tarjetas de lugares reales: ambulatorio, hospitalizacion, farmacia,
     laboratorio, imagenologia, enfermeria, administracion.

3. Ambulatorio.
   - `/consulta`, agenda, atencion y resumen.
   - Fuente operacional: cita + `ClinicalEncounter(type=ambulatory)`.

4. Hospitalizacion.
   - `/hospitalizacion`, camas, rondas, ingreso, hoja diaria, indicaciones y
     epicrisis.
   - Fuente operacional: `ClinicalEncounter(type=hospitalization)`.

5. Ficha tradicional longitudinal.
   - `/pacientes/[patientId]/ficha` como hoja clinica viva.
   - Debe reunir antecedentes, problemas, alergias, medicacion, riesgos,
     documentos, timeline y contexto.

6. Documentos y papel.
   - Print routes con fuente especifica, estado documental y footer si no hay
     firma real.

7. IA simulada y LLM real.
   - Nivel 0 obligatorio: reglas locales, fuentes, faltantes y trazabilidad.
   - Nivel 1 opcional: Ollama/LLM mejora lenguaje; no reemplaza reglas ni
     confirmacion humana.

## Definition of Done por pantalla

Una pantalla esta lista para promocion si cumple todo lo siguiente:

- Existe en `docs/SCREEN_TREE.md`.
- Existe en `apps/web/src/lib/screen-capabilities.ts`.
- Tiene una fuente de verdad clara.
- No mezcla dominios de trabajo.
- No muestra datos clinicos fuera de contexto.
- No crea nuevas rutas tecnicas visibles sin registrar.
- Si escribe, audita y respeta permisos backend.
- Si usa IA, expone fuentes, limites y accion humana.
- Si imprime, usa una fuente especifica y no inventa documentos.
- Pasa `npm run review:screens` junto con los checks del PR.

## Anti-patrones bloqueantes

- Crear una tarjeta principal por accion clinica.
- Crear una pantalla futura con UI productiva falsa.
- Usar `current_care_context` como verdad unica si hay encounters activos.
- Escribir ficha desde IA sin `ClinicalPatch` o endpoint canonico auditado.
- Duplicar paciente por mundo ambulatorio/hospitalizado.
- Agregar dashboard, metricas o timeline reciente en el mapa fisico.
- Agregar componentes grandes inline en paginas cuando existe shell o workspace.

