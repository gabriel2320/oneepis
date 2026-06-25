"use client";

import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { useCurrentUser } from "@/components/auth/use-current-user";
import { AiChartStep } from "@/components/clinical/ai-chart/ai-chart-step";
import type {
  HumanReviewConfirmation,
  SoapDraftState,
} from "@/components/clinical/ai-chart/ai-chart-types";
import { clinicalEventSourceIds } from "@/components/clinical/ai-chart/ai-chart-utils";
import { buildSoapDraftPatch } from "@/components/clinical/ai-chart/clinical-patch";
import { EntryEventProposalsSection } from "@/components/clinical/ai-chart/entry-event-proposals-section";
import { PatientAiChartDraftSection } from "@/components/clinical/ai-chart/patient-ai-chart-draft-section";
import { PatientAiChartEvidenceSection } from "@/components/clinical/ai-chart/patient-ai-chart-evidence-section";
import { PatientAiChartIntentSection } from "@/components/clinical/ai-chart/patient-ai-chart-intent-section";
import { PatientClinicalLoading, PatientClinicalShell } from "@/components/clinical/patient-clinical-shell";
import { ErrorState } from "@/components/clinical/states";
import { AppShell } from "@/components/layout/app-shell";
import { getAiStatus } from "@/lib/api/ai";
import {
  confirmClinicalPatch,
  createClinicalIntent,
  decideClinicalIntentAction,
  decideClinicalReviewItem,
  draftSoapFromEvents,
  listClinicalEvents,
  streamClinicalCommandPreview,
} from "@/lib/api/clinical-record";
import { DEMO_MODE } from "@/lib/api/client";
import { canManageClinicalEntries, canManageClinicalEvents, canUseClinicalAi } from "@/lib/permissions";
import type {
  ClinicalIntentAction,
  ClinicalIntentResponse,
  ClinicalIntentRouteResponse,
  ClinicalIntentType,
  ClinicalReviewItem,
  DraftSoapFromEventsResponse,
  AIStreamEvent,
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
  const canCreateEvents = canManageClinicalEvents(user);
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
  const [routeEvents, setRouteEvents] = useState<AIStreamEvent[]>([]);
  const [isStreamingRoutePreview, setIsStreamingRoutePreview] = useState(false);
  const [routePreviewError, setRoutePreviewError] = useState(false);
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
  const recentEntries = record?.recent_entries ?? [];

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
    mutationFn: async () => {
      setRouteEvents([]);
      setRoutePreviewError(false);
      setIsStreamingRoutePreview(true);
      try {
        return await streamClinicalCommandPreview({
          patientId,
          text: routerText,
          onEvent: (event) => setRouteEvents((current) => [...current, event]),
        });
      } catch {
        setRoutePreviewError(true);
        throw new Error("No se pudo orquestar la intencion clinica.");
      } finally {
        setIsStreamingRoutePreview(false);
      }
    },
    onSuccess: (response) => {
      setRoutedIntent(response);
      if (response.intent_type) {
        intentMutation.mutate(response.intent_type);
      }
    },
  });
  const saveMutation = useMutation({
    mutationFn: (review: HumanReviewConfirmation) =>
      confirmClinicalPatch(patientId, {
        decision: "accepted",
        patch: buildSoapDraftPatch({ soap, draft, review }),
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
        <AiChartStep
          step="1"
          title="Leer contexto"
          description="Primero revisa fuentes, faltantes y limites antes de preparar cualquier borrador."
        />
        <PatientAiChartIntentSection
          routerText={routerText}
          routedIntent={routedIntent}
          aiStatus={aiStatus.data}
          aiStatusIsError={aiStatus.isError}
          canUseAi={canUseAi}
          isRouting={routeMutation.isPending}
          isExecuting={intentMutation.isPending}
          hasRouteError={routeMutation.isError}
          routeEvents={routeEvents}
          isStreamingRoutePreview={isStreamingRoutePreview}
          hasRoutePreviewError={routePreviewError}
          hasIntentError={intentMutation.isError}
          patientId={patientId}
          intent={intent}
          isDecidingReviewItem={reviewDecisionMutation.isPending}
          reviewDecisionMessage={reviewDecisionMessage}
          isDecidingAction={actionDecisionMutation.isPending}
          actionDecisionMessage={actionDecisionMessage}
          onRouterTextChange={setRouterText}
          onRoute={() => routeMutation.mutate()}
          onExecuteIntent={(intentType) => intentMutation.mutate(intentType)}
          onDecideReviewItem={(item, decision) =>
            reviewDecisionMutation.mutate({ item, decision })
          }
          onDecideAction={(action) => actionDecisionMutation.mutate(action)}
        />

        <AiChartStep
          step="2"
          title="Seleccionar evidencia"
          description="Elige eventos clinicos y revisa lectura contextual; Assistant Read no escribe ficha."
        />
        <PatientAiChartEvidenceSection
          patientId={patientId}
          events={events}
          selectedIds={selectedIds}
          recentEntryCount={recentEntries.length}
          canUseAi={canUseAi}
          canWriteSoap={canWriteSoap}
          canCreateEvents={canCreateEvents}
          isGenerating={draftMutation.isPending}
          hasError={eventsQuery.isError}
          onGenerate={() => draftMutation.mutate(undefined)}
          onSelectedIdsChange={setSelectedIds}
        />

        <AiChartStep
          step="3"
          title="Revisar propuestas"
          description="Las propuestas desde evoluciones son revisables y mantienen estados visibles."
        />
        <EntryEventProposalsSection
          patientId={patientId}
          entries={recentEntries}
          canUseAi={canUseAi}
          canCreateEvents={canCreateEvents}
        />

        <PatientAiChartDraftSection
          draft={draft}
          soap={soap}
          canWriteSoap={canWriteSoap}
          isSaving={saveMutation.isPending}
          saveError={saveMutation.isError}
          draftError={draftMutation.isError}
          onSave={(review) => saveMutation.mutate(review)}
          onSoapChange={setSoap}
        />
      </div>
    </PatientClinicalShell>
  );
}
