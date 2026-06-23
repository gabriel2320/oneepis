import type { Patient } from "./patient";

export type ClinicalEntryKind =
  | "intake"
  | "progress"
  | "discharge_summary"
  | "lab_result"
  | "prescription"
  | "procedure"
  | "note";
export type ClinicalEntryStatus = "draft" | "signed" | "amended";
export type ClinicalEventType =
  | "symptom"
  | "vital_sign"
  | "exam_result"
  | "diagnosis"
  | "medication"
  | "procedure"
  | "clinical_note"
  | "care_plan"
  | "administrative";
export type ClinicalEventSourceType = "manual" | "clinical_entry" | "vital_sign" | "imported_document" | "ai_draft";
export type RecordStatus = "active" | "inactive" | "resolved" | "entered_in_error";
export type AllergySeverity = "mild" | "moderate" | "severe" | "unknown";
export type EncounterType = "ambulatory" | "hospitalization" | "emergency" | "unknown";
export type EncounterStatus = "scheduled" | "in_progress" | "completed" | "cancelled";

export type ClinicalEntry = {
  id: string;
  patient_id: string;
  encounter_id?: string | null;
  kind: ClinicalEntryKind;
  status: ClinicalEntryStatus;
  occurred_at: string;
  title: string;
  subjective?: string | null;
  objective?: string | null;
  assessment?: string | null;
  plan?: string | null;
  tags: string[];
  created_by: string;
  created_at: string;
  updated_at: string;
};

export type ClinicalEntryCreate = {
  encounter_id?: string | null;
  kind: ClinicalEntryKind;
  status?: ClinicalEntryStatus;
  occurred_at: string;
  title: string;
  subjective?: string | null;
  objective?: string | null;
  assessment?: string | null;
  plan?: string | null;
  tags?: string[];
  extra_data?: Record<string, unknown>;
  created_by?: string;
};

export type ClinicalEntryUpdate = Partial<
  Pick<
    ClinicalEntryCreate,
    "status" | "occurred_at" | "title" | "subjective" | "objective" | "assessment" | "plan" | "tags"
  >
>;

export type ClinicalEvent = {
  id: string;
  patient_id: string;
  encounter_id?: string | null;
  event_type: ClinicalEventType;
  occurred_at: string;
  summary: string;
  source_type: ClinicalEventSourceType;
  source_ref?: string | null;
  payload: Record<string, unknown>;
  created_by: string;
  created_at: string;
  updated_at: string;
};

export type ClinicalEventCreate = {
  encounter_id?: string | null;
  event_type: ClinicalEventType;
  occurred_at: string;
  summary: string;
  source_type?: ClinicalEventSourceType;
  source_ref?: string | null;
  payload?: Record<string, unknown>;
  created_by?: string;
};

export type ClinicalEventUpdate = Partial<ClinicalEventCreate>;

export type ClinicalTimeline = {
  events: ClinicalEvent[];
  entries: ClinicalEntry[];
};
export type VitalSignCreate = {
  measured_at: string;
  temperature_c?: string | null;
  systolic_bp?: number | null;
  diastolic_bp?: number | null;
  heart_rate_bpm?: number | null;
  respiratory_rate_bpm?: number | null;
  oxygen_saturation_pct?: string | null;
  notes?: string | null;
};

export type VitalSign = {
  id: string;
  patient_id: string;
  measured_at: string;
  temperature_c?: string | null;
  systolic_bp?: number | null;
  diastolic_bp?: number | null;
  heart_rate_bpm?: number | null;
  respiratory_rate_bpm?: number | null;
  oxygen_saturation_pct?: string | null;
  notes?: string | null;
  created_at: string;
  updated_at: string;
};

export type VitalSignUpdate = Partial<VitalSignCreate>;

export type AllergyCreate = {
  substance: string;
  reaction?: string | null;
  severity?: AllergySeverity;
  status?: RecordStatus;
  recorded_at: string;
};

export type Allergy = {
  id: string;
  patient_id: string;
  substance: string;
  reaction?: string | null;
  severity: AllergySeverity;
  status: RecordStatus;
  recorded_at: string;
  created_at: string;
  updated_at: string;
};

export type AllergyUpdate = Partial<AllergyCreate>;

export type MedicationCreate = {
  catalog_item_id?: string | null;
  name: string;
  dose?: string | null;
  route?: string | null;
  frequency?: string | null;
  status?: RecordStatus;
  started_on?: string | null;
  ended_on?: string | null;
  dose_override_reason?: string | null;
};

export type MedicationRead = {
  id: string;
  patient_id: string;
  catalog_item_id?: string | null;
  name: string;
  dose?: string | null;
  route?: string | null;
  frequency?: string | null;
  status: RecordStatus;
  started_on?: string | null;
  ended_on?: string | null;
  dose_check_snapshot: Record<string, unknown>;
  dose_override_reason?: string | null;
  created_at: string;
  updated_at: string;
};

export type Medication = MedicationRead;

export type MedicationUpdate = Partial<MedicationCreate>;

export type ActiveProblemCreate = {
  title: string;
  code_system?: string | null;
  code?: string | null;
  status?: RecordStatus;
  onset_date?: string | null;
  resolved_on?: string | null;
  notes?: string | null;
};

export type ActiveProblem = {
  id: string;
  patient_id: string;
  title: string;
  code_system?: string | null;
  code?: string | null;
  status: RecordStatus;
  onset_date?: string | null;
  resolved_on?: string | null;
  notes?: string | null;
  created_at: string;
  updated_at: string;
};

export type ActiveProblemUpdate = Partial<ActiveProblemCreate>;

export type ClinicalEncounterCreate = {
  type?: EncounterType;
  status?: EncounterStatus;
  reason: string;
  started_at: string;
  ended_at?: string | null;
  location_label?: string | null;
  notes?: string | null;
};

export type ClinicalEncounter = {
  id: string;
  patient_id: string;
  type: EncounterType;
  status: EncounterStatus;
  reason: string;
  started_at: string;
  ended_at?: string | null;
  location_label?: string | null;
  notes?: string | null;
  created_at: string;
  updated_at: string;
};

export type ClinicalEncounterUpdate = Partial<ClinicalEncounterCreate>;
export type PatientRecordSnapshot = {
  patient: Patient;
  latest_vitals?: VitalSign | null;
  active_allergies: Allergy[];
  active_medications: Medication[];
  active_problems: ActiveProblem[];
  recent_entries: ClinicalEntry[];
};

export type AuditEvent = {
  id: string;
  action: string;
  entity_type: string;
  entity_id?: string | null;
  actor_id: string;
  correlation_id?: string | null;
  request_method?: string | null;
  request_path?: string | null;
  extra_data: Record<string, unknown>;
  created_at: string;
};

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
