import { Button } from "@/components/ui/button";
import type { ClinicalReviewItem } from "@/lib/types";

import { formatDate } from "./ai-chart-utils";

type ReviewItemsPanelProps = {
  pendingReviewItems: ClinicalReviewItem[];
  decidedReviewItems: ClinicalReviewItem[];
  isDecidingReviewItem: boolean;
  reviewDecisionMessage: string | null;
  onDecideReviewItem: (item: ClinicalReviewItem, decision: "accepted" | "rejected") => void;
};

export function ReviewItemsPanel({
  pendingReviewItems,
  decidedReviewItems,
  isDecidingReviewItem,
  reviewDecisionMessage,
  onDecideReviewItem,
}: ReviewItemsPanelProps) {
  return (
    <div className="rounded-md border p-3">
      <p className="text-sm font-medium">Propuestas de revision</p>
      <ul className="mt-2 space-y-2 text-xs text-muted-foreground">
        {pendingReviewItems.length > 0 ? (
          pendingReviewItems.map((item) => (
            <ReviewItemRow
              key={`${item.item_type}-${item.source_id ?? item.label}`}
              item={item}
              isDecidingReviewItem={isDecidingReviewItem}
              onDecideReviewItem={onDecideReviewItem}
            />
          ))
        ) : (
          <li>Sin propuestas pendientes</li>
        )}
      </ul>
      {decidedReviewItems.length > 0 ? (
        <details className="mt-3 text-xs text-muted-foreground">
          <summary className="cursor-pointer font-medium">
            Historial de decisiones ({decidedReviewItems.length})
          </summary>
          <ul className="mt-2 space-y-2">
            {decidedReviewItems.map((item) => (
              <li key={`${item.decision_status}-${item.item_type}-${item.source_id ?? item.label}`}>
                <div className="flex flex-wrap items-center gap-1.5">
                  <span className="font-medium">{item.label}</span>
                  <span className="rounded-md border px-1.5 py-0.5">
                    {item.decision_status}
                  </span>
                </div>
                <span className="block">{item.detail}</span>
                <span className="block">Auditoria: {formatReviewDecisionAudit(item)}</span>
              </li>
            ))}
          </ul>
        </details>
      ) : null}
      {reviewDecisionMessage ? (
        <p className="mt-3 text-xs text-muted-foreground">{reviewDecisionMessage}</p>
      ) : null}
    </div>
  );
}

function ReviewItemRow({
  item,
  isDecidingReviewItem,
  onDecideReviewItem,
}: {
  item: ClinicalReviewItem;
  isDecidingReviewItem: boolean;
  onDecideReviewItem: (item: ClinicalReviewItem, decision: "accepted" | "rejected") => void;
}) {
  return (
    <li>
      <span className="font-medium">{item.label}</span>
      <span className="ml-2 rounded-md border px-1.5 py-0.5">{item.decision_status}</span>
      <span className="block">{item.detail}</span>
      <span className="block">Accion sugerida: {item.suggested_action}</span>
      <span className="mt-2 flex gap-2">
        <Button
          type="button"
          size="sm"
          variant="outline"
          disabled={isDecidingReviewItem}
          onClick={() => onDecideReviewItem(item, "accepted")}
        >
          Aceptar
        </Button>
        <Button
          type="button"
          size="sm"
          variant="outline"
          disabled={isDecidingReviewItem}
          onClick={() => onDecideReviewItem(item, "rejected")}
        >
          Rechazar
        </Button>
      </span>
    </li>
  );
}

function formatReviewDecisionAudit(item: ClinicalReviewItem) {
  const actor = item.decision_actor_id ?? "actor no disponible";
  const date = item.decision_at ? formatDate(item.decision_at) : "fecha no disponible";
  const auditId = item.decision_audit_event_id ? ` · audit ${item.decision_audit_event_id}` : "";
  return `${actor} · ${date}${auditId}`;
}
