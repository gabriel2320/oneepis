# Screen Tree

## Decision

El prototipo visual queda aprobado como base. OneEpis no debe crecer por
pantallas sueltas: el arbol maestro se ordena por momentos clinicos y cada
superficie declara su estado real.

```text
paciente -> episodio -> acto clinico -> documento -> firma/estado -> seguimiento
```

Estados permitidos:

- `completa`: tiene flujo humano minimo y, si escribe, API/PostgreSQL/permisos/auditoria/OpenAPI/tests.
- `completa/en expansion gobernada`: funciona, pero tiene un subdominio acotado en crecimiento con guardrails activos.
- `preparada`: existe como borde visible, declara que esta pendiente y no simula produccion.
- `bloqueada`: existe o se nombra para evitar uso clinico hasta completar requisitos legales/clinicos.
- `futura`: pertenece al mapa maestro, pero no tiene ruta o contrato listo.

Las pantallas preparadas o bloqueadas no cuentan como feature final.

Avances `v0.5-patient-core` ya consolidados:

- PR #15 promovio `/consulta/agenda` a agenda minima persistida.
- PR #16 promovio `/consulta/pacientes/[patientId]/resumen` a lectura ambulatoria real.
- PR #17 promovio `/pacientes/[patientId]/documentos` a indice de papel existente.
- Adjuntos externos, consentimientos, receta valida, firma y agenda avanzada siguen futuras/bloqueadas aunque existan accesos de lectura o papel.

La matriz documental se refleja operativamente en el Screen Capability Registry
frontend. Cada ruta visible debe existir aqui y en `apps/web/src/lib/screen-capabilities.ts`.
El gate `npm run check:screens` valida ambos lados.

## Navegacion objetivo

La navegacion actual se mantiene. El destino funcional queda agrupado asi:

- Acceso/configuracion: ingreso, preferencias, estado API/IA y administracion futura.
- Nucleo paciente: ficha, antecedentes, problemas, alergias, medicamentos, signos vitales, eventos, linea de tiempo y auditoria.
- Episodios: encuentros ambulatorios u hospitalarios y vinculo de actos clinicos.
- Ambulatorio: agenda, admision/preconsulta, consulta, evolucion, receta, ordenes, interconsulta, cierre y seguimiento.
- Hospitalizacion: censo/camas, ingreso medico, hoja diaria, evoluciones, indicaciones, resultados, interconsultas, procedimientos, alta y epicrisis.
- Medicacion/vademecum: medicacion activa, vademecum local curado, favoritos, sugeridos, historial y validacion de dosis.
- Ordenes/resultados: laboratorio, imagenes, procedimientos, informes y tendencias.
- Documentos/papel: documentos clinicos, importacion futura, exportacion/impresion y hoja carta.
- Seguridad/auditoria: alertas, riesgos, eventos adversos, auditoria de cambios y auditoria de accesos.
- IA clinica: apoyo contextual dentro de ficha/AI-Chart; no define el centro del producto.

## Rutas reales y estado

