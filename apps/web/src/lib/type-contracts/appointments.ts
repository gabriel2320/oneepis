export type AppointmentStatus =
  | "scheduled"
  | "check_in"
  | "in_progress"
  | "completed"
  | "cancelled"
  | "no_show";

export type ClinicalAppointment = {
  id: string;
  patient_id: string;
  starts_at: string;
  ends_at?: string | null;
  reason: string;
  location_label?: string | null;
  clinician_label?: string | null;
  notes?: string | null;
  status: AppointmentStatus;
  created_by: string;
  created_at: string;
  updated_at: string;
};

export type ClinicalAppointmentCreate = {
  starts_at: string;
  ends_at?: string | null;
  reason: string;
  location_label?: string | null;
  clinician_label?: string | null;
  notes?: string | null;
  status?: AppointmentStatus;
};

export type ClinicalAppointmentUpdate = Partial<ClinicalAppointmentCreate>;
