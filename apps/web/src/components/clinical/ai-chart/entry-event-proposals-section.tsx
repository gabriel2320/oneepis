"use client";

import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { confirmClinicalPatch, proposeEventsFromEntry } from "@/lib/api/clinical-record";
import type {
  ClinicalEntry,
  EventProposalFromEntry,
  EventProposalsFromEntryResponse,
} from "@/lib/types";

import {
  EntryEventProposalsPanel,
  type EventProposalDecisionStatus,
} from "./entry-event-proposals-panel";

type EntryEventProposalsSectionProps = {
  patientId: string;
  entries: ClinicalEntry[];
  canUseAi: boolean;
  canCreateEvents: boolean;
};

export function EntryEventProposalsSection({
  patientId,
  entries,
  canUseAi,
  canCreateEvents,
}: EntryEventProposalsSectionProps) {
  const queryClient = useQueryClient();
  const [selectedEntryId, setSelectedEntryId] = useState("");
  const [proposals, setProposals] = useState<EventProposalsFromEntryResponse | null>(null);
  const [decisionMessage, setDecisionMessage] = useState<string | null>(null);
  const [decisions, setDecisions] = useState<Record<string, EventProposalDecisionStatus>>({});
  const activeEntryId = selectedEntryId || entries[0]?.id || "";

  const proposalMutation = useMutation({
    mutationFn: () => proposeEventsFromEntry(patientId, { entry_id: activeEntryId }),
    onSuccess: (response) => {
      setProposals(response);
      setDecisionMessage(null);
      setDecisions({});
    },
  });
  const acceptMutation = useMutation({
    mutationFn: (proposal: EventProposalFromEntry) =>
      confirmClinicalPatch(patientId, {
        decision: "accepted",
        patch: proposal.patch,
      }),
    onMutate: (proposal) => {
      setDecisions((current) => ({ ...current, [proposal.proposal_id]: "registering" }));
      setDecisionMessage(null);
    },
    onSuccess: async (response, proposal) => {
      setDecisions((current) => ({ ...current, [proposal.proposal_id]: "registered" }));
      setDecisionMessage(response.message);
      await queryClient.invalidateQueries({ queryKey: ["clinical-events", patientId] });
      await queryClient.invalidateQueries({ queryKey: ["patient-record", patientId] });
    },
    onError: (_error, proposal) => {
      setDecisions((current) => {
        const next = { ...current };
        delete next[proposal.proposal_id];
        return next;
      });
    },
  });
  const rejectMutation = useMutation({
    mutationFn: (proposal: EventProposalFromEntry) =>
      confirmClinicalPatch(patientId, {
        decision: "rejected",
        patch: proposal.patch,
      }),
    onMutate: (proposal) => {
      setDecisions((current) => ({ ...current, [proposal.proposal_id]: "registering" }));
      setDecisionMessage(null);
    },
    onSuccess: (response, proposal) => {
      setDecisions((current) => ({ ...current, [proposal.proposal_id]: "rejected" }));
      setDecisionMessage(response.message);
    },
    onError: (_error, proposal) => {
      setDecisions((current) => {
        const next = { ...current };
        delete next[proposal.proposal_id];
        return next;
      });
    },
  });

  return (
    <EntryEventProposalsPanel
      entries={entries}
      selectedEntryId={activeEntryId}
      proposals={proposals}
      canUseAi={canUseAi}
      canCreateEvents={canCreateEvents}
      isGenerating={proposalMutation.isPending}
      isAccepting={acceptMutation.isPending}
      isRejecting={rejectMutation.isPending}
      hasGenerateError={proposalMutation.isError}
      decisionMessage={decisionMessage}
      decisions={decisions}
      onSelectedEntryIdChange={(entryId) => {
        setSelectedEntryId(entryId);
        setProposals(null);
        setDecisionMessage(null);
        setDecisions({});
      }}
      onGenerate={() => proposalMutation.mutate()}
      onAccept={(proposal) => acceptMutation.mutate(proposal)}
      onReject={(proposal) => rejectMutation.mutate(proposal)}
    />
  );
}
