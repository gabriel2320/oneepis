import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import type {
  AIProviderStatus,
  ClinicalIntentRouteResponse,
  ClinicalIntentType,
} from "@/lib/types";
import { DEMO_MODE } from "@/lib/api/client";

import { aiStatusLabel, fallbackActionToIntent } from "./ai-chart-utils";

type ClinicalIntentCommandBarProps = {
  routerText: string;
  routedIntent: ClinicalIntentRouteResponse | null;
  aiStatus?: AIProviderStatus;
  aiStatusIsError: boolean;
  canUseAi: boolean;
  isRouting: boolean;
  isExecuting: boolean;
  hasRouteError: boolean;
  hasIntentError: boolean;
  onRouterTextChange: (value: string) => void;
  onRoute: () => void;
  onExecuteIntent: (intentType: ClinicalIntentType) => void;
};

const intentActions: { intent: ClinicalIntentType; label: string }[] = [
  { intent: "summarize_patient", label: "Resume paciente" },
  { intent: "daily_changes", label: "Que cambio" },
  { intent: "active_problems", label: "Problemas activos" },
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
  hasIntentError,
  onRouterTextChange,
  onRoute,
  onExecuteIntent,
}: ClinicalIntentCommandBarProps) {
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
          disabled={isRouting || routerText.trim().length === 0 || DEMO_MODE || !canUseAi}
          onClick={onRoute}
        >
          Ejecutar
        </Button>
      </div>
      {hasRouteError ? (
        <p className="mb-3 text-sm text-destructive">No se pudo interpretar la frase clinica.</p>
      ) : null}
      {routedIntent ? (
        <ClinicalIntentRouteResult
          routedIntent={routedIntent}
          onExecute={onExecuteIntent}
          isExecuting={isRouting || isExecuting}
        />
      ) : null}
      <GenerativeAiStatus status={aiStatus} isError={aiStatusIsError} />
      <div className="flex flex-wrap gap-2">
        {intentActions.map((action) => (
          <Button
            key={action.intent}
            type="button"
            variant="outline"
            size="sm"
            disabled={isExecuting || DEMO_MODE || !canUseAi}
            onClick={() => onExecuteIntent(action.intent)}
          >
            {action.label}
          </Button>
        ))}
      </div>
      {hasIntentError ? (
        <p className="mt-3 text-sm text-destructive">No se pudo resolver la intencion clinica.</p>
      ) : null}
    </>
  );
}

function ClinicalIntentRouteResult({
  routedIntent,
  onExecute,
  isExecuting,
}: {
  routedIntent: ClinicalIntentRouteResponse;
  onExecute: (intentType: ClinicalIntentType) => void;
  isExecuting: boolean;
}) {
  const fallbackIntents = routedIntent.fallback_options
    .map((action) => ({
      label: action.label,
      intent: fallbackActionToIntent(action),
    }))
    .filter((item): item is { label: string; intent: ClinicalIntentType } => Boolean(item.intent));
  return (
    <div className="mb-4 rounded-md border bg-muted/30 p-3">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-sm font-medium">
            {routedIntent.recognized ? "Intencion reconocida" : "Intencion no reconocida"}
          </p>
          <p className="mt-1 text-xs text-muted-foreground">
            {routedIntent.explanation} Confianza: {routedIntent.confidence}.
          </p>
        </div>
        {routedIntent.intent_type ? (
          <Button
            type="button"
            variant="outline"
            size="sm"
            disabled={isExecuting}
            onClick={() => onExecute(routedIntent.intent_type as ClinicalIntentType)}
          >
            {isExecuting ? "Ejecutando..." : "Reejecutar"}
          </Button>
        ) : null}
      </div>
      {!routedIntent.recognized ? (
        <div className="mt-3 flex flex-wrap gap-2">
          {fallbackIntents.map((action) => (
            <Button
              key={action.label}
              type="button"
              variant="outline"
              size="sm"
              disabled={isExecuting}
              onClick={() => onExecute(action.intent)}
            >
              {action.label}
            </Button>
          ))}
        </div>
      ) : null}
    </div>
  );
}

function GenerativeAiStatus({
  status,
  isError,
}: {
  status?: AIProviderStatus;
  isError: boolean;
}) {
  const label = aiStatusLabel(status, isError);
  return (
    <div className="mb-4 rounded-md border bg-background p-3 text-sm">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <p className="font-medium">Estado IA generativa</p>
          <p className="mt-1 text-xs text-muted-foreground">
            AI-Chart mantiene reglas, plantillas y auditoria aunque Ollama no este disponible.
          </p>
        </div>
        <span className="rounded-md border px-2 py-1 text-xs text-muted-foreground">{label}</span>
      </div>
      {status ? <p className="mt-2 text-xs text-muted-foreground">{status.message}</p> : null}
    </div>
  );
}
