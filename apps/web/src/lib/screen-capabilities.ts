import type { ClinicalIntentType } from "@/lib/types";

export type ScreenStatus =
  | "completa"
  | "completa/en expansion gobernada"
  | "preparada"
  | "bloqueada"
  | "futura";
export type ScreenAiAction =
  | "read"
  | "summarize"
  | "search"
  | "chart"
  | "validate"
  | "draft"
  | "propose_patch";

export type ScreenAiCapability = {
  actions: ScreenAiAction[];
  sourcePolicy: string;
  limitations: string;
  missingDataPolicy: string;
  humanAction: string;
  ollamaAllowed: boolean;
  clinicalPatchAllowed: boolean;
};

export type ScreenCapability = {
  routePattern: string;
  module: string;
  clinicalMoment: string;
  status: ScreenStatus;
  truthSource: string;
  writePolicy: string;
  permissionPolicy: string;
  auditPolicy: string;
  paperPolicy: string;
  aiCapabilities: ScreenAiCapability[];
  futureComplexity: string;
};

const AI = {
  none: [],
  read: [ai(["read"], "fuentes clinicas existentes", "no diagnostica ni prescribe")],
  summary: [ai(["read", "summarize"], "snapshot y fuentes longitudinales", "resumen revisable")],
  chart: [ai(["read", "search", "chart"], "signos, eventos y resultados", "solo tendencias explicables")],
  validate: [ai(["read", "validate"], "vademecum curado y reglas locales", "sin receta valida")],
  draft: [ai(["read", "summarize", "draft"], "eventos/evoluciones seleccionadas", "borrador humano", true)],
  patch: [
    ai(
      ["read", "summarize", "search", "chart", "draft", "propose_patch"],
      "Assistant Read, eventos y ficha",
      "patch confirmado por humano",
      true,
      true,
    ),
  ],
} satisfies Record<string, ScreenAiCapability[]>;

