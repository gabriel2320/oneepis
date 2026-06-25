"use client";

import Link from "next/link";

import { Button } from "@/components/ui/button";
import type { ClinicalIntentAction, ClinicalIntentResponse } from "@/lib/types";

import { clinicalActionKey, clinicalActionTarget } from "./ai-chart-utils";

export function ProblemsEvidencePanel({ intent }: { intent: ClinicalIntentResponse }) {
  return (
    <div className="rounded-md border p-3">
      <p className="text-sm font-medium">Problemas y evidencia</p>
      <div className="mt-2 space-y-3">
        {intent.problem_contexts.length > 0 ? (
          intent.problem_contexts.map((context) => (
            <div key={`${context.status}-${context.problem_id ?? context.title}`}>
              <p className="text-xs font-medium text-muted-foreground">
                {context.title} · {context.status}
              </p>
              <ul className="mt-1 space-y-1 text-xs text-muted-foreground">
                {context.explanations.map((item) => (
                  <li key={item}>Explicacion: {item}</li>
                ))}
                {context.evidence.length > 0 ? (
                  context.evidence.map((mark) => (
                    <li key={`${mark.status}-${mark.source_id ?? mark.label}`}>
                      <div className="space-y-0.5">
                        <div className="flex flex-wrap items-center gap-1.5">
                          <span className="rounded-md border px-1.5 py-0.5">
                            {mark.status}
                          </span>
                          <span>{mark.label}</span>
                        </div>
                        <p>Razon: {mark.detail}</p>
                        {mark.source_id ? (
                          <p>Fuente: registro {shortSourceId(mark.source_id)}</p>
                        ) : null}
                      </div>
                    </li>
                  ))
                ) : (
                  <li>Sin evidencia reciente asociada</li>
                )}
                {context.pending.map((item) => (
                  <li key={item}>
                    <span className="rounded-md border px-1.5 py-0.5">pendiente</span>{" "}
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          ))
        ) : (
          <p className="text-xs text-muted-foreground">Sin problemas estructurados.</p>
        )}
      </div>
    </div>
  );
}

export function ContextPanel({ intent }: { intent: ClinicalIntentResponse }) {
  return (
    <div className="rounded-md border p-3">
      <p className="text-sm font-medium">Contexto construido</p>
      <div className="mt-2 space-y-2">
        {intent.context_sections.map((section) => (
          <div key={section.title}>
            <p className="text-xs font-medium text-muted-foreground">{section.title}</p>
            <ul className="mt-1 space-y-1 text-xs text-muted-foreground">
              {section.items.length > 0 ? (
                section.items.map((item) => <li key={item}>{item}</li>)
              ) : (
                <li>Sin registros</li>
              )}
            </ul>
          </div>
        ))}
      </div>
    </div>
  );
}

export function EvidenceMarksPanel({ intent }: { intent: ClinicalIntentResponse }) {
  return (
    <div className="rounded-md border p-3">
      <p className="text-sm font-medium">Marcas de evidencia</p>
      <ul className="mt-2 space-y-1 text-xs text-muted-foreground">
        {intent.evidence_marks.length > 0 ? (
          intent.evidence_marks.map((mark) => (
            <li key={`${mark.status}-${mark.label}`}>
              {mark.status}: {mark.label} - {mark.detail}
            </li>
          ))
        ) : (
          <li>Sin marcas</li>
        )}
      </ul>
    </div>
  );
}

export function SourcesPanel({ intent }: { intent: ClinicalIntentResponse }) {
  return (
    <div className="rounded-md border p-3">
      <p className="text-sm font-medium">Fuentes</p>
      <ul className="mt-2 space-y-1 text-xs text-muted-foreground">
        {intent.sources.length > 0 ? (
          intent.sources.map((source) => (
            <li key={`${source.source_type}-${source.source_id ?? source.label}`}>
              {source.source_type}: {source.label}
            </li>
          ))
        ) : (
          <li>Sin fuentes</li>
        )}
      </ul>
    </div>
  );
}

export function MissingDataPanel({ intent }: { intent: ClinicalIntentResponse }) {
  return (
    <div className="rounded-md border p-3">
      <p className="text-sm font-medium">Datos faltantes</p>
      <ul className="mt-2 space-y-1 text-xs text-muted-foreground">
        {intent.missing_data.length > 0 ? (
          intent.missing_data.map((item) => <li key={item}>{item}</li>)
        ) : (
          <li>Sin faltantes criticos</li>
        )}
      </ul>
    </div>
  );
}

export function ProposedActionsPanel({
  intent,
  patientId,
  reviewedActionIds,
  isDecidingAction,
  actionDecisionMessage,
  onDecideAction,
}: {
  intent: ClinicalIntentResponse;
  patientId: string;
  reviewedActionIds: string[];
  isDecidingAction: boolean;
  actionDecisionMessage: string | null;
  onDecideAction: (action: ClinicalIntentAction) => void;
}) {
  return (
    <div className="rounded-md border p-3">
      <p className="text-sm font-medium">Acciones propuestas</p>
      <ul className="mt-2 space-y-2 text-xs text-muted-foreground">
        {intent.proposed_actions.map((action) => {
          const actionKey = clinicalActionKey(action);
          const target = clinicalActionTarget(patientId, action);
          const isReviewed = reviewedActionIds.includes(actionKey);
          return (
            <li key={actionKey} className="rounded-md border bg-background p-2">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span className="font-medium text-foreground">{action.label}</span>
                <span className="rounded-md border px-1.5 py-0.5">
                  {action.requires_confirmation ? "confirmable" : "lectura"}
                </span>
              </div>
              {action.description ? <p className="mt-1">{action.description}</p> : null}
              <p className="mt-1">Tipo: {action.action_type}</p>
              <div className="mt-2 flex flex-wrap gap-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  disabled={isDecidingAction || isReviewed}
                  onClick={() => onDecideAction(action)}
                >
                  {isReviewed ? "Propuesta revisada" : action.confirmation_label ?? "Revisar"}
                </Button>
                {target ? (
                  <Button asChild type="button" variant="outline" size="sm">
                    <Link href={target.href}>{target.label}</Link>
                  </Button>
                ) : null}
              </div>
            </li>
          );
        })}
      </ul>
      {actionDecisionMessage ? (
        <p className="mt-3 text-xs text-muted-foreground">{actionDecisionMessage}</p>
      ) : null}
    </div>
  );
}

function shortSourceId(sourceId: string) {
  return sourceId.slice(0, 8);
}
