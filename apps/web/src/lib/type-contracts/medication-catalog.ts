import type { Medication } from "./clinical-record";

export type MedicationCatalogStatus = "available" | "unavailable" | "draft";
export type MedicationSourceSystem =
  | "local_curated"
  | "fda_openfda_label"
  | "fda_drugsfda"
  | "fda_enforcement"
  | "fda_faers"
  | "isp_anamed";
export type MedicationSourceReviewStatus = "draft" | "reviewed" | "deprecated";
export type MedicationDoseSeverity = "info" | "warning" | "critical";

export type MedicationSourceReference = {
  source_system: MedicationSourceSystem;
  source_label: string;
  source_url?: string | null;
  external_id?: string | null;
  source_version?: string | null;
  retrieved_at?: string | null;
  reviewed_at?: string | null;
  review_status: MedicationSourceReviewStatus;
};

export type MedicationDoseRuleRead = {
  id: string;
  catalog_item_id: string;
  source_system: MedicationSourceSystem;
  source_label: string;
  source_url?: string | null;
  external_id?: string | null;
  source_version?: string | null;
  retrieved_at?: string | null;
  reviewed_at?: string | null;
  review_status: MedicationSourceReviewStatus;
  population: string;
  route?: string | null;
  unit?: string | null;
  min_value?: string | null;
  max_value?: string | null;
  frequency_text?: string | null;
  usual_dose_text?: string | null;
  avoid_dose_text?: string | null;
  severity: MedicationDoseSeverity;
  created_at: string;
  updated_at: string;
};

export type MedicationCatalogItemRead = {
  id: string;
  source_system: MedicationSourceSystem;
  source_label: string;
  source_url?: string | null;
  external_id?: string | null;
  source_version?: string | null;
  retrieved_at?: string | null;
  reviewed_at?: string | null;
  review_status: MedicationSourceReviewStatus;
  display_name: string;
  generic_name: string;
  form?: string | null;
  strength?: string | null;
  route?: string | null;
  status: MedicationCatalogStatus;
  tags: string[];
  dose_rules: MedicationDoseRuleRead[];
  created_at: string;
  updated_at: string;
};

export type MedicationCatalogItem = MedicationCatalogItemRead;

export type MedicationDoseWarning = {
  severity: MedicationDoseSeverity;
  message: string;
  requires_override: boolean;
  rule_id?: string | null;
  source?: MedicationSourceReference | null;
};

export type MedicationDraftValidationRequest = {
  catalog_item_id?: string | null;
  name: string;
  dose?: string | null;
  route?: string | null;
  frequency?: string | null;
};

export type MedicationDraftValidationResponse = {
  warnings: MedicationDoseWarning[];
  blocking: boolean;
  limitations: string[];
  source_refs: MedicationSourceReference[];
  normalized_dose: Record<string, unknown>;
  applies_changes: false;
};

export type MedicationDraftingContext = {
  active_medications: Medication[];
  recent_medications: Medication[];
  previous_day_indication_texts: string[];
  suggested_catalog_items: MedicationCatalogItem[];
  limitations: string[];
  applies_changes: false;
};