export const screenCapabilities: ScreenCapability[] = [
  capability("/", "Acceso/configuracion", "seguimiento", "completa", "redirect App Router", "none", "publico/control UI", "none", "none", AI.none, "entrada a pacientes"),
  capability("/login", "Acceso/configuracion", "seguimiento", "completa", "auth local", "none", "publico/control UI", "none", "none", AI.none, "seleccion institucion/rol futura"),
  capability("/configuracion", "Acceso/configuracion", "seguimiento", "completa", "App Router", "none", "sesion local", "none", "none", AI.read, "administracion clinica futura"),
  capability("/configuracion/apariencia", "Acceso/configuracion", "seguimiento", "completa", "preferencias UI", "none", "sesion local", "none", "none", AI.none, "tokens visuales futuros"),
  capability("/configuracion/api", "Acceso/configuracion", "seguimiento", "completa", "config API/OpenAPI", "none", "sesion local", "none", "none", AI.none, "health y versionado"),
  capability("/configuracion/ia", "Acceso/configuracion", "seguimiento", "completa", "AI status", "none", "sesion local", "none", "none", AI.read, "preferencias Ollama/local futuras"),
  capability("/consulta", "Ambulatorio", "seguimiento", "completa", "App Router", "none", "lectura paciente", "none", "none", AI.none, "indice simple"),
  capability("/consulta/agenda", "Ambulatorio", "episodio", "preparada", "UI preparada", "none", "lectura paciente", "none", "none", AI.none, "agenda productiva"),
  capability("/consulta/pacientes/[patientId]/atencion", "Ambulatorio", "acto clinico", "completa", "encuentros + SOAP", "clinical_write", "medico/admin/dev", "writes", "none", AI.draft, "cierre de consulta"),
  capability("/consulta/pacientes/[patientId]/resumen", "Ambulatorio", "seguimiento", "preparada", "UI preparada", "none", "lectura paciente", "none", "none", AI.summary, "resumen ambulatorio real"),
  capability("/hospitalizacion", "Hospitalizacion", "seguimiento", "completa", "App Router", "none", "lectura paciente", "none", "none", AI.none, "indice simple"),
  capability("/hospitalizacion/camas", "Hospitalizacion", "episodio", "completa", "hospitalizacion + camas", "clinical_write", "medico/admin/dev", "writes", "none", AI.none, "censo por servicio/equipo"),
  capability("/hospitalizacion/camas/nueva", "Hospitalizacion", "episodio", "completa", "camas", "clinical_write", "medico/admin/dev", "writes", "none", AI.none, "administracion institucional futura"),
  capability("/hospitalizacion/pacientes/[patientId]/hoja-diaria", "Hospitalizacion", "acto clinico", "completa", "hojas diarias", "clinical_write", "medico/admin/dev", "writes", "carta", AI.summary, "evolucion por problema"),
  capability("/hospitalizacion/pacientes/[patientId]/hoja-diaria/[sheetId]/editar", "Hospitalizacion", "acto clinico", "completa", "hojas diarias", "clinical_write", "medico/admin/dev", "writes", "carta", AI.none, "firma/bloqueo legal futuro"),
  capability("/hospitalizacion/pacientes/[patientId]/indicaciones", "Hospitalizacion", "acto clinico", "completa", "indicaciones draft", "draft_only", "medico/admin/dev", "writes", "carta", AI.summary, "orden ejecutable y firma futura"),
  capability("/hospitalizacion/rondas", "Hospitalizacion", "seguimiento", "completa", "ingresos + camas + hojas", "none", "lectura paciente", "none", "carta", AI.summary, "read-model backend si escala"),
  capability("/pacientes", "Nucleo paciente", "paciente", "completa", "API pacientes / demo", "none", "lectura paciente", "none", "none", AI.none, "buscador universal avanzado"),
  capability("/pacientes/nuevo", "Nucleo paciente", "paciente", "completa", "API pacientes", "patient_write", "escritura paciente", "writes", "none", AI.none, "identidad administrativa"),
  capability("/pacientes/[patientId]", "Nucleo paciente", "paciente", "completa", "redirect App Router", "none", "lectura paciente", "none", "none", AI.none, "entrada a ficha"),
  capability("/pacientes/[patientId]/ai-chart", "IA clinica", "acto clinico", "completa", "AI-Chart + Assistant Read", "clinical_patch", "medico/admin/dev + permiso IA", "patch_writes", "SOAP carta", AI.patch, "cerrar v0.4"),
  capability("/pacientes/[patientId]/alergias", "Seguridad/auditoria", "paciente", "completa", "alergias activas", "none", "lectura paciente", "none", "none", AI.read, "alertas criticas mas amplias"),
  capability("/pacientes/[patientId]/alergias/nueva", "Seguridad/auditoria", "acto clinico", "completa", "alergias activas", "clinical_write", "medico/admin/dev", "writes", "none", AI.none, "reacciones adversas futuras"),
  capability("/pacientes/[patientId]/auditoria", "Seguridad/auditoria", "seguimiento", "completa", "audit events", "none", "lectura auditoria", "none", "none", AI.none, "auditoria de accesos futura"),
  capability("/pacientes/[patientId]/documentos", "Documentos/papel", "documento", "preparada", "UI preparada", "none", "lectura paciente", "none", "none", AI.none, "documentos reales y adjuntos"),
  capability("/pacientes/[patientId]/encuentros", "Episodios", "episodio", "completa", "API encuentros", "none", "lectura paciente", "none", "none", AI.read, "episodio mas explicito"),
  capability("/pacientes/[patientId]/encuentros/nuevo", "Episodios", "episodio", "completa", "API encuentros", "clinical_write", "medico/admin/dev", "writes", "none", AI.none, "admision/preconsulta futura"),
  capability("/pacientes/[patientId]/estado", "Nucleo paciente", "seguimiento", "completa", "API paciente", "clinical_write", "medico/admin/dev", "writes", "none", AI.none, "estados clinicos mas finos"),
  capability("/pacientes/[patientId]/eventos", "Nucleo paciente", "acto clinico", "completa", "clinical events", "clinical_write", "escritura clinica", "writes", "none", AI.read, "linea de tiempo completa"),
  capability("/pacientes/[patientId]/evoluciones", "Episodios", "acto clinico", "completa", "clinical entries", "none", "lectura paciente", "none", "carta", AI.read, "filtros por episodio/problema"),
  capability("/pacientes/[patientId]/evoluciones/desde-eventos", "Episodios", "acto clinico", "completa", "eventos + AI-Chart", "clinical_write", "medico/admin/dev + permiso IA", "writes", "carta", AI.draft, "borrador revisado"),
  capability("/pacientes/[patientId]/evoluciones/nueva", "Episodios", "acto clinico", "completa", "clinical entries", "clinical_write", "medico/admin/dev", "writes", "carta", AI.draft, "firma real futura"),
  capability("/pacientes/[patientId]/ficha", "Nucleo paciente", "paciente", "completa", "record paciente", "none", "lectura paciente", "none", "carta", AI.summary, "antecedentes y resultados"),
  capability("/pacientes/[patientId]/ia", "IA clinica", "seguimiento", "completa", "AI status/sugerencias", "none", "lectura paciente + permiso IA", "none", "none", AI.summary, "apoyo no central"),
  capability("/pacientes/[patientId]/medicacion", "Medicacion/vademecum", "paciente", "completa/en expansion gobernada", "medicacion activa + vademecum", "none", "lectura paciente", "none", "none", AI.validate, "interacciones y receta futura"),
  capability("/pacientes/[patientId]/medicacion/nueva", "Medicacion/vademecum", "acto clinico", "completa/en expansion gobernada", "medicacion + validacion dosis", "clinical_write", "escritura clinica", "writes", "none", AI.validate, "sin receta/orden automatica"),
  capability("/pacientes/[patientId]/problemas", "Nucleo paciente", "paciente", "completa", "problemas activos", "none", "lectura paciente", "none", "none", AI.read, "diagnosticos historicos"),
  capability("/pacientes/[patientId]/problemas/nuevo", "Nucleo paciente", "acto clinico", "completa", "problemas activos", "clinical_write", "medico/admin/dev", "writes", "none", AI.none, "clasificacion diagnostica"),
  capability("/pacientes/[patientId]/signos-vitales", "Ordenes/resultados", "seguimiento", "completa", "signos vitales", "none", "lectura paciente", "none", "none", AI.chart, "tabla/grafico amplio"),
  capability("/pacientes/[patientId]/signos-vitales/nuevo", "Ordenes/resultados", "acto clinico", "completa", "signos vitales", "clinical_write", "enfermeria/medico/admin/dev", "writes", "none", AI.none, "escalas y monitoreo"),
  capability("/print/hospitalizacion/pacientes/[patientId]/hoja-diaria/[sheetId]", "Documentos/papel", "documento", "completa", "hoja diaria", "none", "lectura paciente", "none", "carta", AI.none, "firma real futura"),
  capability("/print/hospitalizacion/pacientes/[patientId]/indicacion/[indicationId]", "Documentos/papel", "documento", "completa", "indicacion draft", "none", "lectura paciente", "none", "carta", AI.none, "no equivale a orden firmada"),
  capability("/print/hospitalizacion/rondas", "Documentos/papel", "documento", "completa", "rondas lectura", "none", "lectura paciente", "none", "carta", AI.none, "read-model si escala"),
  capability("/print/pacientes/[patientId]/evolucion/[entryId]", "Documentos/papel", "documento", "completa", "clinical entry", "none", "lectura paciente", "none", "carta", AI.none, "firma real futura"),
  capability("/print/pacientes/[patientId]/ficha", "Documentos/papel", "documento", "completa", "record paciente", "none", "lectura paciente", "none", "carta", AI.none, "paridad con ficha expandida"),
  capability("/print/pacientes/[patientId]/receta", "Documentos/papel", "documento", "bloqueada", "politica receta", "none", "lectura paciente", "none", "bloqueado", AI.none, "receta valida requiere firma/folio"),
  capability("/print/pacientes/[patientId]/resumen", "Documentos/papel", "documento", "completa", "record paciente", "none", "lectura paciente", "none", "carta", AI.summary, "resumen IA no persistido"),
];

