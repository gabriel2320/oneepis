from __future__ import annotations

import enum


class ClinicalEntryKind(enum.StrEnum):
    INTAKE = "intake"
    PROGRESS = "progress"
    DISCHARGE_SUMMARY = "discharge_summary"
    LAB_RESULT = "lab_result"
    PRESCRIPTION = "prescription"
    PROCEDURE = "procedure"
    NOTE = "note"


class ClinicalEntryStatus(enum.StrEnum):
    DRAFT = "draft"
    SIGNED = "signed"
    AMENDED = "amended"


class ClinicalEventType(enum.StrEnum):
    SYMPTOM = "symptom"
    VITAL_SIGN = "vital_sign"
    EXAM_RESULT = "exam_result"
    DIAGNOSIS = "diagnosis"
    MEDICATION = "medication"
    PROCEDURE = "procedure"
    CLINICAL_NOTE = "clinical_note"
    CARE_PLAN = "care_plan"
    ADMINISTRATIVE = "administrative"


class ClinicalEventSourceType(enum.StrEnum):
    MANUAL = "manual"
    CLINICAL_ENTRY = "clinical_entry"
    VITAL_SIGN = "vital_sign"
    IMPORTED_DOCUMENT = "imported_document"
    AI_DRAFT = "ai_draft"


class AllergySeverity(enum.StrEnum):
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"
    UNKNOWN = "unknown"


class RecordStatus(enum.StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    RESOLVED = "resolved"
    ENTERED_IN_ERROR = "entered_in_error"


class EncounterType(enum.StrEnum):
    AMBULATORY = "ambulatory"
    HOSPITALIZATION = "hospitalization"
    EMERGENCY = "emergency"
    UNKNOWN = "unknown"


class EncounterStatus(enum.StrEnum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class EncounterWorkflowKind(enum.StrEnum):
    GENERAL = "general"
    AMBULATORY_PRECONSULT = "ambulatory_preconsult"
    AMBULATORY_VISIT = "ambulatory_visit"
    HOSPITALIZATION_ADMISSION = "hospitalization_admission"
    HOSPITALIZATION_DAILY = "hospitalization_daily"
    HOSPITALIZATION_DISCHARGE = "hospitalization_discharge"
