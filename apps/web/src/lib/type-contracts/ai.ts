import type { ClinicalEntry, ClinicalEvent, ClinicalEventType } from "./clinical-record";

export type DraftSoapFromEventsRequest = {
  clinical_event_ids: string[];
  encounter_id?: string | null;
};

export type DraftSoapFromEventsResponse = {
  title: string;
  subjective: string;
  objective: string;
  assessment: string;
  plan: string;
  sources: { clinical_event_id: string; label: string }[];
  section_sources: {
    section: "subjective" | "objective" | "assessment" | "plan";
    source_type: string;
    source_id?: string | null;
    label: string;
    reason: string;
  }[];
  warnings: string[];
  ai_available: boolean;
  provider: string;
  requires_human_confirmation: true;
};

export type EventProposalFromEntryRequest = {
  entry_id: string;
  max_proposals?: number;
};

export type ClinicalPatchOperation = {
  op: "add" | "replace" | "annotate";
  path: string;
  value?: unknown;
  reason: string;
};

export type ClinicalPatch = {
  patch_id: string;
  target: "clinical_event" | "evolution" | "problem" | "medication" | "document";
  mode: "draft" | "suggestion";
  operations: ClinicalPatchOperation[];
  sources: { source_type: string; source_id?: string | null; label: string }[];
  warnings: string[];
  requires_human_confirmation: true;
};

export type ConfirmClinicalPatchRequest = {
  decision: "accepted" | "rejected";
  patch: ClinicalPatch;
  note?: string | null;
};

export type ConfirmClinicalPatchResponse = {
  decision: "accepted" | "rejected";
  audited: boolean;
  applies_changes: boolean;
  clinical_event?: ClinicalEvent | null;
  clinical_entry?: ClinicalEntry | null;
  message: string;
};

export type EventProposalFromEntry = {
  proposal_id: string;
  event_type: ClinicalEventType;
  occurred_at: string;
  summary: string;
  source_type: "clinical_entry";
  source_ref: string;
  payload: Record<string, unknown>;
  evidence_label: string;
  patch: ClinicalPatch;
  requires_human_confirmation: true;
};

export type EventProposalsFromEntryResponse = {
  entry_id: string;
  entry_title: string;
  proposals: EventProposalFromEntry[];
  warnings: string[];
  applies_changes: false;
  requires_human_confirmation: true;
};

export type ClinicalIntentType =
  | "summarize_patient"
  | "daily_changes"
  | "active_problems"
  | "timeline"
  | "draft_soap"
  | "show_sources";

export type ClinicalIntentMode = "read" | "draft" | "structured_proposal" | "human_confirmation";

export type ClinicalIntentRequest = {
  intent_type: ClinicalIntentType;
  mode?: ClinicalIntentMode;
  focus?: string | null;
  max_events?: number;
};

export type ClinicalIntentRouteRequest = {
  text: string;
  max_events?: number;
};

export type ClinicalIntentRouteResponse = {
  recognized: boolean;
  original_text: string;
  intent_type?: ClinicalIntentType | null;
  mode: ClinicalIntentMode;
  confidence: "high" | "moderate" | "low";
  explanation: string;
  suggested_actions: {
    action_type: "create_event" | "create_soap_draft" | "review_sources" | "add_pending" | "none";
    action_id?: string | null;
    label: string;
    description?: string | null;
    confirmation_label?: string | null;
    requires_confirmation: boolean;
  }[];
  fallback_options: {
    action_type: "create_event" | "create_soap_draft" | "review_sources" | "add_pending" | "none";
    action_id?: string | null;
    label: string;
    description?: string | null;
    confirmation_label?: string | null;
    requires_confirmation: boolean;
  }[];
};

export type AIStreamEvent =
  | { type: "status"; message: string }
  | { type: "source"; sourceId?: string | null; label: string }
  | { type: "warning"; message: string }
  | { type: "proposal"; data: ClinicalIntentRouteResponse }
  | { type: "done" }
  | { type: "error"; message: string };