export function findScreenCapability(pathname: string | null | undefined) {
  if (!pathname) return null;
  const cleanPath = pathname.split("?")[0].replace(/\/$/, "") || "/";
  return sortedCapabilities.find((capability) =>
    routePatternToRegExp(capability.routePattern).test(cleanPath),
  ) ?? null;
}

export function isClinicalIntentAllowed(
  intentType: ClinicalIntentType,
  capability: ScreenCapability | null | undefined,
) {
  if (!capability) return false;
  const requiredAction = intentActionMap[intentType];
  return capability.aiCapabilities.some((item) => item.actions.includes(requiredAction));
}

function capability(
  routePattern: string,
  module: string,
  clinicalMoment: string,
  status: ScreenStatus,
  truthSource: string,
  writePolicy: string,
  permissionPolicy: string,
  auditPolicy: string,
  paperPolicy: string,
  aiCapabilities: ScreenAiCapability[],
  futureComplexity: string,
): ScreenCapability {
  return {
    routePattern,
    module,
    clinicalMoment,
    status,
    truthSource,
    writePolicy,
    permissionPolicy,
    auditPolicy,
    paperPolicy,
    aiCapabilities,
    futureComplexity,
  };
}

function ai(
  actions: ScreenAiAction[],
  sourcePolicy: string,
  limitations: string,
  ollamaAllowed = false,
  clinicalPatchAllowed = false,
): ScreenAiCapability {
  return {
    actions,
    sourcePolicy,
    limitations,
    missingDataPolicy: "mostrar faltantes y limites cuando apliquen",
    humanAction: clinicalPatchAllowed ? "confirmar patch humano" : "revision humana",
    ollamaAllowed,
    clinicalPatchAllowed,
  };
}

const intentActionMap: Record<ClinicalIntentType, ScreenAiAction> = {
  summarize_patient: "summarize",
  daily_changes: "summarize",
  active_problems: "read",
  timeline: "search",
  draft_soap: "draft",
  show_sources: "read",
};

const sortedCapabilities = [...screenCapabilities].sort((left, right) => {
  const dynamicDelta = dynamicSegmentCount(left.routePattern) - dynamicSegmentCount(right.routePattern);
  if (dynamicDelta !== 0) return dynamicDelta;
  return right.routePattern.length - left.routePattern.length;
});

const regexCache = new Map<string, RegExp>();

function routePatternToRegExp(routePattern: string) {
  const cached = regexCache.get(routePattern);
  if (cached) return cached;
  const escaped = routePattern
    .replace(/[.*+?^${}()|[\]\\]/g, "\\$&")
    .replace(/\\\[.+?\\\]/g, "[^/]+");
  const regex = new RegExp(`^${escaped}$`);
  regexCache.set(routePattern, regex);
  return regex;
}

function dynamicSegmentCount(routePattern: string) {
  return (routePattern.match(/\[[^\]]+\]/g) ?? []).length;
}
