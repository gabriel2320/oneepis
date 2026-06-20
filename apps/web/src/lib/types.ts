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

export type Patient = {
  id: string;
  first_name: string;
  last_name: string;
  preferred_name?: string | null;
  birth_date: string;
  sex_at_birth: SexAtBirth;
  clinical_identifier?: string | null;
  created_at: string;
  updated_at: string;
};

export type ClinicalEntry = {
  id: string;
  patient_id: string;
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
};

export type Allergy = {
  id: string;
  patient_id: string;
  substance: string;
  reaction?: string | null;
  severity: "mild" | "moderate" | "severe" | "unknown";
  status: RecordStatus;
};

export type Medication = {
  id: string;
  patient_id: string;
  name: string;
  dose?: string | null;
  route?: string | null;
  frequency?: string | null;
  status: RecordStatus;
};

export type PatientRecordSnapshot = {
  patient: Patient;
  latest_vitals?: VitalSign | null;
  active_allergies: Allergy[];
  active_medications: Medication[];
  recent_entries: ClinicalEntry[];
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

export type AIProviderStatus = {
  provider: string;
  enabled: boolean;
  available: boolean;
  model?: string | null;
  base_url?: string | null;
  available_models: string[];
  message: string;
};
