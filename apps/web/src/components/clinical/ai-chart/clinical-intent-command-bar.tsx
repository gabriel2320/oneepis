import Link from "next/link";
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

import { aiStatusLabel, clinicalActionKey, clinicalActionTarget, fallbackActionToIntent } from "./ai-chart-utils";

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
          onExecute={onExecuteIntent}
          isExecuting={isRouting || isExecuting}
        />
      ) : null}
      {routeEvents.length > 0 || isStreamingRoutePreview || hasRoutePreviewError ? (
        <div className="mb-4 rounded-md border bg-background p-3">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <p className="text-sm font-medium">Orquestacion streaming</p>
            <span className="rounded-md border px-2 py-1 text-xs text-muted-foreground">
              FastAPI + Next Route Handler + AI SDK
            </span>
          </div>
          <AIStreamEventList events={routeEvents} />
          {isStreamingRoutePreview ? (
            <p className="mt-2 text-xs text-muted-foreground">Transmitiendo...</p>
          ) : null}
          {hasRoutePreviewError ? (
            <p className="mt-2 text-xs text-destructive">
              No se pudo generar la vista previa streaming.
            </p>
          ) : null}
        </div>
      ) : null}
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
    return "Usar la barra clinica requiere rol admin, medico o dev.";
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
    return "Usar intenciones clinicas requiere rol admin, medico o dev.";
  }
  return null;
}

function AIStreamEventList({ events }: { events: AIStreamEvent[] }) {
  if (events.length === 0) {
    return null;
  }
  return (
    <ul className="mt-2 space-y-1 text-xs text-muted-foreground">
      {events.map((event, index) => (
        <li key={`${event.type}-${index}`} className="flex flex-wrap items-center gap-1.5">
          <span className="rounded-md border px-1.5 py-0.5">{event.type}</span>
          <span>{eventLabel(event)}</span>
        </li>
      ))}
    </ul>
  );
}

function eventLabel(event: AIStreamEvent) {
  if (event.type === "status" || event.type === "warning" || event.type === "error") {
    return event.message;
  }
  if (event.type === "source") {
    return event.label;
  }
  if (event.type === "proposal") {
    return event.data.recognized
      ? `Propuesta: ${event.data.intent_type ?? event.data.mode}`
      : "Propuesta de fallback seguro";
  }
  return "Flujo completado";
}

function ClinicalIntentRouteResult({
  routedIntent,
  patientId,
  onExecute,
  isExecuting,
}: {
  routedIntent: ClinicalIntentRouteResponse;
  patientId: string;
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
      {routedIntent.suggested_actions.length > 0 ? (
        <div className="mt-3 flex flex-wrap gap-2">
          {routedIntent.suggested_actions.map((action) => {
            const target = clinicalActionTarget(patientId, action);
            if (!target) return null;
            return (
              <Button key={clinicalActionKey(action)} asChild type="button" variant="outline" size="sm">
                <Link href={target.href}>{target.label}</Link>
              </Button>
            );
          })}
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
