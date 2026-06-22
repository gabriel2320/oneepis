"use client";

import Link from "next/link";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import type {
  ClinicalIntentAction,
  ClinicalIntentResponse,
  ClinicalReviewItem,
} from "@/lib/types";

import { Change24hPanel } from "./change-24h-panel";
import { ReviewItemsPanel } from "./review-items-panel";
import {
  clinicalActionKey,
  clinicalActionTarget,
  groupRuleFindings,
} from "./ai-chart-utils";

type ClinicalIntentResultPanelProps = {
  intent: ClinicalIntentResponse;
  patientId: string;
  isDecidingReviewItem: boolean;
  reviewDecisionMessage: string | null;
  isDecidingAction: boolean;
  actionDecisionMessage: string | null;
  onDecideReviewItem: (item: ClinicalReviewItem, decision: "accepted" | "rejected") => void;
  onDecideAction: (action: ClinicalIntentAction) => void;
};

export function ClinicalIntentResultPanel({
  intent,
  patientId,
  isDecidingReviewItem,
  reviewDecisionMessage,
  isDecidingAction,
  actionDecisionMessage,
  onDecideReviewItem,
  onDecideAction,
}: ClinicalIntentResultPanelProps) {
  const ruleGroups = groupRuleFindings(intent.change_set?.rule_findings ?? [], intent);
  const pendingReviewItems = intent.review_items.filter((item) => item.decision_status === "pending");
  const decidedReviewItems = intent.review_items.filter((item) => item.decision_status !== "pending");
  const [reviewedActionIds, setReviewedActionIds] = useState<string[]>([]);
  return (
    <div className="mt-4 grid gap-4 xl:grid-cols-[minmax(0,1fr)_360px]">
      <div className="rounded-md border bg-muted/30 p-3">
        <div className="mb-2 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
          <span>Modo: {intent.mode}</span>
          <span>Certeza: {intent.certainty}</span>
          {intent.requires_human_confirmation ? <span>Requiere confirmacion humana</span> : null}
        </div>
        <pre className="whitespace-pre-wrap text-sm">{intent.clinical_answer}</pre>
        <Change24hPanel groups={ruleGroups} />
        {intent.warnings.length > 0 ? (
          <div className="mt-3 rounded-md border bg-background p-2 text-xs text-muted-foreground">
            {intent.warnings.map((warning) => (
              <p key={warning}>{warning}</p>
            ))}
          </div>
        ) : null}
      </div>
      <div className="space-y-3">
        <div className="rounded-md border p-3">
          <p className="text-sm font-medium">Comparacion</p>
          <div className="mt-2 space-y-2 text-xs text-muted-foreground">
            <p>Base: {intent.change_set?.baseline ?? "Sin evolucion previa"}</p>
            <div>
              <p className="font-medium">Eventos nuevos</p>
              <ul className="mt-1 space-y-1">
                {intent.change_set?.new_items.length ? (
                  intent.change_set.new_items.map((item) => <li key={item}>{item}</li>)
                ) : (
                  <li>Sin eventos nuevos</li>
                )}
              </ul>
            </div>
            <div>
              <p className="font-medium">Reglas 24 h</p>
              {ruleGroups.length > 0 ? (
                <div className="mt-1 space-y-2">
                  {ruleGroups.map((group) => (
                    <div key={group.label}>
                      <p className="text-[11px] font-medium uppercase text-muted-foreground">
                        {group.label}
                      </p>
                      <ul className="mt-1 space-y-2">
                        {group.items.map((item) => (
                          <li key={item.text}>
                            <div className="flex flex-wrap items-center gap-1.5">
                              <span className="rounded-md border px-1.5 py-0.5">
                                {item.status}
                              </span>
                              <span>{item.text}</span>
                            </div>
                            <p className="mt-0.5 text-[11px] text-muted-foreground">
                              Fuente: {item.source}
                            </p>
                          </li>
                        ))}
                      </ul>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="mt-1">Sin cambios determinísticos relevantes</p>
              )}
            </div>
          </div>
        </div>
        <ProblemsEvidencePanel intent={intent} />
        <ReviewItemsPanel
          pendingReviewItems={pendingReviewItems}
          decidedReviewItems={decidedReviewItems}
          isDecidingReviewItem={isDecidingReviewItem}
          reviewDecisionMessage={reviewDecisionMessage}
          onDecideReviewItem={onDecideReviewItem}
        />
        <ContextPanel intent={intent} />
        <EvidenceMarksPanel intent={intent} />
        <SourcesPanel intent={intent} />
        <MissingDataPanel intent={intent} />
        <ProposedActionsPanel
          intent={intent}
          patientId={patientId}
          reviewedActionIds={reviewedActionIds}
          isDecidingAction={isDecidingAction}
          actionDecisionMessage={actionDecisionMessage}
          onDecideAction={(action) => {
            onDecideAction(action);
            setReviewedActionIds((current) => [...current, clinicalActionKey(action)]);
          }}
        />
      </div>
    </div>
  );
}

function ProblemsEvidencePanel({ intent }: { intent: ClinicalIntentResponse }) {
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
                {context.evidence.length > 0 ? (
                  context.evidence.map((mark) => <li key={`${mark.status}-${mark.label}`}>{mark.label}</li>)
                ) : (
                  <li>Sin evidencia reciente asociada</li>
                )}
                {context.pending.map((item) => (
                  <li key={item}>{item}</li>
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

function ContextPanel({ intent }: { intent: ClinicalIntentResponse }) {
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

function EvidenceMarksPanel({ intent }: { intent: ClinicalIntentResponse }) {
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

function SourcesPanel({ intent }: { intent: ClinicalIntentResponse }) {
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

function MissingDataPanel({ intent }: { intent: ClinicalIntentResponse }) {
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

function ProposedActionsPanel({
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