| Ruta | Modulo | Momento clinico | Estado | Fuente de verdad | Escritura | Permisos | Auditoria | Papel | IA permitida | Pendiente para completar |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `/` | Acceso/configuracion | seguimiento | completa | redirect App Router | no | publico/control UI | no | no | no | redirigir a login o home segun sesion |
| `/login` | Acceso/configuracion | seguimiento | completa | auth local | no | publico/control UI | no | no | no | correo productivo y usuarios persistentes futuros |
| `/login/recuperar` | Acceso/configuracion | seguimiento | completa | auth local | no | publico/control UI | security event + rate-limit | no | no | adaptador correo futuro |
| `/login/desbloquear` | Acceso/configuracion | seguimiento | completa | auth local | no | publico/control UI | security event + rate-limit | no | no | desbloqueo administrativo futuro |
| `/login/desbloquear/confirmar` | Acceso/configuracion | seguimiento | completa | auth local | no | publico/control UI | security event | no | no | destino de correo institucional futuro |
| `/home` | Acceso/configuracion | seguimiento | completa | mapa fisico hospitalario + Screen Capability Registry | no | sesion local | no | no | no | mantener el mapa como lugares fisicos, no como arbol de acciones |
| `/mapa` | Acceso/configuracion | seguimiento | completa | redirect App Router | no | sesion local | no | no | no | alias legacy hacia home |
| `/configuracion` | Acceso/configuracion | seguimiento | completa | App Router | no | sesion local | no | no | estado/config | administracion clinica futura |
| `/configuracion/apariencia` | Acceso/configuracion | seguimiento | completa | preferencias UI | no | sesion local | no | no | no | tokens visuales futuros |
| `/configuracion/ia` | Acceso/configuracion | seguimiento | completa | AI status | no | sesion local | no | no | estado Ollama | IA externa bloqueada: anonimizar payload, preview humano, autorizacion explicita, auditoria y politica PHI |
| `/configuracion/api` | Acceso/configuracion | seguimiento | completa | config API/OpenAPI | no | sesion local | no | no | no | health y versionado |
| `/pacientes` | Nucleo paciente | paciente | completa | API pacientes / demo | no | lectura paciente | no | no | no | buscador universal avanzado y ultimos abiertos |
| `/pacientes/nuevo` | Nucleo paciente | paciente | completa | API pacientes | si | escritura paciente | si | no | no | identidad administrativa mas completa |
| `/pacientes/[patientId]` | Nucleo paciente | paciente | completa | redirect App Router | no | lectura paciente | no | no | no | mantener como entrada a ficha |
| `/pacientes/[patientId]/ficha` | Nucleo paciente | paciente | completa | record paciente + assistant timeline | no | lectura paciente | no | carta | lectura/pendientes | antecedentes, resultados y timeline avanzada existen en ficha; documentos longitudinales siguen futuros |
| `/pacientes/[patientId]/estado` | Nucleo paciente | seguimiento | completa | API paciente | si | medico/admin/dev | si | no | no | estados clinicos mas finos |
| `/pacientes/[patientId]/eventos` | Nucleo paciente | acto clinico | completa | clinical events | si | escritura clinica | si | no | lectura contextual | curaduria minima de antecedentes con categoria/fuente/limite; clasificacion estructurada futura |
| `/pacientes/[patientId]/problemas` | Nucleo paciente | paciente | completa | problemas activos | no | lectura paciente | no | no | lectura contextual | diagnosticos historicos/CIE-10 futuros |
| `/pacientes/[patientId]/problemas/nuevo` | Nucleo paciente | acto clinico | completa | problemas activos | si | medico/admin/dev | si | no | no | clasificacion diagnostica futura |
| `/pacientes/[patientId]/alergias` | Seguridad/auditoria | paciente | completa | alergias activas | no | lectura paciente | no | no | lectura contextual | alertas criticas mas amplias |
| `/pacientes/[patientId]/alergias/nueva` | Seguridad/auditoria | acto clinico | completa | alergias activas | si | medico/admin/dev | si | no | no | reacciones adversas futuras |
| `/pacientes/[patientId]/medicacion` | Medicacion/vademecum | paciente | completa/en expansion gobernada | medicacion activa + vademecum local curado | no | lectura paciente | no | no | sugeridos deterministas | vademecum real curado, interacciones y receta futura |
| `/pacientes/[patientId]/medicacion/nueva` | Medicacion/vademecum | acto clinico | completa/en expansion gobernada | medicacion activa + validacion dosis | si | escritura clinica | si | no | no generativa | receta/orden no se deriva automaticamente |
| `/pacientes/[patientId]/signos-vitales` | Ordenes/resultados | seguimiento | completa | signos vitales | no | lectura paciente | no | no | series | tabla/grafico mas amplio |
| `/pacientes/[patientId]/signos-vitales/nuevo` | Ordenes/resultados | acto clinico | completa | signos vitales | si | enfermeria/medico/admin/dev | si | no | no | escalas y monitoreo futuros |
| `/pacientes/[patientId]/encuentros` | Episodios | episodio | completa | API encuentros | no | lectura paciente | no | no | lectura contextual | episodio ambulatorio/hospitalizado mas explicito |
| `/pacientes/[patientId]/encuentros/nuevo` | Episodios | episodio | completa | API encuentros | si | medico/admin/dev | si | no | no | preconsulta minima ya integrada en atencion; admision avanzada futura |
| `/pacientes/[patientId]/evoluciones` | Episodios | acto clinico | completa | clinical entries | no | lectura paciente | no | carta | lectura contextual | filtros por episodio/problema |
| `/pacientes/[patientId]/evoluciones/nueva` | Episodios | acto clinico | completa | clinical entries | si | medico/admin/dev | si | carta | borrador revisable | firma real futura |
| `/pacientes/[patientId]/evoluciones/desde-eventos` | Episodios | acto clinico | completa | eventos + AI-Chart | si | medico/admin/dev + permiso IA | si | carta | borrador revisable | mantener como borrador revisado |
| `/pacientes/[patientId]/documentos` | Documentos/papel | documento | completa | record + print routes | no | lectura paciente | no | carta | no | adjuntos externos, consentimientos y firma real futuros |
| `/pacientes/[patientId]/ia` | IA clinica | seguimiento | completa | AI status/sugerencias | no | lectura paciente + permiso IA | no | no | apoyo contextual | IA como apoyo, no modulo central |
| `/pacientes/[patientId]/ai-chart` | IA clinica | acto clinico | completa | AI-Chart + Assistant Read | si via `ClinicalPatch` | medico/admin/dev + permiso IA | si si confirma | SOAP carta | lectura, series, borrador | mantener `v0.4-assistant-read` cerrado; no expandir IA antes de nucleo paciente |
| `/pacientes/[patientId]/auditoria` | Seguridad/auditoria | seguimiento | completa | audit events | no | lectura auditoria | no | no | no | auditoria de accesos futura |
| `/consulta` | Ambulatorio | seguimiento | completa | App Router | no | lectura paciente | no | no | no | mantener como indice simple |
| `/consulta/agenda` | Ambulatorio | episodio | completa | `clinical_appointments` | si | medico/admin/dev | si | no | no | preconsulta minima enlazada desde atencion; agenda por equipos futura |
| `/consulta/pacientes/[patientId]/atencion` | Ambulatorio | acto clinico | completa | encuentros + SOAP + preconsulta minima | si | medico/admin/dev; preconsulta enfermeria/medico/admin/dev | si | no | borrador revisable | preconsulta minima con `workflow_kind=ambulatory_preconsult`; diagnosticos finales futuros |
| `/consulta/pacientes/[patientId]/resumen` | Ambulatorio | seguimiento | completa | record + appointments + encounters | no | lectura paciente | no | no | lectura resumida | seguimiento formal e interconsultas futuras |
| `/hospitalizacion` | Hospitalizacion | seguimiento | completa | App Router | no | lectura paciente | no | no | no | mantener como indice simple |
| `/hospitalizacion/camas` | Hospitalizacion | episodio | completa | hospitalizacion + camas | si | medico/admin/dev | si | no | no | censo por servicio/equipo |
| `/hospitalizacion/camas/nueva` | Hospitalizacion | episodio | completa | camas | si | medico/admin/dev | si | no | no | administracion institucional futura |
| `/hospitalizacion/rondas` | Hospitalizacion | seguimiento | completa | ingresos + camas + hojas | no | lectura paciente | no | carta | lectura contextual | read-model backend si escala |
| `/hospitalizacion/pacientes/[patientId]/epicrisis` | Hospitalizacion | documento | completa | `clinical_entries(kind=discharge_summary)` | si | medico/admin/dev | si | carta | borrador revisable | firma real, cierre legal y alta formal futuros |
| `/hospitalizacion/pacientes/[patientId]/ingreso` | Hospitalizacion | documento | completa | `clinical_entries(kind=intake)` | si | medico/admin/dev | si | carta | borrador revisable | firma real y cierre legal futuros |
| `/hospitalizacion/pacientes/[patientId]/hoja-diaria` | Hospitalizacion | acto clinico | completa | hojas diarias | si | medico/admin/dev | si | carta | lectura contextual | evolucion hospitalaria por problema |
| `/hospitalizacion/pacientes/[patientId]/hoja-diaria/[sheetId]/editar` | Hospitalizacion | acto clinico | completa | hojas diarias | si | medico/admin/dev | si | carta | no | firma/bloqueo legal futuro |
| `/hospitalizacion/pacientes/[patientId]/indicaciones` | Hospitalizacion | acto clinico | completa | indicaciones draft | si | medico/admin/dev | si | carta | apoyo no ejecutable | ejecucion bloqueada: orden firmada, doble chequeo, MAR activo, administracion y auditoria futuras |
| `/print/pacientes/[patientId]/ficha` | Documentos/papel | documento | completa | record paciente | no | lectura paciente | no | carta | no | paridad con ficha expandida |
| `/print/pacientes/[patientId]/evolucion/[entryId]` | Documentos/papel | documento | completa | clinical entry | no | lectura paciente | no | carta | no | firma real futura |
| `/print/pacientes/[patientId]/resumen` | Documentos/papel | documento | completa | record paciente | no | lectura paciente | no | carta | resumen no persistido | resumen IA no persistido |
| `/print/pacientes/[patientId]/receta` | Documentos/papel | documento | bloqueada | politica receta | no | lectura paciente | no | bloqueado | no | receta valida requiere firma, folio, actor, fecha clinica y permisos |
| `/print/hospitalizacion/rondas` | Documentos/papel | documento | completa | rondas lectura | no | lectura paciente | no | carta | no | read-model si escala |
| `/print/hospitalizacion/pacientes/[patientId]/epicrisis/[entryId]` | Documentos/papel | documento | completa | `clinical_entries(kind=discharge_summary)` | no | lectura paciente | no | carta | no | firma real futura |
| `/print/hospitalizacion/pacientes/[patientId]/ingreso/[entryId]` | Documentos/papel | documento | completa | `clinical_entries(kind=intake)` | no | lectura paciente | no | carta | no | firma real futura |
| `/print/hospitalizacion/pacientes/[patientId]/hoja-diaria/[sheetId]` | Documentos/papel | documento | completa | hoja diaria | no | lectura paciente | no | carta | no | firma real futura |
| `/print/hospitalizacion/pacientes/[patientId]/indicacion/[indicationId]` | Documentos/papel | documento | completa | indicacion draft | no | lectura paciente | no | carta | no | no equivale a orden firmada |

