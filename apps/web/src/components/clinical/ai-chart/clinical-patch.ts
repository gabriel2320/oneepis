import type { HumanReviewConfirmation, SoapDraftState } from "@/components/clinical/ai-chart/ai-chart-types";
import { emptyToNull } from "@/components/clinical/ai-chart/ai-chart-utils";
import type { ClinicalPatch, DraftSoapFromEventsResponse } from "@/lib/types";

export function buildSoapDraftPatch({
  soap,
  draft,
  review,
}: {
  soap: SoapDraftState;
  draft: DraftSoapFromEventsResponse | null;
  review: HumanReviewConfirmation;
}): ClinicalPatch {
  const occurredAt = review.human_reviewed_at;
  const reason = "Borrador SOAP revisado por humano desde AI-Chart.";
  return {
    patch_id: `soap-draft:${occurredAt}`,
    target: "evolution",
    mode: "draft",
    operations: [
      { op: "add", path: "/kind", value: "progress", reason },
      {
        op: "add",
        path: "/status",
        value: "draft",
        reason: "Las propuestas IA se guardan como borrador no firmado.",
      },
      { op: "add", path: "/occurred_at", value: occurredAt, reason: "Fecha de revision humana." },
      { op: "add", path: "/title", value: soap.title, reason: "Titulo editable confirmado." },
      { op: "add", path: "/subjective", value: emptyToNull(soap.subjective), reason: "Seccion S confirmada." },
      { op: "add", path: "/objective", value: emptyToNull(soap.objective), reason: "Seccion O confirmada." },
      { op: "add", path: "/assessment", value: emptyToNull(soap.assessment), reason: "Seccion A confirmada." },
      { op: "add", path: "/plan", value: emptyToNull(soap.plan), reason: "Seccion P confirmada." },
      { op: "add", path: "/tags", value: ["soap", "ai-chart"], reason: "Trazabilidad del origen." },
      {
        op: "add",
        path: "/extra_data",
        value: {
          ai_chart_sources: draft?.sources ?? [],
          ai_chart_section_sources: draft?.section_sources ?? [],
          ai_provider: draft?.provider,
          requires_human_confirmation: true,
          human_reviewed: review.human_reviewed,
          human_reviewed_at: review.human_reviewed_at,
        },
        reason: "Metadata de fuentes, proveedor y revision.",
      },
    ],
    sources:
      draft?.sources.map((source) => ({
        source_type: "clinical_event",
        source_id: source.clinical_event_id,
        label: source.label,
      })) ?? [],
    warnings: draft?.warnings ?? [],
    requires_human_confirmation: true,
  };
}
