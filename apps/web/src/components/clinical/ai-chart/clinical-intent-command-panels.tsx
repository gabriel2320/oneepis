import Link from "next/link";

import { Button } from "@/components/ui/button";
import type {
  AIProviderStatus,
  AIStreamEvent,
  ClinicalIntentRouteResponse,
  ClinicalIntentType,
} from "@/lib/types";
import { isClinicalIntentAllowed, type ScreenCapability } from "@/lib/screen-capabilities";

import {
  aiStatusLabel,
  clinicalActionKey,
  clinicalActionTarget,
  fallbackActionToIntent,
} from "./ai-chart-utils";

export function ClinicalIntentRouteResult({
  routedIntent,
  patientId,
  screenCapability,
  onExecute,
  isExecuting,
}: {
  routedIntent: ClinicalIntentRouteResponse;
  patientId: string;
  screenCapability: ScreenCapability | null;
  onExecute: (intentType: ClinicalIntentType) => void;
  isExecuting: boolean;
}) {
  const routedIntentType = routedIntent.intent_type as ClinicalIntentType | null;
  const isRoutedIntentAllowed =
    !routedIntentType || isClinicalIntentAllowed(routedIntentType, screenCapability);
  const fallbackIntents = routedIntent.fallback_options
    .map((action) => ({
      label: action.label,
      intent: fallbackActionToIntent(action),
    }))
    .filter((item): item is { label: string; intent: ClinicalIntentType } => {
      if (!item.intent) return false;
      return isClinicalIntentAllowed(item.intent, screenCapability);
    });
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
        {routedIntentType ? (
          <Button
            type="button"
            variant="outline"
            size="sm"
            disabled={isExecuting || !isRoutedIntentAllowed}
            onClick={() => onExecute(routedIntentType)}
          >
            {isExecuting ? "Ejecutando..." : "Reejecutar"}
          </Button>
        ) : null}
      </div>
      {routedIntentType && !isRoutedIntentAllowed ? (
        <p className="mt-3 text-xs text-muted-foreground">
          Esta pantalla no permite ejecutar esa intencion clinica.
        </p>
      ) : null}
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

export function AIStreamRoutePreview({
  events,
  isStreaming,
  hasError,
}: {
  events: AIStreamEvent[];
  isStreaming: boolean;
  hasError: boolean;
}) {
  if (events.length === 0 && !isStreaming && !hasError) {
    return null;
  }
  return (
    <div className="mb-4 rounded-md border bg-background p-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-sm font-medium">Orquestacion streaming</p>
        <span className="rounded-md border px-2 py-1 text-xs text-muted-foreground">
          FastAPI + Next Route Handler + AI SDK
        </span>
      </div>
      <AIStreamEventList events={events} />
      {isStreaming ? (
        <p className="mt-2 text-xs text-muted-foreground">Transmitiendo...</p>
      ) : null}
      {hasError ? (
        <p className="mt-2 text-xs text-destructive">
          No se pudo generar la vista previa streaming.
        </p>
      ) : null}
    </div>
  );
}

export function GenerativeAiStatus({
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
            AI-Chart mantiene reglas, plantillas y auditoria aunque la IA local no este disponible.
          </p>
        </div>
        <span className="rounded-md border px-2 py-1 text-xs text-muted-foreground">{label}</span>
      </div>
      {status ? <p className="mt-2 text-xs text-muted-foreground">{status.message}</p> : null}
    </div>
  );
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
