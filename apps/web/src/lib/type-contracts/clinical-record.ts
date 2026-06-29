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
export type MedicationReadSourceSystem =
  | "local_curated"
  | "fda_openfda_label"
  | "fda_drugsfda"
  | "fda_enforcement"
  | "fda_faers"
  | "isp_anamed";
export type MedicationReadSourceReviewStatus = "draft" | "reviewed" | "deprecated";
export type MedicationMissingField = "dose" | "route" | "frequency" | "source";
export type EncounterWorkflowKind =
  | "general"
  | "ambulatory_preconsult"
  | "ambulatory_visit"
  | "hospitalization_admission"
  | "hospitalization_daily"
  | "hospitalization_discharge";

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

export type MedicationSourceRead = {
  source_system: MedicationReadSourceSystem;
  source_label: string;
  source_url?: string | null;
  external_id?: string | null;
  source_version?: string | null;
  retrieved_at?: string | null;
  reviewed_at?: string | null;
  review_status: MedicationReadSourceReviewStatus;
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
  source?: MedicationSourceRead | null;
  missing_fields: MedicationMissingField[];
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

export type HistoricalDiagnosis = {
  source_event_id: string;
  title: string;
  occurred_at: string;
  source_type: ClinicalEventSourceType;
  source_ref?: string | null;
  source_label: string;
  limit: string;
  code_system?: string | null;
  code?: string | null;
};

export type ClinicalEncounterCreate = {
  type?: EncounterType;
  status?: EncounterStatus;
  workflow_kind?: EncounterWorkflowKind;
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
  workflow_kind: EncounterWorkflowKind;
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
  historical_diagnoses: HistoricalDiagnosis[];
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