## Superficies futuras del mapa maestro

Estas superficies pertenecen a la ficha tradicional, pero no deben crearse hasta
tener contrato minimo y flujo humano verificable.

| Superficie | Modulo | Momento clinico | Estado | Fuente esperada | Escritura | Permisos | Auditoria | Papel | IA permitida | Condicion de entrada |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Antecedentes medicos/quirurgicos/familiares/sociales | Nucleo paciente | paciente | futura | eventos o entidad dedicada | si | medico/admin/dev | si | no | lectura contextual | contrato minimo y lectura en ficha |
| Diagnosticos historicos/CIE-10 | Nucleo paciente | paciente | futura | problemas/diagnosticos | si | medico/admin/dev | si | no | lectura contextual | distinguir problema activo vs diagnostico |
| Vacunas | Nucleo paciente | paciente | futura | entidad dedicada | si | medico/admin/dev | si | si si aplica | lectura contextual | permisos y esquema de inmunizacion |
| Dispositivos/protesis/accesos | Nucleo paciente | paciente | futura | entidad dedicada o eventos | si | medico/admin/dev | si | no | lectura contextual | uso clinico claro |
| Linea de tiempo avanzada/filtrable | Nucleo paciente | seguimiento | completa/en expansion gobernada | eventos + encuentros + resultados | no | lectura paciente | no | no | lectura contextual | filtros y dominios viven dentro de ficha; documentos longitudinales siguen futuros |
| Buscador longitudinal | Nucleo paciente | seguimiento | futura | eventos + entradas + resultados | no | lectura paciente | no | no | busqueda asistida | no duplicar Assistant Read |
| Agenda avanzada/productiva | Ambulatorio | episodio | futura | citas + equipos + admision | si | admision/medico/admin/dev futuro | si | no | no | agenda y preconsulta minimas ya existen; falta agenda por recursos/equipos |
| Preconsulta/admision ambulatoria avanzada | Ambulatorio | episodio | futura | cita + encuentro + signos + evento clinico | si | enfermeria/medico/admin/dev; admision futuro | si | no | faltantes | preconsulta minima de enfermeria ya existe; faltan admision administrativa, equipos y cierre operacional |
| Motivo de consulta estructurado | Ambulatorio | acto clinico | futura | encuentro + entrada clinica | si | medico/admin/dev | si | si si aplica | apoyo SOAP | contrato antes de UI amplia |
| Cierre de consulta | Ambulatorio | firma/estado | futura | encuentro + estado | si | medico/admin/dev | si | si si aplica | no firma | diagnostico/plan/cierre borrador |
| Receta valida | Ambulatorio/documentos | documento | bloqueada | receta firmada | si | medico/admin/dev futuro | si | carta/A5 | no | firma, folio, actor, fecha clinica, permisos y politica activa |
| Ordenes ambulatorias | Ordenes/resultados | acto clinico | futura | ordenes clinicas | si | medico/admin/dev | si | carta | apoyo no ejecutable | tipos de orden y estados |
| Interconsultas/derivaciones | Ambulatorio/hospitalizacion | acto clinico | futura | solicitudes/respuestas | si | medico/admin/dev | si | carta | resumen/fuentes | pregunta clinica, prioridad, cierre |
| Ingreso medico hospitalario firmado | Hospitalizacion | documento | futura | documento ingreso firmado | si | medico/admin/dev futuro | si | carta | borrador revisable | ingreso borrador ya existe; falta firma/cierre legal |
| Evolucion hospitalaria por problema | Hospitalizacion | acto clinico | futura | clinical entries + encuentro | si | medico/admin/dev | si | carta | lectura contextual | no duplicar hoja diaria |
| Evoluciones de enfermeria | Hospitalizacion | acto clinico | futura | notas enfermeria | si | enfermeria/admin/dev | si | carta si aplica | no generativa | permisos enfermeria y turno |
| Kardex | Hospitalizacion | seguimiento | bloqueada | indicaciones ejecutables | si | enfermeria/medico/admin/dev futuro | si | no | no | requiere orden firmada, doble chequeo, MAR activo, administracion y auditoria |
| Administracion de medicamentos | Hospitalizacion | acto clinico | bloqueada | indicaciones ejecutables + MAR | si | enfermeria/admin/dev futuro | si | no | alertas/fuentes | requiere orden firmada, doble chequeo, MAR activo, administracion y auditoria |
| Balance hidrico | Hospitalizacion | seguimiento | futura | observaciones balance | si | enfermeria/admin/dev | si | no | no | periodos, totales y auditoria |
| Resultados laboratorio UI amplia | Ordenes/resultados | seguimiento | futura | `lab_panels`/`lab_results` | no inicialmente | lectura paciente | no | carta si aplica | series/fuentes | la ficha/AI-Chart ya tienen lectura minima; falta vista amplia sin dashboard |
| Imagenes e informes radiologicos | Ordenes/resultados | seguimiento | futura | informes/documentos | no inicialmente | lectura paciente | no | carta si aplica | resumen/fuentes | sin PACS real por ahora |
| Microbiologia | Ordenes/resultados | seguimiento | futura | resultados estructurados | no inicialmente | lectura paciente | no | carta si aplica | series/fuentes | contrato antes de UI |
| Anatomia patologica | Ordenes/resultados | seguimiento | futura | informes/documentos | no inicialmente | lectura paciente | no | carta si aplica | resumen/fuentes | contrato antes de UI |
| Procedimientos | Hospitalizacion/ambulatorio | acto clinico | futura | procedimientos | si | medico/admin/dev | si | carta | apoyo no ejecutable | solicitud, consentimiento y protocolo |
| Alta/epicrisis firmada | Hospitalizacion/documentos | documento | futura | documento egreso firmado | si | medico/admin/dev futuro | si | carta | borrador revisable | epicrisis borrador ya existe; falta firma/cierre legal y alta formal |
| Consentimientos | Documentos/papel | documento | futura | documentos firmados | si | medico/admin/dev futuro | si | carta | no | plantilla versionada, firmante, fecha, custodia y revocacion |
| Adjuntos/documentos externos | Documentos/papel | documento | futura | almacenamiento documental | si | admin/dev futuro | si | segun tipo | resumen futuro | almacenamiento documental, tipo, virus scan, PHI policy, retencion y trazabilidad |
| Seguridad clinica ampliada | Seguridad/auditoria | seguimiento | completa/en expansion gobernada | `ClinicalRisk` bajo paciente | si | enfermeria/medico/admin/dev | si | no | fuentes/resumen | riesgo minimo en ficha; historico avanzado, scores y dashboard siguen fuera |
| Farmacovigilancia | Seguridad/auditoria | seguimiento | futura | eventos adversos + fuentes | si | medico/admin/dev | si | no | no automatica | no usar FAERS como contraindicacion automatica |
| Auditoria de accesos | Seguridad/auditoria | seguimiento | futura | access logs | no | admin/dev | no | no | no | separar acceso de modificacion clinica |
| Administracion clinica | Administracion clinica | seguimiento | futura | usuarios/catalogos/plantillas | si | admin/dev | si | no | no | no bloquear piloto clinico actual |
| IA externa | IA clinica | seguimiento | bloqueada | proveedor externo futuro | no | admin/dev futuro | si si se habilita | no | solo con autorizacion | anonimizar payload, preview humano, autorizacion explicita, auditoria y politica PHI |

