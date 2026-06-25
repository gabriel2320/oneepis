"use client";

import { useState } from "react";

import type {
  ClinicalIntentAction,
  ClinicalIntentResponse,
  ClinicalReviewItem,
} from "@/lib/types";

import { Change24hPanel } from "./change-24h-panel";
import {
  clinicalActionKey,
  groupRuleFindings,
} from "./ai-chart-utils";
import {
  ContextPanel,
  EvidenceMarksPanel,
  MissingDataPanel,
  ProblemsEvidencePanel,
  ProposedActionsPanel,
  SourcesPanel,
} from "./clinical-intent-support-panels";
import { ReviewItemsPanel } from "./review-items-panel";

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
