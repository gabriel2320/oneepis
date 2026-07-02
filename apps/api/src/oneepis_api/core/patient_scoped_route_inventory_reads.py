from typing import Literal

from oneepis_api.core.patient_scoped_route_inventory_types import PatientScopedRoute


def _read(
    method: Literal["GET", "POST"],
    path_template: str,
    surface: str,
    patient_scoped: bool = True,
) -> PatientScopedRoute:
    return PatientScopedRoute(
        method, path_template, surface, patient_scoped, True, True, False, False, False
    )


def _audited_read(
    method: Literal["GET"],
    path_template: str,
    surface: str,
) -> PatientScopedRoute:
    return PatientScopedRoute(
        method, path_template, surface, True, True, False, False, False, False
    )


def _patient_write(
    method: Literal["PATCH"],
    path_template: str,
    surface: str,
) -> PatientScopedRoute:
    return PatientScopedRoute(
        method, path_template, surface, True, False, False, False, False, False
    )


PATIENT_SCOPED_READ_ROUTES: tuple[PatientScopedRoute, ...] = (
    _read("GET", "/api/v1/patients", "patients_index", patient_scoped=False),
    _read("GET", "/api/v1/patients/{patient_id}", "patient"),
    _patient_write("PATCH", "/api/v1/patients/{patient_id}", "patient"),
    _read("GET", "/api/v1/patients/{patient_id}/record", "patient_record"),
    _read("GET", "/api/v1/patients/{patient_id}/context", "patient_context"),
    _read("GET", "/api/v1/patients/{patient_id}/appointments", "appointments"),
    _read("GET", "/api/v1/patients/{patient_id}/appointments/{appointment_id}", "appointments"),
    _read("GET", "/api/v1/patients/{patient_id}/allergies", "allergies"),
    _read("GET", "/api/v1/patients/{patient_id}/allergies/{allergy_id}", "allergies"),
    _read("GET", "/api/v1/patients/{patient_id}/problems", "active_problems"),
    _read("GET", "/api/v1/patients/{patient_id}/problems/{problem_id}", "active_problems"),
    _read("GET", "/api/v1/patients/{patient_id}/medications", "medications"),
    _read(
        "GET",
        "/api/v1/patients/{patient_id}/medications/{medication_id}",
        "medications",
    ),
    _read(
        "GET",
        "/api/v1/patients/{patient_id}/medication-drafting-context",
        "medication_drafting_context",
    ),
    _read(
        "POST",
        "/api/v1/patients/{patient_id}/medications/validate-draft",
        "medication_drafting_context",
    ),
    _read("GET", "/api/v1/patients/{patient_id}/encounters", "encounters"),
    _read("GET", "/api/v1/patients/{patient_id}/encounters/{encounter_id}", "encounters"),
    _read("GET", "/api/v1/patients/{patient_id}/clinical-entries", "clinical_entries"),
    _read(
        "GET",
        "/api/v1/patients/{patient_id}/clinical-entries/{entry_id}",
        "clinical_entries",
    ),
    _read("GET", "/api/v1/patients/{patient_id}/clinical-events", "clinical_events"),
    _read(
        "GET",
        "/api/v1/patients/{patient_id}/clinical-events/{event_id}",
        "clinical_events",
    ),
    _read("GET", "/api/v1/patients/{patient_id}/timeline", "clinical_timeline"),
    _read("GET", "/api/v1/patients/{patient_id}/clinical-orders", "clinical_orders"),
    _read("GET", "/api/v1/patients/{patient_id}/clinical-risks", "clinical_risks"),
    _read(
        "GET",
        "/api/v1/patients/{patient_id}/clinical-risks/{risk_id}",
        "clinical_risks",
    ),
    _read("GET", "/api/v1/patients/{patient_id}/vital-signs", "vital_signs"),
    _read(
        "GET",
        "/api/v1/patients/{patient_id}/vital-signs/{vital_sign_id}",
        "vital_signs",
    ),
    _read("GET", "/api/v1/patients/{patient_id}/lab-panels", "lab_panels_results"),
    _read(
        "GET",
        "/api/v1/patients/{patient_id}/lab-panels/{panel_id}",
        "lab_panels_results",
    ),
    _read(
        "GET",
        "/api/v1/patients/{patient_id}/lab-panels/{panel_id}/results/{result_id}",
        "lab_panels_results",
    ),
    _audited_read("GET", "/api/v1/patients/{patient_id}/audit-events", "patient_audit"),
    _read("POST", "/api/v1/patients/{patient_id}/ai/suggestions", "patient_ai"),
    _read("POST", "/api/v1/patients/{patient_id}/ai/draft-soap-from-events", "patient_ai"),
    _read("POST", "/api/v1/patients/{patient_id}/ai/event-proposals-from-entry", "patient_ai"),
    _read("POST", "/api/v1/patients/{patient_id}/ai/confirm-clinical-patch", "patient_ai"),
    _read("POST", "/api/v1/patients/{patient_id}/ai/clinical-intent", "patient_ai"),
    _read("POST", "/api/v1/patients/{patient_id}/ai/clinical-intent-route", "patient_ai"),
    _read("POST", "/api/v1/patients/{patient_id}/ai/action-decision", "patient_ai"),
    _read("POST", "/api/v1/patients/{patient_id}/ai/review-item-decision", "patient_ai"),
    _read("GET", "/api/v1/patients/{patient_id}/assistant/timeline", "assistant_timeline"),
    _read("GET", "/api/v1/patients/{patient_id}/assistant/search", "assistant_search"),
    _read("POST", "/api/v1/patients/{patient_id}/assistant/chart", "assistant_chart"),
    _read(
        "POST",
        "/api/v1/patients/{patient_id}/assistant/correlate",
        "assistant_correlation",
    ),
    _read(
        "GET",
        "/api/v1/hospitalization/patients/{patient_id}/daily-sheets",
        "hospital_daily_sheets",
    ),
    _read(
        "GET",
        "/api/v1/hospitalization/patients/{patient_id}/indications",
        "hospital_indications",
    ),
    _read(
        "GET",
        "/api/v1/hospitalization/active",
        "active_hospitalization",
        patient_scoped=False,
    ),
)