## Secuencia de construccion

| Bloque | Pantalla inicial | Contrato requerido | Criterio de promocion |
| --- | --- | --- | --- |
| Nucleo paciente faltante | antecedentes dentro de ficha existente | reusar eventos/problemas/alergias/medicacion antes de entidad dedicada | antecedentes visibles en ficha como lectura minima, con faltantes declarados y sin duplicar eventos |
| Linea de tiempo avanzada | vista longitudinal dentro de ficha | lectura compuesta de eventos, encuentros, entradas, documentos y resultados | filtros por dominio, fuente inspeccionable y sin escritura |
| Diagnosticos historicos | extension de problemas | contrato que separe problema activo, diagnostico historico y codificacion | no mezclar estado activo con diagnostico cerrado |
| Ambulatorio minimo | `/consulta/agenda` | `ClinicalAppointment` con estados reales | implementado como agenda persistida; preconsulta minima vive en atencion |
| Consulta completa | `/consulta/pacientes/[patientId]/atencion` | cierre de encuentro, diagnostico/plan y documento si aplica | SOAP/plan/cierre con auditoria y sin receta valida automatica |
| Preconsulta ambulatoria | agenda/atencion existentes | reutilizar cita, encuentro ambulatorio con `workflow_kind=ambulatory_preconsult`, signos vitales y evento clinico de preconsulta | implementada como panel minimo en atencion; enfermeria puede completarla con permiso estrecho y admision sigue futura |
| Resumen ambulatorio | `/consulta/pacientes/[patientId]/resumen` | lectura de record, citas y encuentros existentes | implementado como vista de lectura; seguimiento formal queda futuro |
| Hospitalizacion critica | ingreso medico | `ClinicalEntry(kind=intake)` vinculado a encuentro hospitalario | papel carta, borrador y auditoria implementados; firma/cierre legal futuros |
| Evolucion hospitalaria | hoja diaria/evolucion por problema | entradas por problema vinculadas a ingreso | no reemplazar firma real; mantener borrador trazable |
| Alta/epicrisis | epicrisis borrador | `ClinicalEntry(kind=discharge_summary)` vinculado a hospitalizacion activa | salida imprimible como borrador no firmado; firma/cierre legal futuros |
| Laboratorio sobrio | resultados en ficha o AI-Chart | reutilizar `lab_panels`/`lab_results` existentes | lectura minima con fuente especifica por resultado; UI amplia queda futura y sin dashboard |
| Imagenes/informes | informes como documentos clinicos | contrato documental o resultado estructurado minimo | no crear PACS ni visor complejo |
| Seguridad clinica | alertas/riesgos | `ClinicalRisk` minimo con fuente, severidad, estado y accion humana | implementado en ficha; sin scores automaticos ni dashboard |
| Papel tradicional | ingreso, evolucion, indicacion, epicrisis | estado documental, actor/fecha si existen y ruta print | hoja carta, metadata documental visible, sin fallback silencioso y footer de desarrollo si no firmado |
| Indice de documentos | `/pacientes/[patientId]/documentos` | rutas print existentes y entradas del record | implementado como indice; adjuntos externos y consentimientos quedan futuros |

