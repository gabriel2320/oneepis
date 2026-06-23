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
| `/` | Acceso/configuracion | seguimiento | completa | redirect App Router | no | publico/control UI | no | no | no | mantener entrada a `/pacientes` |
| `/login` | Acceso/configuracion | seguimiento | completa | auth local | no | publico/control UI | no | no | no | seleccion institucion/rol futura |
| `/configuracion` | Acceso/configuracion | seguimiento | completa | App Router | no | sesion local | no | no | estado/config | administracion clinica futura |
| `/configuracion/apariencia` | Acceso/configuracion | seguimiento | completa | preferencias UI | no | sesion local | no | no | no | tokens visuales futuros |
| `/configuracion/ia` | Acceso/configuracion | seguimiento | completa | AI status | no | sesion local | no | no | estado Ollama | preferencias Ollama/local futuras |
| `/configuracion/api` | Acceso/configuracion | seguimiento | completa | config API/OpenAPI | no | sesion local | no | no | no | health y versionado |
| `/pacientes` | Nucleo paciente | paciente | completa | API pacientes / demo | no | lectura paciente | no | no | no | buscador universal avanzado y ultimos abiertos |
| `/pacientes/nuevo` | Nucleo paciente | paciente | completa | API pacientes | si | escritura paciente | si | no | no | identidad administrativa mas completa |
| `/pacientes/[patientId]` | Nucleo paciente | paciente | completa | redirect App Router | no | lectura paciente | no | no | no | mantener como entrada a ficha |
| `/pacientes/[patientId]/ficha` | Nucleo paciente | paciente | completa | record paciente | no | lectura paciente | no | carta | lectura/pendientes | antecedentes pendientes; resultados y timeline con lectura minima |
| `/pacientes/[patientId]/estado` | Nucleo paciente | seguimiento | completa | API paciente | si | medico/admin/dev | si | no | no | estados clinicos mas finos |
| `/pacientes/[patientId]/eventos` | Nucleo paciente | acto clinico | completa | clinical events | si | escritura clinica | si | no | lectura contextual | linea de tiempo completa futura |
| `/pacientes/[patientId]/problemas` | Nucleo paciente | paciente | completa | problemas activos | no | lectura paciente | no | no | lectura contextual | diagnosticos historicos/CIE-10 futuros |
| `/pacientes/[patientId]/problemas/nuevo` | Nucleo paciente | acto clinico | completa | problemas activos | si | medico/admin/dev | si | no | no | clasificacion diagnostica futura |
| `/pacientes/[patientId]/alergias` | Seguridad/auditoria | paciente | completa | alergias activas | no | lectura paciente | no | no | lectura contextual | alertas criticas mas amplias |
| `/pacientes/[patientId]/alergias/nueva` | Seguridad/auditoria | acto clinico | completa | alergias activas | si | medico/admin/dev | si | no | no | reacciones adversas futuras |
| `/pacientes/[patientId]/medicacion` | Medicacion/vademecum | paciente | completa/en expansion gobernada | medicacion activa + vademecum local curado | no | lectura paciente | no | no | sugeridos deterministas | vademecum real curado, interacciones y receta futura |
| `/pacientes/[patientId]/medicacion/nueva` | Medicacion/vademecum | acto clinico | completa/en expansion gobernada | medicacion activa + validacion dosis | si | escritura clinica | si | no | no generativa | receta/orden no se deriva automaticamente |
| `/pacientes/[patientId]/signos-vitales` | Ordenes/resultados | seguimiento | completa | signos vitales | no | lectura paciente | no | no | series | tabla/grafico mas amplio |
| `/pacientes/[patientId]/signos-vitales/nuevo` | Ordenes/resultados | acto clinico | completa | signos vitales | si | enfermeria/medico/admin/dev | si | no | no | escalas y monitoreo futuros |
| `/pacientes/[patientId]/encuentros` | Episodios | episodio | completa | API encuentros | no | lectura paciente | no | no | lectura contextual | episodio ambulatorio/hospitalizado mas explicito |
| `/pacientes/[patientId]/encuentros/nuevo` | Episodios | episodio | completa | API encuentros | si | medico/admin/dev | si | no | no | admision/preconsulta futura |
| `/pacientes/[patientId]/evoluciones` | Episodios | acto clinico | completa | clinical entries | no | lectura paciente | no | carta | lectura contextual | filtros por episodio/problema |
| `/pacientes/[patientId]/evoluciones/nueva` | Episodios | acto clinico | completa | clinical entries | si | medico/admin/dev | si | carta | borrador revisable | firma real futura |
| `/pacientes/[patientId]/evoluciones/desde-eventos` | Episodios | acto clinico | completa | eventos + AI-Chart | si | medico/admin/dev + permiso IA | si | carta | borrador revisable | mantener como borrador revisado |
| `/pacientes/[patientId]/documentos` | Documentos/papel | documento | preparada | UI preparada | no | lectura paciente | no | no | no | documentos reales, adjuntos, consentimientos |
| `/pacientes/[patientId]/ia` | IA clinica | seguimiento | completa | AI status/sugerencias | no | lectura paciente + permiso IA | no | no | apoyo contextual | IA como apoyo, no modulo central |
| `/pacientes/[patientId]/ai-chart` | IA clinica | acto clinico | completa | AI-Chart + Assistant Read | si via `ClinicalPatch` | medico/admin/dev + permiso IA | si si confirma | SOAP carta | lectura, series, borrador | cerrar `v0.4-assistant-read` |
| `/pacientes/[patientId]/auditoria` | Seguridad/auditoria | seguimiento | completa | audit events | no | lectura auditoria | no | no | no | auditoria de accesos futura |
| `/consulta` | Ambulatorio | seguimiento | completa | App Router | no | lectura paciente | no | no | no | mantener como indice simple |
| `/consulta/agenda` | Ambulatorio | episodio | preparada | UI preparada | no | lectura paciente | no | no | no | agenda productiva |
| `/consulta/pacientes/[patientId]/atencion` | Ambulatorio | acto clinico | completa | encuentros + SOAP | si | medico/admin/dev | si | no | borrador revisable | cierre de consulta y diagnosticos finales |
| `/consulta/pacientes/[patientId]/resumen` | Ambulatorio | seguimiento | preparada | UI preparada | no | lectura paciente | no | no | lectura resumida | resumen ambulatorio real si aporta sobre ficha |
| `/hospitalizacion` | Hospitalizacion | seguimiento | completa | App Router | no | lectura paciente | no | no | no | mantener como indice simple |
| `/hospitalizacion/camas` | Hospitalizacion | episodio | completa | hospitalizacion + camas | si | medico/admin/dev | si | no | no | censo por servicio/equipo |
| `/hospitalizacion/camas/nueva` | Hospitalizacion | episodio | completa | camas | si | medico/admin/dev | si | no | no | administracion institucional futura |
| `/hospitalizacion/rondas` | Hospitalizacion | seguimiento | completa | ingresos + camas + hojas | no | lectura paciente | no | carta | lectura contextual | read-model backend si escala |
| `/hospitalizacion/pacientes/[patientId]/hoja-diaria` | Hospitalizacion | acto clinico | completa | hojas diarias | si | medico/admin/dev | si | carta | lectura contextual | evolucion hospitalaria por problema |
| `/hospitalizacion/pacientes/[patientId]/hoja-diaria/[sheetId]/editar` | Hospitalizacion | acto clinico | completa | hojas diarias | si | medico/admin/dev | si | carta | no | firma/bloqueo legal futuro |
| `/hospitalizacion/pacientes/[patientId]/indicaciones` | Hospitalizacion | acto clinico | completa | indicaciones draft | si | medico/admin/dev | si | carta | apoyo no ejecutable | orden ejecutable y firma futura |
| `/print/pacientes/[patientId]/ficha` | Documentos/papel | documento | completa | record paciente | no | lectura paciente | no | carta | no | paridad con ficha expandida |
| `/print/pacientes/[patientId]/evolucion/[entryId]` | Documentos/papel | documento | completa | clinical entry | no | lectura paciente | no | carta | no | firma real futura |
| `/print/pacientes/[patientId]/resumen` | Documentos/papel | documento | completa | record paciente | no | lectura paciente | no | carta | resumen no persistido | resumen IA no persistido |
| `/print/pacientes/[patientId]/receta` | Documentos/papel | documento | bloqueada | politica receta | no | lectura paciente | no | bloqueado | no | receta valida requiere firma/folio |
| `/print/hospitalizacion/rondas` | Documentos/papel | documento | completa | rondas lectura | no | lectura paciente | no | carta | no | read-model si escala |
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
| Linea de tiempo completa | Nucleo paciente | seguimiento | futura | eventos + encuentros + documentos | no | lectura paciente | no | no | lectura contextual | partir leyendo fuentes existentes |
| Buscador longitudinal | Nucleo paciente | seguimiento | futura | eventos + entradas + resultados | no | lectura paciente | no | no | busqueda asistida | no duplicar Assistant Read |
| Agenda productiva | Ambulatorio | episodio | futura | citas/appointments | si | admision/medico/admin/dev | si | no | no | modelo de cita y estados |
| Admision/preconsulta ambulatoria | Ambulatorio | episodio | futura | encuentro + observaciones | si | admision/enfermeria/medico/admin/dev | si | no | faltantes | identidad, signos y pendientes |
| Motivo de consulta estructurado | Ambulatorio | acto clinico | futura | encuentro + entrada clinica | si | medico/admin/dev | si | si si aplica | apoyo SOAP | contrato antes de UI amplia |
| Cierre de consulta | Ambulatorio | firma/estado | futura | encuentro + estado | si | medico/admin/dev | si | si si aplica | no firma | diagnostico/plan/cierre borrador |
| Receta valida | Ambulatorio/documentos | documento | bloqueada | receta firmada | si | medico/admin/dev futuro | si | carta/A5 | no | firma, folio, actor, fecha clinica y permisos |
| Ordenes ambulatorias | Ordenes/resultados | acto clinico | futura | ordenes clinicas | si | medico/admin/dev | si | carta | apoyo no ejecutable | tipos de orden y estados |
| Interconsultas/derivaciones | Ambulatorio/hospitalizacion | acto clinico | futura | solicitudes/respuestas | si | medico/admin/dev | si | carta | resumen/fuentes | pregunta clinica, prioridad, cierre |
| Ingreso medico hospitalario | Hospitalizacion | documento | futura | documento ingreso | si | medico/admin/dev | si | carta | borrador revisable | encuentro hospitalario y firma/borrador |
| Evolucion hospitalaria por problema | Hospitalizacion | acto clinico | futura | clinical entries + encuentro | si | medico/admin/dev | si | carta | lectura contextual | no duplicar hoja diaria |
| Evoluciones de enfermeria | Hospitalizacion | acto clinico | futura | notas enfermeria | si | enfermeria/admin/dev | si | carta si aplica | no generativa | permisos enfermeria y turno |
| Kardex | Hospitalizacion | seguimiento | bloqueada | indicaciones ejecutables | si | enfermeria/medico/admin/dev futuro | si | no | no | requiere indicacion ejecutable y doble chequeo |
| Administracion de medicamentos | Hospitalizacion | acto clinico | bloqueada | indicaciones ejecutables + MAR | si | enfermeria/admin/dev futuro | si | no | alertas/fuentes | seguridad medicamentosa y firma/ejecucion |
| Balance hidrico | Hospitalizacion | seguimiento | futura | observaciones balance | si | enfermeria/admin/dev | si | no | no | periodos, totales y auditoria |
| Resultados laboratorio UI | Ordenes/resultados | seguimiento | futura | `lab_panels`/`lab_results` | no inicialmente | lectura paciente | no | carta si aplica | series/fuentes | lectura sobria sin dashboard |
| Imagenes e informes radiologicos | Ordenes/resultados | seguimiento | futura | informes/documentos | no inicialmente | lectura paciente | no | carta si aplica | resumen/fuentes | sin PACS real por ahora |
| Microbiologia | Ordenes/resultados | seguimiento | futura | resultados estructurados | no inicialmente | lectura paciente | no | carta si aplica | series/fuentes | contrato antes de UI |
| Anatomia patologica | Ordenes/resultados | seguimiento | futura | informes/documentos | no inicialmente | lectura paciente | no | carta si aplica | resumen/fuentes | contrato antes de UI |
| Procedimientos | Hospitalizacion/ambulatorio | acto clinico | futura | procedimientos | si | medico/admin/dev | si | carta | apoyo no ejecutable | solicitud, consentimiento y protocolo |
| Alta y epicrisis | Hospitalizacion/documentos | documento | futura | documento egreso | si | medico/admin/dev | si | carta | borrador revisable | borrador no firmado antes de firma real |
| Consentimientos | Documentos/papel | documento | futura | documentos firmados | si | medico/admin/dev futuro | si | carta | no | reglas de firma y custodia |
| Adjuntos/documentos externos | Documentos/papel | documento | futura | almacenamiento documental | si | admin/dev futuro | si | segun tipo | resumen futuro | privacidad, virus scan y trazabilidad |
| Seguridad clinica ampliada | Seguridad/auditoria | seguimiento | futura | alertas/riesgos/eventos | si | rol segun evento | si | no | fuentes/limites | caidas, UPP, TEV, aislamiento, adversos |
| Farmacovigilancia | Seguridad/auditoria | seguimiento | futura | eventos adversos + fuentes | si | medico/admin/dev | si | no | no automatica | no usar FAERS como contraindicacion automatica |
| Auditoria de accesos | Seguridad/auditoria | seguimiento | futura | access logs | no | admin/dev | no | no | no | separar acceso de modificacion clinica |
| Administracion clinica | Administracion clinica | seguimiento | futura | usuarios/catalogos/plantillas | si | admin/dev | si | no | no | no bloquear piloto clinico actual |
| IA externa | IA clinica | seguimiento | bloqueada | proveedor externo futuro | no | admin/dev futuro | si si se habilita | no | solo con autorizacion | anonimizar, preview payload y autorizacion explicita |