export type ClinicalReviewItem = {
  item_type:
    | "missing_medication_dose"
    | "missing_medication_frequency"
    | "unstructured_medication_event"
    | "unlinked_medication_event";
  label: string;
  detail: string;
  severity: "info" | "warning" | "critical";
  source_type: string;
  source_id?: string | null;
  suggested_action: string;
  decision_status: "pending" | "accepted" | "rejected";
  decision_actor_id?: string | null;
  decision_at?: string | null;
  decision_audit_event_id?: string | null;
};

export type ClinicalReviewItemDecisionRequest = {
  decision: "accepted" | "rejected";
  item_type: ClinicalReviewItem["item_type"];
  label: string;
  detail: string;
  source_type: string;
  source_id?: string | null;
  note?: string | null;
};

export type ClinicalReviewItemDecisionResponse = {
  decision: "accepted" | "rejected";
  audited: boolean;
  message: string;
};

export type ClinicalIntentAction = {
  action_type: "create_event" | "create_soap_draft" | "review_sources" | "add_pending" | "none";
  action_id?: string | null;
  label: string;
  description?: string | null;
  confirmation_label?: string | null;
  requires_confirmation: boolean;
};

export type ClinicalIntentActionDecisionRequest = {
  decision: "reviewed" | "accepted" | "rejected";
  action_type: ClinicalIntentAction["action_type"];
  label: string;
  action_id?: string | null;
  description?: string | null;
  requires_confirmation: boolean;
  note?: string | null;
};

export type ClinicalIntentActionDecisionResponse = {
  decision: "reviewed" | "accepted" | "rejected";
  audited: boolean;
  applies_changes: boolean;
  message: string;
};

export type ClinicalIntentResponse = {
  intent_type: string;
  mode: string;
  clinical_answer: string;
  sources: { source_type: string; source_id?: string | null; label: string }[];
  certainty: "high" | "moderate" | "low";
  missing_data: string[];
  proposed_actions: ClinicalIntentAction[];
  evidence_marks: {
    label: string;
    status: "confirmed" | "inferred" | "missing" | "needs_review";
    detail: string;
    source_id?: string | null;
  }[];
  context_sections: { title: string; items: string[] }[];
  problem_contexts: {
    problem_id?: string | null;
    title: string;
    status: "structured" | "unlinked";
    evidence: {
      label: string;
      status: "confirmed" | "inferred" | "missing" | "needs_review";
      detail: string;
      source_id?: string | null;
    }[];
    pending: string[];
    explanations: string[];
  }[];
  change_set?: {
    baseline?: string | null;
    new_items: string[];
    rule_findings: string[];
    missing_for_comparison: string[];
  } | null;
  review_items: ClinicalReviewItem[];
  warnings: string[];
  requires_human_confirmation: boolean;
};
export type ClinicalInsightRequest = {
  patient_id?: string | null;
  source_text: string;
  focus: "summary" | "risks" | "next_steps";
};

export type ClinicalInsightResponse = {
  provider: string;
  status: "disabled" | "draft" | "error";
  model?: string | null;
  summary: string;
  structured_points: string[];
  safety_notes: string[];
};

export type AiTaskStatus = {
  task: "summary" | "suggestions" | "fallback" | "embeddings";
  model: string;
  available: boolean;
  enabled: boolean;
};

export type AIProviderStatus = {
  provider: string;
  enabled: boolean;
  available: boolean;
  model?: string | null;
  summary_model?: string | null;
  suggestions_model?: string | null;
  fallback_model?: string | null;
  embeddings_model?: string | null;
  base_url?: string | null;
  available_models: string[];
  tasks: AiTaskStatus[];
  message: string;
};

export type PatientAiSuggestionRequest = {
  focus: "summary" | "safety" | "documentation";
};

export type ClinicalAiSuggestion = {
  title: string;
  detail: string;
  severity: "info" | "warning" | "critical";
  source: "ollama" | "local_rules";
  action_label?: string | null;
};

export type PatientAiSuggestionsResponse = {
  provider: string;
  status: "disabled" | "draft" | "error";
  model?: string | null;
  patient_id: string;
  generated_at: string;
  summary: string;
  suggestions: ClinicalAiSuggestion[];
  safety_notes: string[];
};
