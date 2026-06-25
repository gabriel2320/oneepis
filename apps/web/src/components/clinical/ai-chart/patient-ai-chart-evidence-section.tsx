"use client";

import type { ClinicalEvent } from "@/lib/types";

import { AiChartGovernancePanel } from "./ai-chart-governance-panel";
import { AssistantReadPanel } from "./assistant-read-panel";
import { EventSelectionPanel } from "./event-selection-panel";

type PatientAiChartEvidenceSectionProps = {
  patientId: string;
  events: ClinicalEvent[];
  selectedIds: string[];
  recentEntryCount: number;
  canUseAi: boolean;
  canWriteSoap: boolean;
  canCreateEvents: boolean;
  isGenerating: boolean;
  hasError: boolean;
  onGenerate: () => void;
  onSelectedIdsChange: (ids: string[]) => void;
};

export function PatientAiChartEvidenceSection({
  patientId,
  events,
  selectedIds,
  recentEntryCount,
  canUseAi,
  canWriteSoap,
  canCreateEvents,
  isGenerating,
  hasError,
  onGenerate,
  onSelectedIdsChange,
}: PatientAiChartEvidenceSectionProps) {
  return (
    <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_420px]">
      <EventSelectionPanel
        events={events}
        selectedIds={selectedIds}
        isGenerating={isGenerating}
        canUseAi={canUseAi}
        hasError={hasError}
        onGenerate={onGenerate}
        onSelectedIdsChange={onSelectedIdsChange}
      />
      <div className="space-y-4">
        <AiChartGovernancePanel
          eventCount={events.length}
          entryCount={recentEntryCount}
          selectedEventCount={selectedIds.length}
          canUseAi={canUseAi}
          canWriteSoap={canWriteSoap}
          canCreateEvents={canCreateEvents}
        />
        <AssistantReadPanel patientId={patientId} />
      </div>
    </div>
  );
}
