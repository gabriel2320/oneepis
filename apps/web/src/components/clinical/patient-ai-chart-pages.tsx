"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { type ReactNode, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { BrainCircuit, Save } from "lucide-react";

import { useCurrentUser } from "@/components/auth/use-current-user";
import { ClinicalSectionCard } from "@/components/clinical/cards";
import { PatientClinicalLoading, PatientClinicalShell } from "@/components/clinical/patient-clinical-shell";
import { EmptyState, ErrorState } from "@/components/clinical/states";
import { AppShell } from "@/components/layout/app-shell";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { getAiStatus } from "@/lib/api/ai";
import {
  createClinicalIntent,
  createClinicalEntry,
  decideClinicalIntentAction,
  decideClinicalReviewItem,
  draftSoapFromEvents,
  listClinicalEvents,
  routeClinicalIntent,
} from "@/lib/api/clinical-record";
import { DEMO_MODE } from "@/lib/api/client";
import { canManageClinicalEntries, canUseClinicalAi } from "@/lib/permissions";
import type {
  AIProviderStatus,
  ClinicalEvent,
  ClinicalIntentAction,
  ClinicalIntentResponse,
  ClinicalIntentRouteResponse,
  ClinicalIntentType,
  ClinicalReviewItem,
  DraftSoapFromEventsResponse,
} from "@/lib/types";

import { BackLink, PageTitle, usePatientId, usePatientRecordQuery } from "./patient-page-shared";

