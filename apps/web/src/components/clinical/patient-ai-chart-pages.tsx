"use client";

import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { useCurrentUser } from "@/components/auth/use-current-user";
import { AiChartGovernancePanel } from "@/components/clinical/ai-chart/ai-chart-governance-panel";
import type {
  HumanReviewConfirmation,
  SoapDraftState,
} from "@/components/clinical/ai-chart/ai-chart-types";
import { clinicalEventSourceIds, emptyToNull } from "@/components/clinical/ai-chart/ai-chart-utils";
import { ClinicalIntentCommandBar } from "@/components/clinical/ai-chart/clinical-intent-command-bar";
import { ClinicalIntentResultPanel } from "@/components/clinical/ai-chart/clinical-intent-result-panel";
import { DraftSoapPaper } from "@/components/clinical/ai-chart/draft-soap-paper";
import { EventSelectionPanel } from "@/components/clinical/ai-chart/event-selection-panel";
import { ClinicalSectionCard } from "@/components/clinical/cards";
import { PatientClinicalLoading, PatientClinicalShell } from "@/components/clinical/patient-clinical-shell";
import { ErrorState } from "@/components/clinical/states";
import { AppShell } from "@/components/layout/app-shell";
import { getAiStatus } from "@/lib/api/ai";
import {
  createClinicalEntry,
  createClinicalIntent,
  decideClinicalIntentAction,
  decideClinicalReviewItem,
  draftSoapFromEvents,
  listClinicalEvents,
  routeClinicalIntent,
} from "@/lib/api/clinical-record";
import { DEMO_MODE } from "@/lib/api/client";
import { canManageClinicalEntries, canUseClinicalAi } from "@/lib/permissions";
import type {
  ClinicalIntentAction,
  ClinicalIntentResponse,
  ClinicalIntentRouteResponse,
  ClinicalIntentType,
  ClinicalReviewItem,
  DraftSoapFromEventsResponse,
} from "@/lib/types";

import { BackLink, PageTitle, usePatientId, usePatientRecordQuery } from "./patient-page-shared";

