# Screen Tree

## Decision

El prototipo visual queda aprobado como base. OneEpis no debe crecer por
pantallas sueltas: el arbol maestro se ordena por momentos clinicos.

```text
paciente -> episodio -> acto clinico -> documento -> firma/estado -> seguimiento
```

Estados permitidos:

- `completa`: tiene flujo humano minimo y, si escribe, API/PostgreSQL/permisos/auditoria/OpenAPI/tests.
- `preparada`: existe como borde visible, declara que esta pendiente y no simula produccion.
- `futura`: pertenece al mapa maestro, pero no tiene ruta o contrato listo.

Las pantallas preparadas no cuentan como feature final.

## Navegacion objetivo

La navegacion actual se mantiene. El destino funcional queda agrupado asi:

- Nucleo paciente: ficha, antecedentes, problemas, alergias, medicamentos, signos vitales, eventos, linea de tiempo y auditoria.
- Ambulatorio: agenda, admision/preconsulta, consulta, evolucion, receta, ordenes, interconsulta, cierre y seguimiento.
- Hospitalizado: censo/camas, ingreso medico, hoja diaria, evoluciones, indicaciones, resultados, interconsultas, procedimientos, alta y epicrisis.
- Ordenes y resultados: laboratorio, imagenes, procedimientos y tendencias.
- Documentos/papel: documentos clinicos, importacion futura, exportacion/impresion y hoja carta.
- Seguridad/auditoria: alertas, riesgos, eventos adversos, auditoria de cambios y accesos.
- IA clinica: apoyo contextual dentro de ficha/AI-Chart; no define el centro del producto.

## Rutas reales y estado

