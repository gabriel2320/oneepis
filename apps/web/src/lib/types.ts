export type SexAtBirth = "female" | "male" | "intersex" | "unknown";
export type ClinicalEntryKind =
  | "intake"
  | "progress"
  | "lab_result"
  | "prescription"
  | "procedure"
  | "note";
export type ClinicalEntryStatus = "draft" | "signed" | "amended";
export type RecordStatus = "active" | "inactive" | "resolved" | "entered_in_error";
export type AllergySeverity = "mild" | "moderate" | "severe" | "unknown";
export type UserRole = "admin" | "medico" | "enfermeria" | "solo_lectura" | "dev";
export type PatientClinicalStatus = "draft" | "active" | "closed" | "archived";
export type CareContext = "ambulatory" | "hospitalized" | "unknown";
export type EncounterType = "ambulatory" | "hospitalization" | "emergency" | "unknown";
export type EncounterStatus = "scheduled" | "in_progress" | "completed" | "cancelled";
export type HospitalBedStatus = "available" | "occupied" | "cleaning" | "blocked";

export type AuthUser = {
  email: string;
  name: string;
  roles: UserRole[];
  actor_id: string;
};

export type LoginRequest = {
  email: string;
  password: string;
};

export type LoginResponse = {
  access_token: string;
  token_type: "bearer";
  expires_at: string;
  user: AuthUser;
};

export type PatientCreate = {
  first_name: string;
  last_name: string;
  preferred_name?: string | null;
  birth_date: string;
  sex_at_birth: SexAtBirth;
  document_id_hash?: string | null;
  clinical_identifier?: string | null;
  clinical_status?: PatientClinicalStatus;
  current_care_context?: CareContext;
  contact_phone?: string | null;
  email?: string | null;
  emergency_contact?: Record<string, unknown>;
};

export type PatientUpdate = Partial<
  Pick<
    PatientCreate,
    | "first_name"
    | "last_name"
    | "preferred_name"
    | "contact_phone"
    | "email"
    | "emergency_contact"
    | "clinical_status"
    | "current_care_context"
  >
>;

export type Patient = {
  id: string;
  first_name: string;
  last_name: string;
  preferred_name?: string | null;
  birth_date: string;
  sex_at_birth: SexAtBirth;
  clinical_status: PatientClinicalStatus;
  current_care_context: CareContext;
  clinical_identifier?: string | null;
  created_at: string;
  updated_at: string;
};

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
  name: string;
  dose?: string | null;
  route?: string | null;
  frequency?: string | null;
  status?: RecordStatus;
  started_on?: string | null;
  ended_on?: string | null;
};

export type Medication = {
  id: string;
  patient_id: string;
  name: string;
  dose?: string | null;
  route?: string | null;
  frequency?: string | null;
  status: RecordStatus;
  started_on?: string | null;
  ended_on?: string | null;
  created_at: string;
  updated_at: string;
};

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

export type HospitalBed = {
  id: string;
  ward: string;
  room: string;
  bed_label: string;
  status: HospitalBedStatus;
  encounter_id?: string | null;
  notes?: string | null;
  created_at: string;
  updated_at: string;
};

export type HospitalBedCreate = {
  ward: string;
  room: string;
  bed_label: string;
  status?: HospitalBedStatus;
  encounter_id?: string | null;
  notes?: string | null;
};

export type HospitalBedUpdate = Partial<HospitalBedCreate>;

export type HospitalizationBoardItem = {
  patient: Patient;
  encounter: ClinicalEncounter;
  bed?: HospitalBed | null;
};

export type HospitalDailySheet = {
  id: string;
  patient_id: string;
  encounter_id: string;
  sheet_date: string;
  clinical_summary: string;
  overnight_events?: string | null;
  active_plan?: string | null;
  pending_tasks?: string | null;
  safety_notes?: string | null;
  created_by: string;
  created_at: string;
  updated_at: string;
};

export type HospitalDailySheetCreate = {
  sheet_date: string;
  clinical_summary: string;
  overnight_events?: string | null;
  active_plan?: string | null;
  pending_tasks?: string | null;
  safety_notes?: string | null;
};

export type HospitalDailySheetUpdate = Partial<HospitalDailySheetCreate>;

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
