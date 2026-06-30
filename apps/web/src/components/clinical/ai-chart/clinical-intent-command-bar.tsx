import { usePathname } from "next/navigation";

import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import type {
  AIProviderStatus,
  AIStreamEvent,
  ClinicalIntentRouteResponse,
  ClinicalIntentType,
} from "@/lib/types";
import { DEMO_MODE } from "@/lib/api/client";
import { findScreenCapability, isClinicalIntentAllowed } from "@/lib/screen-capabilities";

import {
  AIStreamRoutePreview,
  ClinicalIntentRouteResult,
  GenerativeAiStatus,
} from "./clinical-intent-command-panels";

type ClinicalIntentCommandBarProps = {
  routerText: string;
  routedIntent: ClinicalIntentRouteResponse | null;
  aiStatus?: AIProviderStatus;
  aiStatusIsError: boolean;
  canUseAi: boolean;
  isRouting: boolean;
  isExecuting: boolean;
  hasRouteError: boolean;
  routeEvents: AIStreamEvent[];
  isStreamingRoutePreview: boolean;
  hasRoutePreviewError: boolean;
  hasIntentError: boolean;
  patientId: string;
  onRouterTextChange: (value: string) => void;
  onRoute: () => void;
  onExecuteIntent: (intentType: ClinicalIntentType) => void;
};

const intentActions: { intent: ClinicalIntentType; label: string }[] = [
  { intent: "summarize_patient", label: "Resume paciente" },
  { intent: "daily_changes", label: "Que cambio" },
  { intent: "active_problems", label: "Antecedentes activos" },
  { intent: "diagnostic_candidates", label: "Candidatos Dx" },
  { intent: "timeline", label: "Timeline" },
  { intent: "draft_soap", label: "Prepara SOAP" },
  { intent: "show_sources", label: "Fuentes" },
];

export function ClinicalIntentCommandBar({
  routerText,
  routedIntent,
  aiStatus,
  aiStatusIsError,
  canUseAi,
  isRouting,
  isExecuting,
  hasRouteError,
  routeEvents,
  isStreamingRoutePreview,
  hasRoutePreviewError,
  hasIntentError,
  patientId,
  onRouterTextChange,
  onRoute,
  onExecuteIntent,
}: ClinicalIntentCommandBarProps) {
  const screenCapability = findScreenCapability(usePathname());
  const routeBlockedReason = clinicalCommandBlockedReason({
    isPending: isRouting,
    hasText: routerText.trim().length > 0,
    canUseAi,
  });
  const intentBlockedReason = clinicalIntentBlockedReason({
    isPending: isExecuting,
    canUseAi,
  });
  return (
    <>
      <div className="mb-4 grid gap-2 md:grid-cols-[minmax(0,1fr)_auto]">
        <Textarea
          className="min-h-16"
          placeholder="Ej: prepara evolucion de hoy, que cambio desde ayer, muestra fuentes"
          value={routerText}
          onChange={(event) => onRouterTextChange(event.target.value)}
        />
        <Button
          type="button"
          variant="secondary"
          disabled={Boolean(routeBlockedReason)}
          onClick={onRoute}
        >
          Ejecutar
        </Button>
      </div>
      {routeBlockedReason && !isRouting ? (
        <p className="mb-3 text-xs text-muted-foreground">{routeBlockedReason}</p>
      ) : null}
      {hasRouteError ? (
        <p className="mb-3 text-sm text-destructive">No se pudo interpretar la frase clinica.</p>
      ) : null}
      {routedIntent ? (
        <ClinicalIntentRouteResult
          routedIntent={routedIntent}
          patientId={patientId}
          screenCapability={screenCapability}
          onExecute={onExecuteIntent}
          isExecuting={isRouting || isExecuting}
        />
      ) : null}
      <AIStreamRoutePreview
        events={routeEvents}
        isStreaming={isStreamingRoutePreview}
        hasError={hasRoutePreviewError}
      />
      <GenerativeAiStatus status={aiStatus} isError={aiStatusIsError} />
      <div className="flex flex-wrap gap-2">
        {intentActions.map((action) => (
          <Button
            key={action.intent}
            type="button"
            variant="outline"
            size="sm"
            disabled={
              Boolean(intentBlockedReason) ||
              !isClinicalIntentAllowed(action.intent, screenCapability)
            }
            onClick={() => onExecuteIntent(action.intent)}
          >
            {action.label}
          </Button>
        ))}
      </div>
      {intentBlockedReason && !isExecuting ? (
        <p className="mt-3 text-xs text-muted-foreground">{intentBlockedReason}</p>
      ) : null}
      {hasIntentError ? (
        <p className="mt-3 text-sm text-destructive">No se pudo resolver la intencion clinica.</p>
      ) : null}
    </>
  );
}

function clinicalCommandBlockedReason({
  isPending,
  hasText,
  canUseAi,
}: {
  isPending: boolean;
  hasText: boolean;
  canUseAi: boolean;
}) {
  if (isPending) {
    return "Interpretando frase clinica.";
  }
  if (DEMO_MODE) {
    return "Modo demo: no se ejecutan intenciones reales.";
  }
  if (!canUseAi) {
    return "Usar la barra clinica requiere un perfil autorizado.";
  }
  if (!hasText) {
    return "Escribe una instruccion clinica para ejecutar.";
  }
  return null;
}

function clinicalIntentBlockedReason({
  isPending,
  canUseAi,
}: {
  isPending: boolean;
  canUseAi: boolean;
}) {
  if (isPending) {
    return "Ejecutando intencion clinica.";
  }
  if (DEMO_MODE) {
    return "Modo demo: no se ejecutan intenciones reales.";
  }
  if (!canUseAi) {
    return "Usar intenciones clinicas requiere un perfil autorizado.";
  }
  return null;
}
