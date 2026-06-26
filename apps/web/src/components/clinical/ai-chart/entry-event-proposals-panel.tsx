"use client";

import { Button } from "@/components/ui/button";
import { DEMO_MODE } from "@/lib/api/client";
import type {
  ClinicalEntry,
  EventProposalFromEntry,
  EventProposalsFromEntryResponse,
} from "@/lib/types";

import { formatDate } from "./ai-chart-utils";
import { ClinicalPatchPreview } from "./clinical-patch-preview";

export type EventProposalDecisionStatus = "pending" | "registering" | "registered" | "rejected";

type EntryEventProposalsPanelProps = {
  entries: ClinicalEntry[];
  selectedEntryId: string;
  proposals: EventProposalsFromEntryResponse | null;
  canUseAi: boolean;
  canCreateEvents: boolean;
  isGenerating: boolean;
  isAccepting: boolean;
  isRejecting: boolean;
  hasGenerateError: boolean;
  decisionMessage: string | null;
  decisions: Record<string, EventProposalDecisionStatus>;
  onSelectedEntryIdChange: (entryId: string) => void;
  onGenerate: () => void;
  onAccept: (proposal: EventProposalFromEntry) => void;
  onReject: (proposal: EventProposalFromEntry) => void;
};

export function EntryEventProposalsPanel({
  entries,
  selectedEntryId,
  proposals,
  canUseAi,
  canCreateEvents,
  isGenerating,
  isAccepting,
  isRejecting,
  hasGenerateError,
  decisionMessage,
  decisions,
  onSelectedEntryIdChange,
  onGenerate,
  onAccept,
  onReject,
}: EntryEventProposalsPanelProps) {
  const generateBlockedReason = proposalGenerationBlockedReason({
    selectedEntryId,
    canUseAi,
    isGenerating,
  });
  return (
    <div className="rounded-md border p-3">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-sm font-medium">Eventos desde evolucion</p>
          <p className="mt-1 text-xs text-muted-foreground">
            Propone eventos longitudinales desde una evolucion escrita. No registra nada sin
            aceptacion humana.
          </p>
        </div>
        <span className="rounded-md border px-2 py-1 text-xs text-muted-foreground">
          propuesta revisable
        </span>
      </div>
      <p className="mt-2 text-[11px] text-muted-foreground">
        Estados: pendiente / registrando / registrada en ficha / rechazada.
      </p>
      <div className="mt-3 grid gap-2 md:grid-cols-[minmax(0,1fr)_auto]">
        <select
          className="h-9 rounded-md border bg-background px-3 text-sm"
          value={selectedEntryId}
          disabled={entries.length === 0 || isGenerating}
          onChange={(event) => onSelectedEntryIdChange(event.target.value)}
        >
          {entries.length > 0 ? (
            entries.map((entry) => (
              <option key={entry.id} value={entry.id}>
                {entry.title} / {formatDate(entry.occurred_at)}
              </option>
            ))
          ) : (
            <option value="">Sin evoluciones recientes</option>
          )}
        </select>
        <Button
          type="button"
          variant="secondary"
          disabled={Boolean(generateBlockedReason)}
          onClick={onGenerate}
        >
          {isGenerating ? "Generando..." : "Proponer eventos"}
        </Button>
      </div>
      {generateBlockedReason && !isGenerating ? (
        <p className="mt-2 text-xs text-muted-foreground">{generateBlockedReason}</p>
      ) : null}
      {!canUseAi ? (
        <p className="mt-2 text-xs text-muted-foreground">
          Generar propuestas AI-Chart requiere rol admin, medico o dev.
        </p>
      ) : null}
      {hasGenerateError ? (
        <p className="mt-2 text-xs text-destructive">No se pudieron generar propuestas.</p>
      ) : null}
      {proposals ? (
        <div className="mt-3 space-y-2">
          {proposals.warnings.map((warning) => (
            <p key={warning} className="text-xs text-muted-foreground">
              {warning}
            </p>
          ))}
          {proposals.proposals.length > 0 ? (
            <ul className="space-y-2">
              {proposals.proposals.map((proposal) => (
                <ProposalRow
                  key={proposal.proposal_id}
                  proposal={proposal}
                  decision={decisions[proposal.proposal_id]}
                  canUseAi={canUseAi}
                  canCreateEvents={canCreateEvents}
                  isMutating={isAccepting || isRejecting}
                  onAccept={onAccept}
                  onReject={onReject}
                />
              ))}
            </ul>
          ) : (
            <p className="text-xs text-muted-foreground">Sin candidatos para esta evolucion.</p>
          )}
        </div>
      ) : null}
      {decisionMessage ? (
        <p className="mt-3 text-xs text-muted-foreground">{decisionMessage}</p>
      ) : null}
    </div>
  );
}

