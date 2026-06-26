export type AssistantTimelineItemType =
  | "encounter"
  | "clinical_entry"
  | "clinical_event"
  | "vital_sign"
  | "medication"
  | "problem"
  | "allergy"
  | "lab_result";

export type AssistantTimelineItem = {
  item_type: AssistantTimelineItemType;
  item_id: string;
  occurred_at: string;
  label: string;
  summary: string;
  source_label: string;
  source_path: string;
  encounter_id?: string | null;
  encounter_type?: "ambulatory" | "hospitalization" | "emergency" | "unknown" | null;
  encounter_status?: "scheduled" | "in_progress" | "completed" | "cancelled" | null;
  scope: "ambulatory" | "hospitalization" | "emergency" | "longitudinal" | "unknown";
};

export type AssistantTimelineResponse = {
  patient_id: string;
  items: AssistantTimelineItem[];
  missing_data: string[];
  warnings: string[];
  limit: number;
  has_more: boolean;
  applies_changes: false;
};

export type AssistantSearchResult = {
  item_type: AssistantTimelineItemType;
  item_id: string;
  occurred_at: string;
  label: string;
  snippet: string;
  matched_fields: string[];
  source_label: string;
  source_path: string;
};

export type AssistantSearchResponse = {
  patient_id: string;
  query: string;
  results: AssistantSearchResult[];
  missing_data: string[];
  warnings: string[];
  limit: number;
  has_more: boolean;
  applies_changes: false;
};

export type AssistantChartRequest = {
  series?: string[];
  limit?: number;
};

export type AssistantChartPoint = {
  occurred_at: string;
  value: number;
  source_type: "vital_sign" | "clinical_event" | "lab_result";
  source_id: string;
  source_path: string;
  note?: string | null;
};

export type AssistantChartSeries = {
  key: string;
  label: string;
  unit?: string | null;
  source_label: string;
  points: AssistantChartPoint[];
};

export type AssistantChartResponse = {
  patient_id: string;
  series: AssistantChartSeries[];
  missing_data: string[];
  warnings: string[];
  limit: number;
  has_more: boolean;
  applies_changes: false;
};

export type AssistantCorrelationPreset =
  | "fever_infection"
  | "renal_medications"
  | "respiratory_oxygen"
  | "hemoglobin_bleeding"
  | "medication_changes";

export type AssistantCorrelationRequest = {
  presets?: AssistantCorrelationPreset[];
  limit?: number;
};

export type AssistantCorrelationEvidence = {
  source_type: "vital_sign" | "clinical_event" | "lab_result" | "medication";
  source_id: string;
  occurred_at: string;
  label: string;
  summary: string;
  source_path: string;
};

export type AssistantCorrelationResult = {
  preset: AssistantCorrelationPreset;
  label: string;
  summary: string;
  evidence: AssistantCorrelationEvidence[];
  missing_data: string[];
  warnings: string[];
};

export type AssistantCorrelationResponse = {
  patient_id: string;
  correlations: AssistantCorrelationResult[];
  missing_data: string[];
  warnings: string[];
  limit: number;
  has_more: boolean;
  applies_changes: false;
};