| Ruta | Modulo | Estado | Fuente de verdad | Escritura | Papel | Pendiente |
| --- | --- | --- | --- | --- | --- | --- |
| `/` | Inicio | completa | redirect App Router | no | no | mantiene entrada a `/pacientes` |
| `/login` | Acceso | completa | auth local | no | no | seleccion institucion/rol futura |
| `/pacientes` | Nucleo paciente | completa | API pacientes / demo | no | no | buscador universal avanzado y ultimos abiertos |
| `/pacientes/nuevo` | Nucleo paciente | completa | API pacientes | si | no | identidad administrativa mas completa |
| `/pacientes/[patientId]` | Nucleo paciente | completa | redirect App Router | no | no | mantener como entrada a ficha |
| `/pacientes/[patientId]/estado` | Nucleo paciente | completa | API paciente | si | no | estados clinicos mas finos |
| `/pacientes/[patientId]/ficha` | Nucleo paciente | completa | record paciente | no | si | antecedentes y resultados en lectura longitudinal |
| `/pacientes/[patientId]/encuentros` | Episodios | completa | API encuentros | no | no | episodio ambulatorio/hospitalizado mas explicito |
| `/pacientes/[patientId]/encuentros/nuevo` | Episodios | completa | API encuentros | si | no | admision/preconsulta futura |
| `/pacientes/[patientId]/evoluciones` | Acto clinico | completa | clinical entries | no | si | filtros por episodio/problema |
| `/pacientes/[patientId]/evoluciones/nueva` | Acto clinico | completa | clinical entries | si | si | firma real futura |
| `/pacientes/[patientId]/evoluciones/desde-eventos` | Acto clinico | completa | eventos + AI-Chart | si | si | mantener como borrador revisado |
| `/pacientes/[patientId]/eventos` | Nucleo paciente | completa | clinical events | si | no | linea de tiempo completa futura |
| `/pacientes/[patientId]/problemas` | Nucleo paciente | completa | problemas activos | no | no | diagnosticos historicos/CIE-10 futuros |
| `/pacientes/[patientId]/problemas/nuevo` | Nucleo paciente | completa | problemas activos | si | no | clasificacion diagnostica futura |
| `/pacientes/[patientId]/alergias` | Seguridad clinica | completa | alergias activas | no | no | alertas criticas mas amplias |
| `/pacientes/[patientId]/alergias/nueva` | Seguridad clinica | completa | alergias activas | si | no | reacciones adversas futuras |
| `/pacientes/[patientId]/medicacion` | Nucleo paciente | completa | medicacion activa | no | no | conciliacion e historial farmacologico |
| `/pacientes/[patientId]/medicacion/nueva` | Nucleo paciente | completa | medicacion activa | si | no | receta/orden no se deriva automaticamente |
| `/pacientes/[patientId]/signos-vitales` | Resultados/observaciones | completa | signos vitales | no | no | tabla/grafico mas amplio |
| `/pacientes/[patientId]/signos-vitales/nuevo` | Resultados/observaciones | completa | signos vitales | si | no | escalas y monitoreo futuros |
| `/pacientes/[patientId]/documentos` | Documentos | preparada | UI preparada | no | no | documentos reales, adjuntos, consentimientos |
| `/pacientes/[patientId]/ia` | IA clinica | completa | AI status/sugerencias | no | no | IA como apoyo, no modulo central |
| `/pacientes/[patientId]/ai-chart` | IA clinica | completa | AI-Chart + Assistant Read | si via `ClinicalPatch` | si para SOAP | cerrar `v0.4-assistant-read` |
| `/pacientes/[patientId]/auditoria` | Seguridad/auditoria | completa | audit events | no | no | auditoria de accesos futura |
| `/consulta` | Ambulatorio | completa | App Router | no | no | mantener como indice simple |
| `/consulta/agenda` | Ambulatorio | preparada | UI preparada | no | no | agenda productiva |
| `/consulta/pacientes/[patientId]/atencion` | Ambulatorio | completa minima | encuentros + SOAP | si | no | cierre de consulta y diagnosticos finales |
| `/consulta/pacientes/[patientId]/resumen` | Ambulatorio | preparada | UI preparada | no | no | resumen ambulatorio real si aporta sobre ficha |
| `/hospitalizacion` | Hospitalizado | completa | App Router | no | no | mantener como indice simple |
| `/hospitalizacion/camas` | Hospitalizado | completa | hospitalizacion + camas | si | no | censo por servicio/equipo |
| `/hospitalizacion/camas/nueva` | Hospitalizado | completa | camas | si | no | administracion institucional futura |
| `/hospitalizacion/rondas` | Hospitalizado | completa | ingresos + camas + hojas | no | si | read-model backend si escala |
| `/hospitalizacion/pacientes/[patientId]/hoja-diaria` | Hospitalizado | completa | hojas diarias | si | si | evolucion hospitalaria por problema |
| `/hospitalizacion/pacientes/[patientId]/hoja-diaria/[sheetId]/editar` | Hospitalizado | completa | hojas diarias | si | si | firma/bloqueo legal futuro |
| `/hospitalizacion/pacientes/[patientId]/indicaciones` | Hospitalizado | completa minima | indicaciones draft | si | si | orden ejecutable y firma futura |
| `/configuracion` | Configuracion | completa | App Router | no | no | administracion clinica futura |
| `/configuracion/apariencia` | Configuracion | completa | preferencias UI | no | no | tokens visuales futuros |
| `/configuracion/ia` | Configuracion | completa | AI status | no | no | Ollama/preferencias futuras |
| `/configuracion/api` | Configuracion | completa | config API/OpenAPI | no | no | health y versionado |
| `/print/pacientes/[patientId]/ficha` | Papel | completa | record paciente | no | carta | paridad con ficha expandida |
| `/print/pacientes/[patientId]/evolucion/[entryId]` | Papel | completa | clinical entry | no | carta | firma real futura |
| `/print/pacientes/[patientId]/resumen` | Papel | completa | record paciente | no | carta | resumen IA no persistido |
| `/print/pacientes/[patientId]/receta` | Papel | preparada/bloqueada | politica receta | no | A5/bloqueado | receta valida requiere firma/folio |
| `/print/hospitalizacion/rondas` | Papel | completa | rondas lectura | no | carta | read-model si escala |
| `/print/hospitalizacion/pacientes/[patientId]/hoja-diaria/[sheetId]` | Papel | completa | hoja diaria | no | carta | firma real futura |
| `/print/hospitalizacion/pacientes/[patientId]/indicacion/[indicationId]` | Papel | completa minima | indicacion draft | no | carta | no equivale a orden firmada |