export function PatientAiChartPage() {
  const patientId = usePatientId();
  const router = useRouter();
  const queryClient = useQueryClient();
  const { record, recordQuery } = usePatientRecordQuery(patientId);
  const { user, isLoading: userLoading } = useCurrentUser();
  const canUseAi = canUseClinicalAi(user);
  const canWriteSoap = canManageClinicalEntries(user);
  const aiStatus = useQuery({
    queryKey: ["ai-status"],
    queryFn: getAiStatus,
    enabled: !DEMO_MODE,
    staleTime: 30_000,
  });
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [draft, setDraft] = useState<DraftSoapFromEventsResponse | null>(null);
  const [intent, setIntent] = useState<ClinicalIntentResponse | null>(null);
  const [routerText, setRouterText] = useState("");
  const [routedIntent, setRoutedIntent] = useState<ClinicalIntentRouteResponse | null>(null);
  const [reviewDecisionMessage, setReviewDecisionMessage] = useState<string | null>(null);
  const [actionDecisionMessage, setActionDecisionMessage] = useState<string | null>(null);
  const [soap, setSoap] = useState<SoapDraftState>({
    title: "Evolucion SOAP desde eventos",
    subjective: "",
    objective: "",
    assessment: "",
    plan: "",
  });

  const eventsQuery = useQuery({
    queryKey: ["clinical-events", patientId],
    queryFn: () => listClinicalEvents(patientId),
    enabled: Boolean(patientId) && !DEMO_MODE,
  });
  const events = useMemo(() => eventsQuery.data ?? [], [eventsQuery.data]);

  const draftMutation = useMutation({
    mutationFn: (clinicalEventIds?: string[]) =>
      draftSoapFromEvents(patientId, { clinical_event_ids: clinicalEventIds ?? selectedIds }),
    onSuccess: (response) => {
      setDraft(response);
      setSoap({
        title: response.title,
        subjective: response.subjective,
        objective: response.objective,
        assessment: response.assessment,
        plan: response.plan,
      });
    },
  });
  const intentMutation = useMutation({
    mutationFn: (intentType: ClinicalIntentType) =>
      createClinicalIntent(patientId, {
        intent_type: intentType,
        mode: intentType === "draft_soap" ? "draft" : "read",
      }),
    onSuccess: (response) => {
      setIntent(response);
      if (response.intent_type === "draft_soap") {
        const sourceEventIds = clinicalEventSourceIds(response);
        if (sourceEventIds.length > 0) {
          setSelectedIds(sourceEventIds);
          draftMutation.mutate(sourceEventIds);
        }
      }
    },
  });
  const routeMutation = useMutation({
    mutationFn: () => routeClinicalIntent(patientId, { text: routerText }),
    onSuccess: (response) => {
      setRoutedIntent(response);
      if (response.intent_type) {
        intentMutation.mutate(response.intent_type);
      }
    },
  });
  const saveMutation = useMutation({
    mutationFn: (review: HumanReviewConfirmation) =>
      createClinicalEntry(patientId, {
        kind: "progress",
        status: "draft",
        occurred_at: new Date().toISOString(),
        title: soap.title,
        subjective: emptyToNull(soap.subjective),
        objective: emptyToNull(soap.objective),
        assessment: emptyToNull(soap.assessment),
        plan: emptyToNull(soap.plan),
        tags: ["soap", "ai-chart"],
        extra_data: {
          ai_chart_sources: draft?.sources ?? [],
          ai_chart_section_sources: draft?.section_sources ?? [],
          ai_provider: draft?.provider,
          requires_human_confirmation: true,
          human_reviewed: review.human_reviewed,
          human_reviewed_at: review.human_reviewed_at,
        },
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["patient-record", patientId] });
      router.push(`/pacientes/${patientId}/evoluciones`);
    },
  });
  const reviewDecisionMutation = useMutation({
    mutationFn: ({
      item,
      decision,
    }: {
      item: ClinicalReviewItem;
      decision: "accepted" | "rejected";
    }) =>
      decideClinicalReviewItem(patientId, {
        decision,
        item_type: item.item_type,
        label: item.label,
        detail: item.detail,
        source_type: item.source_type,
        source_id: item.source_id,
      }),
    onSuccess: (response) => {
      setReviewDecisionMessage(response.message);
    },
  });
  const actionDecisionMutation = useMutation({
    mutationFn: (action: ClinicalIntentAction) =>
      decideClinicalIntentAction(patientId, {
        decision: action.requires_confirmation ? "accepted" : "reviewed",
        action_type: action.action_type,
        action_id: action.action_id,
        label: action.label,
        description: action.description,
        requires_confirmation: action.requires_confirmation,
      }),
    onSuccess: (response) => {
      setActionDecisionMessage(response.message);
    },
  });

  if (recordQuery.isLoading && !DEMO_MODE) {
    return <PatientClinicalLoading />;
  }

  if (!record) {
    return (
      <AppShell>
        <div className="mx-auto max-w-3xl p-4 md:p-6">
          <ErrorState description="No se pudo cargar el paciente para AI-Chart." />
        </div>
      </AppShell>
    );
  }

  return (
    <PatientClinicalShell record={record} activeSection="ai-chart">
      <div className="space-y-5">
        <BackLink href={`/pacientes/${patientId}/ficha`} label="Ficha" />
        <PageTitle
          title="AI-Chart Core"
          description="Eventos clinicos -> contexto -> borrador SOAP editable -> confirmacion humana."
        />
        {DEMO_MODE ? <ErrorState description="El modo demo no permite generar borradores reales." /> : null}
        {!DEMO_MODE && !userLoading && !canUseAi ? (
          <ErrorState description="Tu rol actual no permite usar IA clinica." />
        ) : null}
        <ClinicalSectionCard
          title="Intenciones clinicas"
          description="Barra dirigida: interpreta frases clinicas y propone acciones seguras."
        >
          <ClinicalIntentCommandBar
            routerText={routerText}
            routedIntent={routedIntent}
            aiStatus={aiStatus.data}
            aiStatusIsError={aiStatus.isError}
            canUseAi={canUseAi}
            isRouting={routeMutation.isPending}
            isExecuting={intentMutation.isPending}
            hasRouteError={routeMutation.isError}
            hasIntentError={intentMutation.isError}
            patientId={patientId}
            onRouterTextChange={setRouterText}
            onRoute={() => routeMutation.mutate()}
            onExecuteIntent={(intentType) => intentMutation.mutate(intentType)}
          />
          {intent ? (
            <ClinicalIntentResultPanel
              intent={intent}
              patientId={patientId}
              onDecideReviewItem={(item, decision) =>
                reviewDecisionMutation.mutate({ item, decision })
              }
              isDecidingReviewItem={reviewDecisionMutation.isPending}
              reviewDecisionMessage={reviewDecisionMessage}
              onDecideAction={(action) => actionDecisionMutation.mutate(action)}
              isDecidingAction={actionDecisionMutation.isPending}
              actionDecisionMessage={actionDecisionMessage}
            />
          ) : null}
        </ClinicalSectionCard>

        <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_420px]">
          <EventSelectionPanel
            events={events}
            selectedIds={selectedIds}
            isGenerating={draftMutation.isPending}
            canUseAi={canUseAi}
            hasError={eventsQuery.isError}
            onGenerate={() => draftMutation.mutate(undefined)}
            onSelectedIdsChange={setSelectedIds}
          />
          <AiChartGovernancePanel />
        </div>

        {draftMutation.isError ? <ErrorState description="No se pudo generar el borrador SOAP." /> : null}
        {draft ? (
          <DraftSoapPaper
            draft={draft}
            soap={soap}
            canWriteSoap={canWriteSoap}
            isSaving={saveMutation.isPending}
            saveError={saveMutation.isError}
            onSave={(review) => saveMutation.mutate(review)}
            onSoapChange={setSoap}
          />
        ) : null}
      </div>
    </PatientClinicalShell>
  );
}