function ProposalRow({
  proposal,
  decision,
  canUseAi,
  canCreateEvents,
  isMutating,
  onAccept,
  onReject,
}: {
  proposal: EventProposalFromEntry;
  decision?: EventProposalDecisionStatus;
  canUseAi: boolean;
  canCreateEvents: boolean;
  isMutating: boolean;
  onAccept: (proposal: EventProposalFromEntry) => void;
  onReject: (proposal: EventProposalFromEntry) => void;
}) {
  const acceptBlockedReason = acceptProposalBlockedReason({
    canUseAi,
    canCreateEvents,
    isMutating,
    decision,
  });
  const rejectBlockedReason = rejectProposalBlockedReason({ isMutating, decision });
  const status = decision ?? "pending";
  return (
    <li className="rounded-md border bg-background p-2 text-xs text-muted-foreground">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span className="font-medium text-foreground">{proposal.summary}</span>
        <div className="flex flex-wrap gap-1.5">
          <span className="rounded-md border px-1.5 py-0.5">{proposalStatusLabel(status)}</span>
          <span className="rounded-md border px-1.5 py-0.5">{proposal.event_type}</span>
        </div>
      </div>
      <p className="mt-1">Fuente: {proposal.evidence_label}</p>
      <p className="mt-1">
        Destino: evento clinico longitudinal, guardado solo al confirmar el patch.
      </p>
      <ClinicalPatchPreview
        title="Patch antes de registrar"
        operations={proposal.patch.operations}
        paths={["/event_type", "/occurred_at", "/summary", "/source_type"]}
      />
      <div className="mt-2 flex flex-wrap gap-2">
        <Button
          type="button"
          size="sm"
          variant="outline"
          disabled={Boolean(acceptBlockedReason)}
          onClick={() => onAccept(proposal)}
        >
          {decision === "registering" ? "Registrando..." : "Registrar evento"}
        </Button>
        <Button
          type="button"
          size="sm"
          variant="outline"
          disabled={Boolean(rejectBlockedReason)}
          onClick={() => onReject(proposal)}
        >
          Rechazar
        </Button>
      </div>
      {acceptBlockedReason && !isMutating ? (
        <p className="mt-2 text-[11px] text-muted-foreground">{acceptBlockedReason}</p>
      ) : null}
    </li>
  );
}

function proposalGenerationBlockedReason({
  selectedEntryId,
  canUseAi,
  isGenerating,
}: {
  selectedEntryId: string;
  canUseAi: boolean;
  isGenerating: boolean;
}) {
  if (isGenerating) {
    return "Generando propuestas.";
  }
  if (!selectedEntryId) {
    return "Selecciona una evolucion reciente.";
  }
  if (DEMO_MODE) {
    return "Modo demo: no se generan propuestas reales.";
  }
  if (!canUseAi) {
    return "Generar propuestas asistidas requiere un perfil autorizado.";
  }
  return null;
}

function acceptProposalBlockedReason({
  canUseAi,
  canCreateEvents,
  isMutating,
  decision,
}: {
  canUseAi: boolean;
  canCreateEvents: boolean;
  isMutating: boolean;
  decision?: EventProposalDecisionStatus;
}) {
  if (isMutating) {
    return "Registrando decision.";
  }
  if (decision && decision !== "pending") {
    return "Esta propuesta ya tiene una decision en esta sesion.";
  }
  if (!canUseAi) {
    return "Registrar propuestas asistidas requiere un perfil autorizado.";
  }
  if (!canCreateEvents) {
    return "Registrar eventos clinicos requiere un perfil clinico autorizado.";
  }
  return null;
}

function rejectProposalBlockedReason({
  isMutating,
  decision,
}: {
  isMutating: boolean;
  decision?: EventProposalDecisionStatus;
}) {
  if (isMutating) {
    return "Registrando decision.";
  }
  if (decision && decision !== "pending") {
    return "Esta propuesta ya tiene una decision en esta sesion.";
  }
  return null;
}

function proposalStatusLabel(status: EventProposalDecisionStatus) {
  const labels: Record<EventProposalDecisionStatus, string> = {
    pending: "pendiente",
    registering: "registrando",
    registered: "registrada en ficha",
    rejected: "rechazada",
  };
  return labels[status];
}