type SoapDraftState = {
  title: string;
  subjective: string;
  objective: string;
  assessment: string;
  plan: string;
};

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
  const [soap, setSoap] = useState({
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
    mutationFn: () =>
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
          <div className="mb-4 grid gap-2 md:grid-cols-[minmax(0,1fr)_auto]">
            <Textarea
              className="min-h-16"
              placeholder="Ej: prepara evolucion de hoy, que cambio desde ayer, muestra fuentes"
              value={routerText}
              onChange={(event) => setRouterText(event.target.value)}
            />
            <Button
              type="button"
              variant="secondary"
              disabled={
                routeMutation.isPending ||
                routerText.trim().length === 0 ||
                DEMO_MODE ||
                !canUseAi
              }
              onClick={() => routeMutation.mutate()}
            >
              Ejecutar
            </Button>
          </div>
          {routeMutation.isError ? (
            <p className="mb-3 text-sm text-destructive">No se pudo interpretar la frase clinica.</p>
          ) : null}
          {routedIntent ? (
            <ClinicalIntentRouteResult
              routedIntent={routedIntent}
              onExecute={(intentType) => intentMutation.mutate(intentType)}
              isExecuting={routeMutation.isPending || intentMutation.isPending}
            />
          ) : null}
          <GenerativeAiStatus status={aiStatus.data} isError={aiStatus.isError} />
          <div className="flex flex-wrap gap-2">
            {intentActions.map((action) => (
              <Button
                key={action.intent}
                type="button"
                variant="outline"
                size="sm"
                disabled={intentMutation.isPending || DEMO_MODE || !canUseAi}
                onClick={() => intentMutation.mutate(action.intent)}
              >
                {action.label}
              </Button>
            ))}
          </div>
          {intentMutation.isError ? (
            <p className="mt-3 text-sm text-destructive">No se pudo resolver la intencion clinica.</p>
          ) : null}
          {intent ? (
            <ClinicalIntentResult
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
          <ClinicalSectionCard
            title="Eventos fuente"
            description="Selecciona los hechos que deben entrar al borrador."
            action={
              <Button
                type="button"
                size="sm"
                disabled={
                  selectedIds.length === 0 ||
                  draftMutation.isPending ||
                  DEMO_MODE ||
                  !canUseAi
                }
                onClick={() => draftMutation.mutate(undefined)}
              >
                <BrainCircuit className="h-4 w-4" />
                {draftMutation.isPending ? "Generando..." : "Generar SOAP"}
              </Button>
            }
          >
            <EventSelectionList
              events={events}
              selectedIds={selectedIds}
              onSelectedIdsChange={setSelectedIds}
            />
            {eventsQuery.isError ? <p className="mt-3 text-sm text-destructive">No se pudieron cargar eventos.</p> : null}
          </ClinicalSectionCard>

          <ClinicalSectionCard title="Gobernanza" description="La IA no firma ni escribe sola.">
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li>Todo borrador requiere revision humana.</li>
              <li>Las fuentes quedan en metadata del borrador.</li>
              <li>Si Ollama esta apagado, se usa degradacion local.</li>
            </ul>
          </ClinicalSectionCard>
        </div>

        {draftMutation.isError ? <ErrorState description="No se pudo generar el borrador SOAP." /> : null}
        {draft ? (
          <DraftSoapPaper
            draft={draft}
            soap={soap}
            canWriteSoap={canWriteSoap}
            isSaving={saveMutation.isPending}
            saveError={saveMutation.isError}
            onSave={() => saveMutation.mutate()}
            onSoapChange={setSoap}
          />
        ) : null}
      </div>
    </PatientClinicalShell>
  );
}

function DraftSoapPaper({
  draft,
  soap,
  canWriteSoap,
  isSaving,
  saveError,
  onSave,
  onSoapChange,
}: {
  draft: DraftSoapFromEventsResponse;
  soap: SoapDraftState;
  canWriteSoap: boolean;
  isSaving: boolean;
  saveError: boolean;
  onSave: () => void;
  onSoapChange: (next: SoapDraftState | ((current: SoapDraftState) => SoapDraftState)) => void;
}) {
  const providerStatus = draft.ai_available ? "IA generativa activa" : "Modo estructurado sin IA";
  const certainty = draft.sources.length > 0 ? "moderada" : "baja";
  return (
    <ClinicalSectionCard
      title="Hoja carta SOAP"
      description="Borrador editable con margen inteligente, no firmado."
      action={
        <Button
          type="button"
          size="sm"
          disabled={isSaving || DEMO_MODE || !canWriteSoap}
          onClick={onSave}
        >
          <Save className="h-4 w-4" />
          {isSaving ? "Guardando..." : "Guardar borrador"}
        </Button>
      }
    >
      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_320px]">
        <div className="rounded-md border bg-background p-4 shadow-sm">
          <div className="mb-4 border-b pb-3">
            <p className="text-xs font-medium uppercase text-muted-foreground">
              Evolucion medica · borrador no firmado
            </p>
            <Textarea
              className="mt-2 min-h-16 border-0 bg-muted/30 text-lg font-semibold shadow-none focus-visible:ring-1"
              value={soap.title}
              onChange={(event) =>
                onSoapChange((current) => ({ ...current, title: event.target.value }))
              }
            />
          </div>
          <div className="space-y-4">
            <SoapTextareaLike
              label="S"
              value={soap.subjective}
              onChange={(value) => onSoapChange((current) => ({ ...current, subjective: value }))}
            />
            <SoapTextareaLike
              label="O"
              value={soap.objective}
              onChange={(value) => onSoapChange((current) => ({ ...current, objective: value }))}
            />
            <SoapTextareaLike
              label="A"
              value={soap.assessment}
              onChange={(value) => onSoapChange((current) => ({ ...current, assessment: value }))}
            />
            <SoapTextareaLike
              label="P"
              value={soap.plan}
              onChange={(value) => onSoapChange((current) => ({ ...current, plan: value }))}
            />
          </div>
        </div>
        <aside className="space-y-3 rounded-md border bg-muted/20 p-3">
          <div>
            <p className="text-sm font-medium">Margen inteligente</p>
            <p className="mt-1 text-xs text-muted-foreground">
              Visible, editable y auditable antes de guardar.
            </p>
          </div>
          <SmartMarginBlock title="Estado">
            <p>{providerStatus}</p>
            <p>Proveedor: {draft.provider}</p>
            <p>Certeza: {certainty}</p>
            <p>Firma: requiere confirmacion humana</p>
          </SmartMarginBlock>
          <SmartMarginBlock title="Fuentes">
            {draft.sources.length > 0 ? (
              <ul className="space-y-1">
                {draft.sources.map((source) => (
                  <li key={source.clinical_event_id}>{source.label}</li>
                ))}
              </ul>
            ) : (
              <p>Sin fuentes estructuradas.</p>
            )}
          </SmartMarginBlock>
          <SmartMarginBlock title="Trazabilidad S/O/A/P">
            {draft.section_sources.length > 0 ? (
              <ul className="space-y-2">
                {draft.section_sources.map((source) => (
                  <li key={`${source.section}-${source.source_type}-${source.source_id ?? source.label}`}>
                    <span className="font-medium text-foreground">
                      {soapSectionLabel(source.section)}
                    </span>
                    <span className="block">{source.label}</span>
                    <span className="block">{source.reason}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p>Sin trazabilidad por seccion.</p>
            )}
          </SmartMarginBlock>
          <SmartMarginBlock title="Datos faltantes y advertencias">
            {draft.warnings.length > 0 ? (
              <ul className="space-y-1">
                {draft.warnings.map((warning) => (
                  <li key={warning}>{warning}</li>
                ))}
              </ul>
            ) : (
              <p>Sin advertencias criticas del generador.</p>
            )}
          </SmartMarginBlock>
          <SmartMarginBlock title="Acciones humanas">
            <ul className="space-y-1">
              <li>Editar texto antes de guardar.</li>
              <li>Guardar como borrador clinico.</li>
              <li>Firmar solo en flujo humano futuro.</li>
            </ul>
          </SmartMarginBlock>
          {saveError ? <p className="text-sm text-destructive">No se pudo guardar el borrador.</p> : null}
        </aside>
      </div>
    </ClinicalSectionCard>
  );
}

function SmartMarginBlock({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="rounded-md border bg-background p-3 text-xs text-muted-foreground">
      <p className="mb-2 font-medium text-foreground">{title}</p>
      {children}
    </div>
  );
}

function soapSectionLabel(section: DraftSoapFromEventsResponse["section_sources"][number]["section"]) {
  const labels = {
    subjective: "S",
    objective: "O",
    assessment: "A",
    plan: "P",
  };
  return labels[section];
}

function EventSelectionList({
  events,
  selectedIds,
  onSelectedIdsChange,
}: {
  events: ClinicalEvent[];
  selectedIds: string[];
  onSelectedIdsChange: (ids: string[]) => void;
}) {
  if (events.length === 0) {
    return (
      <EmptyState
        title="Sin eventos clinicos"
        description="Registra eventos antes de pedir un borrador SOAP desde AI-Chart."
      />
    );
  }

  return (
    <div className="space-y-2">
      {events.map((event) => {
        const checked = selectedIds.includes(event.id);
        return (
          <label key={event.id} className="flex gap-3 rounded-md border p-3 text-sm">
            <input
              type="checkbox"
              className="mt-1"
              checked={checked}
              onChange={(change) => {
                if (change.target.checked) {
                  onSelectedIdsChange([...selectedIds, event.id]);
                  return;
                }
                onSelectedIdsChange(selectedIds.filter((id) => id !== event.id));
              }}
            />
            <span className="min-w-0">
              <span className="block font-medium">{event.summary}</span>
              <span className="block text-xs text-muted-foreground">
                {event.event_type} - {formatDate(event.occurred_at)}
              </span>
            </span>
          </label>
        );
      })}
    </div>
  );
}

const intentActions: { intent: ClinicalIntentType; label: string }[] = [
  { intent: "summarize_patient", label: "Resume paciente" },
  { intent: "daily_changes", label: "Que cambio" },
  { intent: "active_problems", label: "Problemas activos" },
  { intent: "timeline", label: "Timeline" },
  { intent: "draft_soap", label: "Prepara SOAP" },
  { intent: "show_sources", label: "Fuentes" },
];

function ClinicalIntentRouteResult({
  routedIntent,
  onExecute,
  isExecuting,
}: {
  routedIntent: ClinicalIntentRouteResponse;
  onExecute: (intentType: ClinicalIntentType) => void;
  isExecuting: boolean;
}) {
  const fallbackIntents = routedIntent.fallback_options
    .map((action) => ({
      label: action.label,
      intent: fallbackActionToIntent(action),
    }))
    .filter((item): item is { label: string; intent: ClinicalIntentType } => Boolean(item.intent));
  return (
    <div className="mb-4 rounded-md border bg-muted/30 p-3">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-sm font-medium">
            {routedIntent.recognized ? "Intencion reconocida" : "Intencion no reconocida"}
          </p>
          <p className="mt-1 text-xs text-muted-foreground">
            {routedIntent.explanation} Confianza: {routedIntent.confidence}.
          </p>
        </div>
        {routedIntent.intent_type ? (
          <Button
            type="button"
            variant="outline"
            size="sm"
            disabled={isExecuting}
            onClick={() => onExecute(routedIntent.intent_type as ClinicalIntentType)}
          >
            {isExecuting ? "Ejecutando..." : "Reejecutar"}
          </Button>
        ) : null}
      </div>
      {!routedIntent.recognized ? (
        <div className="mt-3 flex flex-wrap gap-2">
          {fallbackIntents.map((action) => (
            <Button
              key={action.label}
              type="button"
              variant="outline"
              size="sm"
              disabled={isExecuting}
              onClick={() => onExecute(action.intent)}
            >
              {action.label}
            </Button>
          ))}
        </div>
      ) : null}
    </div>
  );
}

function GenerativeAiStatus({
  status,
  isError,
}: {
  status?: AIProviderStatus;
  isError: boolean;
}) {
  const label = aiStatusLabel(status, isError);
  return (
    <div className="mb-4 rounded-md border bg-background p-3 text-sm">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <p className="font-medium">Estado IA generativa</p>
          <p className="mt-1 text-xs text-muted-foreground">
            AI-Chart mantiene reglas, plantillas y auditoria aunque Ollama no este disponible.
          </p>
        </div>
        <span className="rounded-md border px-2 py-1 text-xs text-muted-foreground">{label}</span>
      </div>
      {status ? <p className="mt-2 text-xs text-muted-foreground">{status.message}</p> : null}
    </div>
  );
}

function ClinicalIntentResult({
  intent,
  patientId,
  onDecideReviewItem,
  isDecidingReviewItem,
  reviewDecisionMessage,
  onDecideAction,
  isDecidingAction,
  actionDecisionMessage,
}: {
  intent: ClinicalIntentResponse;
  patientId: string;
  onDecideReviewItem: (item: ClinicalReviewItem, decision: "accepted" | "rejected") => void;
  isDecidingReviewItem: boolean;
  reviewDecisionMessage: string | null;
  onDecideAction: (action: ClinicalIntentAction) => void;
  isDecidingAction: boolean;
  actionDecisionMessage: string | null;
}) {
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
        <Change24hSummary groups={ruleGroups} />
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
                    <span className="block">
                      Auditoria: {formatReviewDecisionAudit(item)}
                    </span>
                  </li>
                ))}
              </ul>
            </details>
          ) : null}
          {reviewDecisionMessage ? (
            <p className="mt-3 text-xs text-muted-foreground">{reviewDecisionMessage}</p>
          ) : null}
        </div>
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
        <div className="rounded-md border p-3">
          <p className="text-sm font-medium">Acciones propuestas</p>
          <ul className="mt-2 space-y-2 text-xs text-muted-foreground">
            {intent.proposed_actions.map((action) => {
              const actionKey = clinicalActionKey(action);
              const target = clinicalActionTarget(patientId, action);
              const isReviewed = reviewedActionIds.includes(actionKey);
              return (
                <li
                  key={actionKey}
                  className="rounded-md border bg-background p-2"
                >
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
                      onClick={() => {
                        onDecideAction(action);
                        setReviewedActionIds((current) => [...current, actionKey]);
                      }}
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
      </div>
    </div>
  );
}

function Change24hSummary({ groups }: { groups: { label: string; items: RuleFindingView[] }[] }) {
  const findings = groups.flatMap((group) =>
    group.items.slice(0, 2).map((item) => ({
      ...item,
      group: group.label,
    })),
  );
  if (findings.length === 0) {
    return null;
  }
  return (
    <div className="mt-4 rounded-md border bg-background p-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-sm font-medium">Cambios 24 h</p>
        <span className="rounded-md border px-2 py-1 text-xs text-muted-foreground">
          reglas estructuradas
        </span>
      </div>
      <div className="mt-3 grid gap-2 md:grid-cols-2">
        {findings.map((item) => (
          <div key={`${item.group}-${item.text}`} className="rounded-md border bg-muted/20 p-2 text-xs">
            <div className="flex flex-wrap items-center gap-1.5">
              <span className="rounded-md border bg-background px-1.5 py-0.5 text-muted-foreground">
                {item.status}
              </span>
              <span className="font-medium">{item.group}</span>
            </div>
            <p className="mt-1 text-muted-foreground">{item.text}</p>
            <p className="mt-1 text-[11px] text-muted-foreground">Fuente: {item.source}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

function clinicalActionKey(action: ClinicalIntentResponse["proposed_actions"][number]) {
  return action.action_id ?? `${action.action_type}-${action.label}`;
}

function clinicalEventSourceIds(intent: ClinicalIntentResponse) {
  return intent.sources
    .filter((source) => source.source_type === "clinical_event" && source.source_id)
    .map((source) => source.source_id as string);
}

function clinicalActionTarget(patientId: string, action: ClinicalIntentAction) {
  const eventHref = clinicalEventPrefillHref(patientId, action);
  const problemHref = clinicalProblemPrefillHref(patientId, action);
  const targets: Partial<Record<ClinicalIntentAction["action_type"], { href: string; label: string }>> = {
    create_event: {
      href: problemHref ?? eventHref,
      label: problemHref ? "Registrar problema" : "Abrir eventos",
    },
    create_soap_draft: {
      href: `/pacientes/${patientId}/evoluciones/desde-eventos`,
      label: "Crear borrador",
    },
    review_sources: {
      href: `/pacientes/${patientId}/ficha`,
      label: "Revisar ficha",
    },
    add_pending: {
      href: eventHref,
      label: "Registrar pendiente",
    },
  };
  return targets[action.action_type] ?? null;
}

function clinicalProblemPrefillHref(patientId: string, action: ClinicalIntentAction) {
  const normalizedLabel = action.label.toLocaleLowerCase("es-CL");
  if (!normalizedLabel.includes("problema")) {
    return null;
  }
  const params = new URLSearchParams({
    title: action.label,
    notes: action.description ?? "",
  });
  if (action.action_id) {
    params.set("aiActionId", action.action_id);
  }
  return `/pacientes/${patientId}/problemas/nuevo?${params.toString()}`;
}

function clinicalEventPrefillHref(patientId: string, action: ClinicalIntentAction) {
  const params = new URLSearchParams({
    eventType: action.action_type === "add_pending" ? "care_plan" : "clinical_note",
    summary: action.label,
    details: action.description ?? "",
  });
  if (action.action_id) {
    params.set("aiActionId", action.action_id);
  }
  return `/pacientes/${patientId}/eventos?${params.toString()}`;
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

function SoapTextareaLike({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <label className="grid gap-2 text-sm font-medium">
      {label}
      <Textarea className="min-h-28" value={value} onChange={(event) => onChange(event.target.value)} />
    </label>
  );
}

function emptyToNull(value?: string | null) {
  const trimmed = value?.trim();
  return trimmed ? trimmed : null;
}

function fallbackActionToIntent(action: ClinicalIntentAction): ClinicalIntentType | null {
  const normalized = (action.action_id ?? action.label).toLocaleLowerCase("es-CL");
  if (normalized.includes("resumir")) return "summarize_patient";
  if (normalized.includes("cambio")) return "daily_changes";
  if (normalized.includes("evolucion") || normalized.includes("soap")) return "draft_soap";
  if (normalized.includes("fuentes")) return "show_sources";
  return null;
}

function aiStatusLabel(status?: AIProviderStatus, isError = false) {
  if (isError) return "degradada";
  if (!status) return "consultando";
  if (!status.enabled) return "apagada";
  if (!status.available) return "degradada";
  return "activa";
}

function groupRuleFindings(items: string[], intent: ClinicalIntentResponse) {
  const groups = [
    { label: "Signos vitales", items: [] as RuleFindingView[] },
    { label: "Examenes", items: [] as RuleFindingView[] },
    { label: "Medicacion", items: [] as RuleFindingView[] },
    { label: "Revision", items: [] as RuleFindingView[] },
    { label: "Otros", items: [] as RuleFindingView[] },
  ];
  for (const item of items) {
    const normalized = item.toLocaleLowerCase("es-CL");
    const view = {
      text: item,
      status: ruleFindingStatus(item),
      source: ruleFindingSource(item, intent),
    };
    if (
      normalized.includes("temperatura") ||
      normalized.includes("frecuencia cardiaca") ||
      normalized.includes("presion") ||
      normalized.includes("saturacion")
    ) {
      groups[0].items.push(view);
    } else if (
      normalized.includes("examen") ||
      normalized.includes("creatinina") ||
      normalized.includes("pcr") ||
      normalized.includes("hemoglobina")
    ) {
      groups[1].items.push(view);
    } else if (
      normalized.includes("medicamento") ||
      normalized.includes("medicacion") ||
      normalized.includes("dosis")
    ) {
      groups[2].items.push(view);
    } else if (normalized.includes("revisar") || normalized.includes("sin problema")) {
      groups[3].items.push(view);
    } else {
      groups[4].items.push(view);
    }
  }
  return groups.filter((group) => group.items.length > 0);
}

type RuleFindingView = {
  text: string;
  status: "mejora" | "empeora" | "revisar" | "observado";
  source: string;
};

function ruleFindingStatus(item: string): RuleFindingView["status"] {
  const normalized = item.toLocaleLowerCase("es-CL");
  if (
    normalized.includes("revisar") ||
    normalized.includes("sin problema") ||
    normalized.includes("sin dosis") ||
    normalized.includes("sin frecuencia") ||
    normalized.includes("medicacion")
  ) {
    return "revisar";
  }
  if (
    normalized.includes("creatinina subio") ||
    normalized.includes("hemoglobina bajo") ||
    normalized.includes("saturacion o2 bajo") ||
    normalized.includes("temperatura subio") ||
    normalized.includes("pcr subio")
  ) {
    return "empeora";
  }
  if (
    normalized.includes("saturacion o2 subio") ||
    normalized.includes("temperatura bajo") ||
    normalized.includes("pcr bajo")
  ) {
    return "mejora";
  }
  return "observado";
}

function ruleFindingSource(item: string, intent: ClinicalIntentResponse) {
  const matchedSource = intent.sources.find((source) => hasTokenOverlap(item, source.label));
  if (matchedSource) {
    return `${matchedSource.source_type}: ${matchedSource.label}`;
  }

  const matchedNewItem = intent.change_set?.new_items.find((newItem) => hasTokenOverlap(item, newItem));
  if (matchedNewItem) {
    return `clinical_event: ${matchedNewItem}`;
  }

  const normalized = normalizeClinicalText(item);
  if (
    normalized.includes("temperatura") ||
    normalized.includes("frecuencia cardiaca") ||
    normalized.includes("presion") ||
    normalized.includes("saturacion")
  ) {
    return "signos vitales: ultimos dos controles estructurados";
  }
  if (
    normalized.includes("examen") ||
    normalized.includes("creatinina") ||
    normalized.includes("pcr") ||
    normalized.includes("hemoglobina")
  ) {
    return "clinical_event: exam_result estructurado";
  }
  if (
    normalized.includes("medicamento") ||
    normalized.includes("medicacion") ||
    normalized.includes("dosis") ||
    normalized.includes("frecuencia")
  ) {
    return "clinical_event/medication: medicacion estructurada";
  }
  return "contexto clinico estructurado";
}

function hasTokenOverlap(left: string, right: string) {
  const rightTokens = new Set(meaningfulTokens(right));
  return meaningfulTokens(left).some((token) => rightTokens.has(token));
}

function meaningfulTokens(value: string) {
  return normalizeClinicalText(value)
    .replace(/[^a-z0-9\s]/g, " ")
    .split(/\s+/)
    .filter((token) => token.length >= 4);
}

function normalizeClinicalText(value: string) {
  return value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLocaleLowerCase("es-CL");
}

function formatDate(value: string) {
  return new Date(value).toLocaleString("es-CL", { dateStyle: "short", timeStyle: "short" });
}
