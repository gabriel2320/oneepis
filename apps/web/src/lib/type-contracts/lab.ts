import type { ClinicalEventSourceType, RecordStatus } from "./clinical-record";

export type LabResultFlag = "low" | "normal" | "high" | "critical" | "abnormal" | "unknown";

export type LabResultCreate = {
  code?: string | null;
  name: string;
  value?: string | null;
  numeric_value?: string | number | null;
  unit?: string | null;
  reference_range?: string | null;
  flag?: LabResultFlag;
  status?: RecordStatus;
  notes?: string | null;
};

export type LabResultUpdate = {
  code?: string | null;
  name?: string | null;
  value?: string | null;
  numeric_value?: string | number | null;
  unit?: string | null;
  reference_range?: string | null;
  flag?: LabResultFlag | null;
  status?: RecordStatus | null;
  notes?: string | null;
};

export type LabResultSourceRead = {
  source_type: ClinicalEventSourceType;
  source_ref?: string | null;
  panel_id: string;
  panel_name: string;
  request_path: string;
  label: string;
};

export type LabResultRead = {
  id: string;
  panel_id: string;
  patient_id: string;
  code?: string | null;
  name: string;
  value?: string | null;
  numeric_value?: string | number | null;
  unit?: string | null;
  reference_range?: string | null;
  flag: LabResultFlag;
  status: RecordStatus;
  notes?: string | null;
  source: LabResultSourceRead;
  created_at: string;
  updated_at: string;
};

export type LabResult = LabResultRead;

export type LabPanelCreate = {
  encounter_id?: string | null;
  occurred_at: string;
  panel_name: string;
  source_type?: ClinicalEventSourceType;
  source_ref?: string | null;
  status?: RecordStatus;
  summary?: string | null;
  created_by?: string;
  results: LabResultCreate[];
};

export type LabPanelUpdate = {
  encounter_id?: string | null;
  occurred_at?: string | null;
  panel_name?: string | null;
  source_type?: ClinicalEventSourceType | null;
  source_ref?: string | null;
  status?: RecordStatus | null;
  summary?: string | null;
};

export type LabPanelRead = {
  id: string;
  patient_id: string;
  encounter_id?: string | null;
  occurred_at: string;
  panel_name: string;
  source_type: ClinicalEventSourceType;
  source_ref?: string | null;
  status: RecordStatus;
  summary?: string | null;
  created_by: string;
  results: LabResult[];
  created_at: string;
  updated_at: string;
};

export type LabPanel = LabPanelRead;