## Brechas futuras del mapa maestro

Estas superficies pertenecen a la ficha tradicional, pero no deben crearse hasta
tener contrato minimo y flujo humano verificable.

| Superficie | Modulo | Estado | Fuente esperada | Escritura | Papel | Condicion de entrada |
| --- | --- | --- | --- | --- | --- | --- |
| Antecedentes medicos/quirurgicos/familiares/sociales | Nucleo paciente | futura | eventos o entidad dedicada | si | no | contrato minimo y lectura en ficha |
| Diagnosticos historicos/CIE-10 | Nucleo paciente | futura | problemas/diagnosticos | si | no | distinguir problema activo vs diagnostico |
| Vacunas | Nucleo paciente | futura | entidad dedicada | si | no | permisos y esquema de inmunizacion |
| Dispositivos/protesis/accesos | Nucleo paciente | futura | entidad dedicada o eventos | si | no | uso clinico claro |
| Linea de tiempo completa | Nucleo paciente | futura | eventos + encuentros + documentos | no | no | puede partir leyendo fuentes existentes |
| Agenda productiva | Ambulatorio | futura | citas/appointments | si | no | modelo de cita y estados |
| Admision/preconsulta ambulatoria | Ambulatorio | futura | encuentro + observaciones | si | no | identidad, signos y pendientes |
| Receta valida | Ambulatorio/documentos | futura | receta firmada | si | si | firma, folio, actor, fecha clinica y permisos |
| Ordenes ambulatorias | Ordenes | futura | ordenes clinicas | si | si | tipos de orden y estados no ejecutables/ejecutables |
| Interconsultas/derivaciones | Ambulatorio/hospitalizado | futura | solicitudes/respuestas | si | si | pregunta clinica, prioridad, cierre |
| Ingreso medico hospitalario | Hospitalizado | futura | documento ingreso | si | si | encuentro hospitalario y firma/borrador |
| Evoluciones de enfermeria | Hospitalizado | futura | notas enfermeria | si | si | permisos enfermeria y turno |
| Kardex/administracion medicamentos | Hospitalizado | futura | indicaciones ejecutables | si | no | seguridad medicamentosa y doble chequeo |
| Balance hidrico | Hospitalizado | futura | observaciones balance | si | no | periodos, totales y auditoria |
| Resultados laboratorio UI | Resultados | futura | `lab_panels`/`lab_results` | no inicialmente | si si aplica | lectura sobria sin dashboard |
| Imagenes e informes radiologicos | Resultados | futura | informes/documentos | no inicialmente | si si aplica | sin PACS real por ahora |
| Microbiologia/anatomia patologica | Resultados | futura | resultados estructurados | no inicialmente | si si aplica | contrato antes de UI |
| Procedimientos | Hospitalizado/ambulatorio | futura | procedimientos | si | si | solicitud, consentimiento y protocolo |
| Alta y epicrisis | Hospitalizado/documentos | futura | documento egreso | si | si | borrador no firmado antes de firma real |
| Seguridad clinica ampliada | Seguridad | futura | alertas/riesgos/eventos | si | no | caidas, UPP, TEV, aislamiento, adversos |
| Administracion clinica | Admin | futura | usuarios/catalogos/plantillas | si | no | no bloquear piloto clinico actual |

## Reglas de promocion

- De `futura` a `preparada`: debe declarar en UI que no simula flujo productivo y tener E2E si queda visible.
- De `preparada` a `completa`: requiere API/PostgreSQL/permisos/auditoria/OpenAPI/UI, y papel si produce documento clinico.
- Una pantalla completa no puede depender de fallback silencioso al primer paciente, documento o registro si la ruta trae ID.
- IA puede sugerir o resumir, pero no convierte una pantalla futura en completa ni firma documentos.
