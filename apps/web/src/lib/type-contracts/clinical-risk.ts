import type { RecordStatus } from "./clinical-record";

export type ClinicalRiskType =
  | "fall"
  | "pressure_injury"
  | "vte"
  | "isolation"
  | "adverse_event"
  | "other";

export type ClinicalRiskSeverity = "low" | "moderate" | "high" | "critical" | "unknown";

export type ClinicalRiskSourceKind =
  | "manual"
  | "vital_sign"
  | "clinical_event"
  | "clinical_entry"
  | "lab_result";

export type ClinicalRiskCreate = {
  encounter_id?: string | null;
  risk_type: ClinicalRiskType;
  severity?: ClinicalRiskSeverity;
  source_kind?: ClinicalRiskSourceKind;
  source_ref?: string | null;
  reason: string;
  human_action?: string | null;
  reviewed_at?: string | null;
};

export type ClinicalRiskUpdate = Partial<ClinicalRiskCreate> & {
  status?: RecordStatus | null;
};

export type ClinicalRisk = {
  id: string;
  patient_id: string;
  encounter_id?: string | null;
  risk_type: ClinicalRiskType;
  severity: ClinicalRiskSeverity;
  status: RecordStatus;
  source_kind: ClinicalRiskSourceKind;
  source_ref?: string | null;
  reason: string;
  human_action?: string | null;
  reviewed_at?: string | null;
  created_by: string;
  created_at: string;
  updated_at: string;
};