## Contratos minimos antes de UI amplia

Estos contratos sirven como condicion de entrada para los proximos PRs y
bloquean pantallas decorativas. Si una fila queda implementada parcialmente,
el mapa debe declarar que sigue pendiente.

| Superficie | Modelo minimo | API minima futura | UI minima permitida | Papel | Tests obligatorios |
| --- | --- | --- | --- | --- | --- |
| Agenda real | `ClinicalAppointment`: paciente, inicio, fin opcional, motivo, ubicacion, profesional/equipo opcional y estado `scheduled/check_in/in_progress/completed/cancelled/no_show` | implementado: listar por fecha/rango, crear, actualizar estado y listar por paciente | `/consulta/agenda` muestra agenda persistida, estados reales y enlace a atencion | no aplica inicialmente | permisos, auditoria de escritura, E2E agenda -> paciente -> atencion |
| Admision/preconsulta ambulatoria | Reutilizar `ClinicalAppointment`, `ClinicalEncounter(type=ambulatory)`, `VitalSign` y `ClinicalEvent(event_type=clinical_note)`; no tabla nueva en el primer PR | usa endpoints existentes de citas, encuentros, signos y eventos; endpoint compuesto solo si evita duplicar logica clinica real | panel sobrio dentro de atencion: confirmar identidad local, motivo breve, signos, revision alergias/medicacion, prioridad textual y pendientes | sin papel inicialmente; si se convierte en documento, resumen carta futuro con estado borrador | `solo_lectura` solo lee; preconsulta minima escribe con `enfermeria/medico/admin/dev`; enfermeria solo puede crear el encuentro tecnico de preconsulta, no encuentros generales; admision administrativa sigue futura; 404 por paciente/cita/encuentro ajeno; auditoria en cada escritura; E2E agenda -> preconsulta -> atencion |
| Atencion ambulatoria cerrable | `ClinicalEncounter` existente con `status=completed`, `ended_at`, evolucion SOAP vinculada y plan documentado | implementado minimo reutilizando PATCH de encuentros y entradas clinicas existentes | `/consulta/pacientes/[patientId]/atencion` permite crear borrador y cerrar encuentro como no firmado con destino/auditoria visibles | resumen carta futuro si produce documento | cierre exige actor, auditoria, no receta valida automatica y no orden ejecutable |
| Ingreso medico hospitalario | `ClinicalEntry(kind=intake)` vinculado a encuentro `hospitalization`; no tabla nueva en primer PR | implementado reutilizando entradas clinicas vinculadas al ingreso | pantalla hospitalaria de ingreso como borrador editable, con secciones clinicas minimas | carta obligatoria de ingreso borrador | encuentro debe ser hospitalario, permisos medico/admin/dev, auditoria y print sin fallback |
| Epicrisis borrador | `ClinicalEntry(kind=discharge_summary)` vinculado a encuentro `hospitalization`; no tabla nueva en primer PR | implementado reutilizando entradas clinicas vinculadas a la hospitalizacion | pantalla unica de epicrisis vinculada al ingreso, sin firma legal | carta obligatoria con estado draft y footer desarrollo | encuentro debe ser hospitalario, permisos medico/admin/dev, auditoria y print sin fallback |
| Papel tradicional | documento clinico con fuente, estado, actor y fecha clinica cuando existan | no API nueva salvo documento fuente; print lee por ID especifico | boton `Ver papel` solo si la fuente existe o declara `sin papel aun` | carta por defecto | smoke print, sin fallback al primer registro, estado visible y footer si no firmado |
| Riesgos clinicos | `ClinicalRisk` con paciente, encuentro opcional, tipo, severidad, estado, fuente, accion humana y revision | implementado bajo paciente: listar, crear, leer y corregir; sin ruta global de riesgos | resumen sobrio dentro de ficha; atencion/hospitalizacion futura, sin dashboard | sin papel inicialmente; si se vuelve documento, hoja carta de resumen de riesgos | permisos por rol, auditoria before/after, fuentes inspeccionables, E2E de alerta visible y no automatica |

