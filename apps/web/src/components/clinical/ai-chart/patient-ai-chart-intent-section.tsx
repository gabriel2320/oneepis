"use client";

import { ClinicalSectionCard } from "@/components/clinical/cards";
import type {
  AIProviderStatus,
  AIStreamEvent,
  ClinicalIntentAction,
  ClinicalIntentResponse,
  ClinicalIntentRouteResponse,
  ClinicalIntentType,
  ClinicalReviewItem,
} from "@/lib/types";

import { ClinicalIntentCommandBar } from "./clinical-intent-command-bar";
import { ClinicalIntentResultPanel } from "./clinical-intent-result-panel";

type PatientAiChartIntentSectionProps = {
  routerText: string;
  routedIntent: ClinicalIntentRouteResponse | null;
  aiStatus?: AIProviderStatus;
  aiStatusIsError: boolean;
  canUseAi: boolean;
  isRouting: boolean;
  isExecuting: boolean;
  hasRouteError: boolean;
  routeEvents: AIStreamEvent[];
  isStreamingRoutePreview: boolean;
  hasRoutePreviewError: boolean;
  hasIntentError: boolean;
  patientId: string;
  intent: ClinicalIntentResponse | null;
  isDecidingReviewItem: boolean;
  reviewDecisionMessage: string | null;
  isDecidingAction: boolean;
  actionDecisionMessage: string | null;
  onRouterTextChange: (value: string) => void;
  onRoute: () => void;
  onExecuteIntent: (intentType: ClinicalIntentType) => void;
  onDecideReviewItem: (item: ClinicalReviewItem, decision: "accepted" | "rejected") => void;
  onDecideAction: (action: ClinicalIntentAction) => void;
};

export function PatientAiChartIntentSection({
  routerText,
  routedIntent,
  aiStatus,
  aiStatusIsError,
  canUseAi,
  isRouting,
  isExecuting,
  hasRouteError,
  routeEvents,
  isStreamingRoutePreview,
  hasRoutePreviewError,
  hasIntentError,
  patientId,
  intent,
  isDecidingReviewItem,
  reviewDecisionMessage,
  isDecidingAction,
  actionDecisionMessage,
  onRouterTextChange,
  onRoute,
  onExecuteIntent,
  onDecideReviewItem,
  onDecideAction,
}: PatientAiChartIntentSectionProps) {
  return (
    <ClinicalSectionCard
      title="Intenciones clinicas"
      description="Barra dirigida: interpreta frases clinicas y propone acciones seguras."
    >
      <ClinicalIntentCommandBar
        routerText={routerText}
        routedIntent={routedIntent}
        aiStatus={aiStatus}
        aiStatusIsError={aiStatusIsError}
        canUseAi={canUseAi}
        isRouting={isRouting}
        isExecuting={isExecuting}
        hasRouteError={hasRouteError}
        routeEvents={routeEvents}
        isStreamingRoutePreview={isStreamingRoutePreview}
        hasRoutePreviewError={hasRoutePreviewError}
        hasIntentError={hasIntentError}
        patientId={patientId}
        onRouterTextChange={onRouterTextChange}
        onRoute={onRoute}
        onExecuteIntent={onExecuteIntent}
      />
      {intent ? (
        <ClinicalIntentResultPanel
          intent={intent}
          patientId={patientId}
          onDecideReviewItem={onDecideReviewItem}
          isDecidingReviewItem={isDecidingReviewItem}
          reviewDecisionMessage={reviewDecisionMessage}
          onDecideAction={onDecideAction}
          isDecidingAction={isDecidingAction}
          actionDecisionMessage={actionDecisionMessage}
        />
      ) : null}
    </ClinicalSectionCard>
  );
}
