import type { ClinicalEncounter } from "./clinical-record";
import type { Patient } from "./patient";

export type HospitalBedStatus = "available" | "occupied" | "cleaning" | "blocked";
export type HospitalDailySheetStatus = "draft" | "closed";
export type HospitalIndicationStatus = "draft" | "closed";
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
  status: HospitalDailySheetStatus;
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
  status?: HospitalDailySheetStatus;
  clinical_summary: string;
  overnight_events?: string | null;
  active_plan?: string | null;
  pending_tasks?: string | null;
  safety_notes?: string | null;
};

export type HospitalDailySheetUpdate = Partial<HospitalDailySheetCreate>;

export type HospitalIndication = {
  id: string;
  patient_id: string;
  encounter_id: string;
  status: HospitalIndicationStatus;
  indicated_at: string;
  title: string;
  indication_text: string;
  rationale?: string | null;
  safety_notes?: string | null;
  created_by: string;
  created_at: string;
  updated_at: string;
};

export type HospitalIndicationCreate = {
  status?: HospitalIndicationStatus;
  indicated_at: string;
  title: string;
  indication_text: string;
  rationale?: string | null;
  safety_notes?: string | null;
};

export type HospitalIndicationUpdate = Partial<HospitalIndicationCreate>;