### Contrato `PROG-AMB-PRECONSULTA-00`

Estado inicial: implementacion minima integrada en `/consulta/pacientes/[patientId]/atencion`.

Objetivo: preparar la primera preconsulta ambulatoria minima sin crear una
pantalla grande ni una capa nueva. La preconsulta ordena el paso desde cita a
atencion, pero no firma, no receta, no emite orden y no reemplaza la consulta
medica.

Fuente de verdad inicial:

- `ClinicalAppointment`: agenda, estado `check_in`/`in_progress`, motivo,
  ubicacion y profesional/equipo textual.
- `ClinicalEncounter(type=ambulatory)`: episodio clinico al que se vinculan
  signos, eventos y evolucion posterior.
- `VitalSign`: mediciones tomadas en admision o enfermeria.
- `ClinicalEvent(event_type=clinical_note)`: nota de preconsulta con
  `payload.preconsult` para prioridad textual, revision de alergias/medicacion,
  faltantes y observaciones.

Payload sugerido para el evento de preconsulta:

```json
{
  "preconsult": {
    "identity_checked": true,
    "chief_complaint": "texto breve",
    "triage_priority": "routine|priority|urgent|unknown",
    "allergies_reviewed": true,
    "medications_reviewed": true,
    "missing_data": ["dato faltante"],
    "human_action": "revisar en atencion"
  }
}
```

