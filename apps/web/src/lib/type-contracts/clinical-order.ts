export type ClinicalOrderStatus = "draft" | "cancelled" | "entered_in_error";
export type ClinicalOrderKind = "lab" | "imaging" | "nursing" | "other";

export type ClinicalOrder = {
  id: string;
  patient_id: string;
  encounter_id: string;
  status: ClinicalOrderStatus;
  kind: ClinicalOrderKind;
  ordered_at: string;
  title: string;
  order_text: string;
  rationale?: string | null;
  created_by: string;
  created_at: string;
  updated_at: string;
};