## Secuencia de construccion

| Bloque | Pantalla inicial | Contrato requerido | Criterio de promocion |
| --- | --- | --- | --- |
| Nucleo paciente faltante | antecedentes dentro de ficha o ruta dedicada minima | entidad/evento de antecedentes, permisos de escritura, OpenAPI y lectura en ficha | antecedentes visibles en ficha, auditados si escriben y sin duplicar eventos |
| Linea de tiempo completa | vista longitudinal dentro de ficha | lectura compuesta de eventos, encuentros, entradas, documentos y resultados | filtros por dominio, fuente inspeccionable y sin escritura |
| Diagnosticos historicos | extension de problemas | contrato que separe problema activo, diagnostico historico y codificacion | no mezclar estado activo con diagnostico cerrado |
| Ambulatorio minimo | `/consulta/agenda` o admision/preconsulta | modelo de cita/estado o encuentro preconsulta | agenda deja de ser preparada solo si persiste estados reales y E2E |
| Consulta completa | `/consulta/pacientes/[patientId]/atencion` | cierre de encuentro, diagnostico/plan y documento si aplica | SOAP/plan/cierre con auditoria y sin receta valida automatica |
| Hospitalizacion critica | ingreso medico | documento de ingreso vinculado a encuentro hospitalario | papel carta, borrador/closed y auditoria |
| Evolucion hospitalaria | hoja diaria/evolucion por problema | entradas por problema vinculadas a ingreso | no reemplazar firma real; mantener borrador trazable |
| Alta/epicrisis | epicrisis borrador | documento egreso, estado, actor, fecha clinica y papel | salida imprimible como borrador no firmado |
| Laboratorio UI minima | resultados en ficha o AI-Chart | reutilizar `lab_panels`/`lab_results` existentes | lectura sobria, fuentes por resultado y sin dashboard |
| Imagenes/informes | informes como documentos clinicos | contrato documental o resultado estructurado minimo | no crear PACS ni visor complejo |
| Seguridad clinica | alertas/riesgos | contrato por riesgo/evento y severidad | fuente, severidad, limite y accion humana |
| Papel tradicional | ingreso, evolucion, indicacion, epicrisis | estado documental, actor/fecha si existen y ruta print | hoja carta, sin fallback silencioso y footer de desarrollo si no firmado |

## Reglas de promocion

- De `futura` a `preparada`: debe declarar en UI que no simula flujo productivo y tener E2E si queda visible.
- De `preparada` a `completa`: requiere API/PostgreSQL/permisos/auditoria/OpenAPI/UI, y papel si produce documento clinico.
- De `bloqueada` a cualquier otro estado: requiere registrar primero la regla clinica/legal que quita el bloqueo.
- Una pantalla completa no puede depender de fallback silencioso al primer paciente, documento o registro si la ruta trae ID.
- IA puede sugerir o resumir, pero no convierte una pantalla futura en completa ni firma documentos.
- La IA permitida por pantalla se declara en el Screen Capability Registry; una accion no declarada debe quedar bloqueada antes de ejecutarse.
- Receta valida, firma clinica, folio, despacho, administracion de medicamentos, ordenes ejecutables, agenda productiva e IA externa siguen bloqueadas/futuras hasta cumplir sus contratos.