Permisos y auditoria:

- lectura: mismos roles que lectura de paciente, incluyendo `solo_lectura`
- escritura de preconsulta minima: `enfermeria`, `medico`, `admin` y `dev`
- decision post-#35: `enfermeria` puede crear solo el encuentro ambulatorio
  tecnico de preconsulta; no puede crear hospitalizaciones, encuentros
  ambulatorios comunes ni actualizar/cancelar encuentros
- `admision` sigue futura hasta existir rol administrativo y limites propios
- `solo_lectura` no puede cambiar estado de cita, signos ni evento
- toda escritura usa endpoints existentes con auditoria de dominio
- la UI debe validar pertenencia del paciente a cita, encuentro, signo y evento;
  el backend debe responder `404` ante recursos ajenos

IA permitida:

- solo lectura de faltantes y resumen contextual con fuentes
- Ollama/local puede redactar un resumen no persistido si la pantalla declara
  esa capacidad en el registry
- prohibido: chat libre, diagnostico autonomo, receta, orden, firma, cierre
  automatico o `ClinicalPatch` desde preconsulta

Criterio de promocion a `completa`:

- contrato implementado con entidades existentes o justificacion explicita de
  entidad nueva
- permisos, auditoria y tests API si escribe
- UI minima en atencion, sin ruta nueva
- E2E visible con selectores exactos: cita -> check-in -> preconsulta ->
  atencion
