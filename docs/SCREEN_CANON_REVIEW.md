# Screen Canon Review

OneEpis crece desde el arbol clinico, no desde pantallas sueltas. Cada cambio de
UI debe conservar esta secuencia:

```text
login -> mapa fisico -> lugar de trabajo -> paciente longitudinal -> episodio -> acto clinico -> documento -> seguimiento
```

Regla de producto:

```text
Paciente une. Lugar orienta. Encounter separa. Timeline reconcilia.
Auditoria prueba. IA resume, no decide.
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

## PR-000 Auditoria HIS Inicial

Esta seccion archiva el prompt maestro como protocolo operativo compacto para
agentes IA. No crea pantallas nuevas ni autoriza rutas. El objetivo de PR-000
es auditar el estado real antes de continuar ciclos de construccion.

### Protocolo de ciclo PR

Cada ciclo de PR debe seguir este orden:

1. Auditar repo, rutas, registry, contratos API, permisos, auditoria, estados y
   uso de datos demo.
2. Planificar un subarbol pequeno: maximo un dominio y una accion principal.
3. Implementar rutas, navegacion, datos, permisos, estados y metadata solo si
   existe fuente de verdad o bloqueo explicito.
4. Validar con gates proporcionales; no declarar gate como pasado si no corrio.
5. Documentar `PR_PLAN`, `PR_SUMMARY`, riesgos, deuda y proximo PR.
6. Revisar como auditor clinico: rechazar pantallas huerfanas, datos falsos,
   dashboards decorativos, acciones legales falsas, falta de permisos o falta
   de auditoria.
7. Cerrar dejando el arbol mas conectado que antes.

Plantilla obligatoria antes de codificar:

```text
PR_PLAN:
- branch:
- domain:
- goal:
- screens:
- routes:
- components:
- api/hooks:
- permissions:
- audit:
- tests:
- outOfScope:
```

Plantilla obligatoria al cerrar:

```text
PR_SUMMARY:
- files changed:
- routes connected:
- states added:
- permissions handled:
- gates run:
- failures:
- risks:
- next PR:
```

### AUDIT_REPORT

- stack detected: Next.js App Router + React/TypeScript + Tailwind/shadcn UI;
  FastAPI + SQLAlchemy/Alembic + PostgreSQL; OpenAPI export; Ollama/local rules
  como IA opcional y secundaria.
- route system: App Router bajo `apps/web/src/app`; 57 `page.tsx` visibles.
- registry: 57 rutas registradas en
  `apps/web/src/lib/screen-capabilities.registry.json`; tabla real generada en
  `docs/SCREEN_TREE.md`.
- existing domains: Acceso/configuracion, Nucleo paciente, Episodios,
  Ambulatorio, Hospitalizacion, Medicacion/vademecum, Ordenes/resultados,
  Documentos/papel, Seguridad/auditoria e IA clinica.
- missing domains: ADT productivo, Urgencias, UCI, Enfermeria dedicada,
  CPOE ejecutable, Farmacia ejecutiva, LIS amplio, RIS/PACS, Pabellon,
  Anestesia, Procedimientos, Maternidad/neonatologia, Banco de sangre,
  Rehabilitacion, Nutricion, Calidad global, Agenda/recursos amplia, Censo
  global, Facturacion, Inventario, Equipamiento, Personal/turnos,
  Administracion institucional, Integraciones y Portal paciente.
- existing screens: login/recuperacion/desbloqueo, `/inicio`, `/home`, mapa
  legacy, configuracion, pacientes, ficha, alergias, problemas, medicacion,
  signos, eventos, encuentros, evoluciones, documentos, auditoria paciente,
  ambulatorio, agenda, resumen/atencion, hospitalizacion, camas, rondas,
  ingreso, hoja diaria, indicaciones, epicrisis, AI-Chart/IA y print routes.
- orphan screens: NOT_FOUND por guard actual; `check:screens` valida que toda
  ruta visible tenga registry y tabla generada.
- duplicated components: UNKNOWN; existen shells y workspaces por dominio, pero
  no se ejecuto auditoria de duplicacion semantica componente por componente.
- existing clinical components: `PatientClinicalShell`,
  `DomainClinicalShell`, `AmbulatoryClinicalShell`, `HospitalClinicalShell`,
  `ClinicalWorkspaceLayout`, `ClinicalSectionCard`, estados clinicos,
  widgets de auditoria, papel e indicadores de capacidad.
- missing foundation components: `HospitalShell`, `HospitalTopbar`,
  `EpisodeContextBar`, `ClinicalBreadcrumb` global y `AuditMetadataFooter`
  como abstracciones transversales explicitas. Existen equivalentes parciales
  en `AppShell`, shells de paciente/dominio y layouts de papel.
- API readiness: pacientes, auth, encuentros, entradas, eventos, alergias,
  problemas, medicacion, signos, citas, camas, hojas diarias, indicaciones,
  riesgos, laboratorio minimo, auditoria e IA contextual tienen endpoints o
  servicios. ADT, urgencias, UCI, CPOE ejecutable, farmacia ejecutiva, MAR,
  LIS/RIS amplio, pabellon, facturacion e integraciones quedan NOT_FOUND como
  producto.
- permission readiness: RBAC minimo existe en backend y frontend; ABAC por
  institucion/sede/equipo queda futuro.
- audit readiness: escritura clinica y varias acciones IA registran eventos;
  auditoria de accesos existe de forma minima y debe endurecerse separando
  lecturas sensibles de escrituras clinicas.
- demo data risks: fixtures demo existen bajo `DEMO_MODE`; riesgo vivo es evitar
  fallback invisible a primer paciente, primer documento u orden. Los PRs deben
  mantener demo visible y bloqueado para escrituras reales.
- visual canon risks: riesgo de convertir `/inicio`, ficha o home en dashboard;
  riesgo de abrir dominios futuros con UI productiva falsa; riesgo de reponer
  copy de arquitectura visible.
- blockers: firma, receta valida, orden ejecutable, MAR, consentimientos,
  adjuntos productivos, auth productiva, ABAC contextual, backups, cifrado,
  logs PHI-safe e interoperabilidad real.
- safe next step: reforzar flujos existentes antes de abrir nuevos dominios:
  pacientes/MPI minimo, contexto paciente, estados transversales, auditoria de
  accesos y flujo ambulatorio/hospitalizacion ya existentes.

### Primeros 10 PRs recomendados

1. PR-000: auditoria HIS inicial y protocolo compacto para agentes; sin UI.
2. PR-001: endurecer `/inicio` como bandeja por rol con acciones existentes,
   sin datos clinicos ni roles tecnicos visibles. En esta rama ya existe una
   primera version y solo deberia recibir hardening, no nuevos dominios.
3. PR-002: mejorar `/pacientes` como indice maestro minimo: busqueda, empty,
   error, permisos y seleccion de ficha. Es el siguiente PR funcional
   recomendado antes de abrir urgencia, UCI, farmacia, MAR o portal.
4. PR-003: abrir contexto paciente mas explicito: identidad, alertas y
   episodios existentes, sin fusion ni duplicados productivos.
5. PR-004: reforzar ficha longitudinal: continuidad accionable, metadata,
   fuentes y no-dashboard.
6. PR-005: consolidar estados transversales reutilizables en pantallas
   clinicas existentes.
7. PR-006: endurecer auditoria de accesos y separar lectura sensible de
   escritura clinica.
8. PR-007: ambulatorio: agenda -> resumen -> atencion -> cierre no firmado,
   sin receta ni orden ejecutable.
9. PR-008: hospitalizacion: censo/cama -> ronda -> documentos borrador, sin
   firma, alta legal ni MAR.
10. PR-009: documentos/papel: print por ID estricto, sin fallback, metadata y
    estado documental visible.

## Secuencia de PR vigente

1. Reconciliar documentos canonicos con el estado real.
   - Marcar como cerrados `workflow_kind`, helpers ambulatorios/hospitalarios,
     labels humanos, fixtures demo separados y helpers HTTP de auth.
   - No tocar conducta de producto.

2. Revisar login y mapa fisico.
   - `/login`, recuperacion, desbloqueo, `/home`, `/mapa`, `AppShell` y logo.
   - Criterio: sin roles/perfiles/credenciales demo antes de sesion; Home solo
     lugares fisicos.

3. Revisar mundo ambulatorio.
   - `/consulta`, `/consulta/agenda`, atencion y resumen.
   - Criterio: cita + encuentro ambulatorio como fuente operacional, sin
     mezclar acciones hospitalarias ni ficha longitudinal.

4. Revisar mundo hospitalizado.
   - `/hospitalizacion`, camas, rondas, ingreso, hoja diaria, indicaciones y
     epicrisis.
   - Criterio: borrador/no firmado visible donde corresponda; sin orden
     ejecutable, MAR, firma legal, UCI ni pabellon productivo.

5. Revisar ficha longitudinal tradicional.
   - `/pacientes/[patientId]/ficha` y subpantallas nucleares.
   - Criterio: ficha unica del paciente, no dashboard, con IA solo como lectura
     contextual con fuentes, limites y faltantes.

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
     documentos, timeline y contexto canonico de lectura.

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
