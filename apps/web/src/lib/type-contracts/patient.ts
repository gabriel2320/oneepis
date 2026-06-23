export type SexAtBirth = "female" | "male" | "intersex" | "unknown";
export type PatientClinicalStatus = "draft" | "active" | "closed" | "archived";
export type CareContext = "ambulatory" | "hospitalized" | "unknown";

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