- `SCREEN_TREE`, Screen Capability Registry y `CURRENT_STATE` actualizados en
  el mismo PR

### Contrato `PROG-CLINICAL-RISK-00`

Estado: implementado como minimo por `PROG-CLINICAL-RISK-01`.

Objetivo: definir riesgos clinicos estructurados antes de crear UI amplia. El
foco inicial es seguridad visible, no scores automaticos ni alertas opacas.

Tipos iniciales permitidos:

- `fall`: riesgo de caida
- `pressure_injury`: riesgo de UPP
- `vte`: riesgo tromboembolico
- `isolation`: aislamiento/precaucion
- `adverse_event`: evento adverso o casi evento
- `other`: riesgo clinico local no clasificado

Modelo minimo implementado:

- `patient_id` obligatorio y `encounter_id` opcional
- `risk_type`, `severity` (`low|moderate|high|critical|unknown`) y `status`
  (`active|resolved|entered_in_error`)
- `source_kind` (`manual|vital_sign|clinical_event|clinical_entry|lab_result`)
  y `source_ref` para inspeccionar la fuente
- `reason`, `human_action`, `reviewed_at`, `created_by` y timestamps
- no usar `ActiveProblem` como sustituto de riesgo activo; diagnostico y riesgo
  clinico tienen ciclos de vida distintos

API minima implementada:

- bajo paciente: listar, crear, leer y corregir riesgos; no ruta global `/risks`
- validar pertenencia de paciente, encuentro y fuente
- `solo_lectura` puede ver, pero no crear ni corregir
- escritura permitida por defecto a `enfermeria`, `medico`, `admin` y `dev`;
  excepciones por tipo deben documentarse antes de implementar
- correccion por estado `entered_in_error`, no delete fisico
- auditoria con `before/after`, `patient_id`, `risk_id`, `risk_type`,
  `severity`, `status`, fuente y `correlation_id`

UI minima implementada:

- mostrar resumen compacto de riesgos activos en ficha y pantallas clinicas
  existentes; hoy vive en ficha; no dashboard de seguridad
- cada alerta muestra severidad, razon, fuente, fecha, limite y accion humana
- no bloquear flujo clinico por inferencia automatica; solo resaltar y exigir
  revision humana
- resultados resueltos o `entered_in_error` siguen visibles en auditoria o
  historial, pero no como alerta activa

IA permitida:

- solo lectura, resumen de faltantes y explicacion de fuentes
- prohibido generar diagnostico, score automatico, orden, receta, aislamiento
  automatico, indicacion ejecutable o `ClinicalPatch`
- cualquier sugerencia debe decir "requiere revision" y mostrar fuente/limite

Criterio de promocion a `completa/en expansion gobernada`:

- entidad `ClinicalRisk` creada con contrato actualizado
- API bajo paciente, permisos, auditoria, OpenAPI y tipos TS
- UI minima en ficha, sin ruta global
- E2E de ficha cubre presencia de riesgos y ausencia de automatizacion
- `SCREEN_TREE` y `CURRENT_STATE` actualizados en el mismo PR

## Reglas de promocion

- De `futura` a `preparada`: debe declarar en UI que no simula flujo productivo y tener E2E si queda visible.
- De `preparada` a `completa`: requiere API/PostgreSQL/permisos/auditoria/OpenAPI/UI, y papel si produce documento clinico.
- De `bloqueada` a cualquier otro estado: requiere registrar primero la regla clinica/legal que quita el bloqueo.
- Una pantalla completa no puede depender de fallback silencioso al primer paciente, documento o registro si la ruta trae ID.
- IA puede sugerir o resumir, pero no convierte una pantalla futura en completa ni firma documentos.
- La IA permitida por pantalla se declara en el Screen Capability Registry; una accion no declarada debe quedar bloqueada antes de ejecutarse.
- Receta valida, firma clinica, folio, despacho, administracion de medicamentos, ordenes ejecutables, agenda avanzada e IA externa siguen bloqueadas/futuras hasta cumplir sus contratos.
