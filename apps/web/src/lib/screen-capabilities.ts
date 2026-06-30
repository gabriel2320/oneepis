import type { ClinicalIntentType } from "@/lib/types";
import screenCapabilityRows from "./screen-capabilities.registry.json";

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

type ScreenAiProfile = keyof typeof AI;

type ScreenCapabilityRow = Omit<ScreenCapability, "aiCapabilities"> & {
  aiProfile: ScreenAiProfile;
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

export const screenCapabilities: ScreenCapability[] = (screenCapabilityRows as ScreenCapabilityRow[])
  .map((row) => capability(row));

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

function capability(row: ScreenCapabilityRow): ScreenCapability {
  return {
    routePattern: row.routePattern,
    module: row.module,
    clinicalMoment: row.clinicalMoment,
    status: row.status,
    truthSource: row.truthSource,
    writePolicy: row.writePolicy,
    permissionPolicy: row.permissionPolicy,
    auditPolicy: row.auditPolicy,
    paperPolicy: row.paperPolicy,
    aiCapabilities: AI[row.aiProfile],
    futureComplexity: row.futureComplexity,
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
  diagnostic_candidates: "read",
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
