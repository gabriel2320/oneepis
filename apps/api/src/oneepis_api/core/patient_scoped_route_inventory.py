from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class PatientScopedRoute:
    method: Literal["GET", "POST", "PATCH", "DELETE"]
    path_template: str
    surface: str
    patient_scoped: bool
    read_audit_required: bool
    read_abac_dev_only: bool
    write_surface: bool
    write_abac_dev_only: bool
    runtime_write_abac: bool


def _read(
    method: Literal["GET", "POST"],
    path_template: str,
    surface: str,
    patient_scoped: bool = True,
) -> PatientScopedRoute:
    return PatientScopedRoute(
        method, path_template, surface, patient_scoped, True, True, False, False, False
    )


def _write(
    method: Literal["POST", "PATCH", "DELETE"],
    path_template: str,
    surface: str,
    write_abac_dev_only: bool = False,
) -> PatientScopedRoute:
    return PatientScopedRoute(
        method,
        path_template,
        surface,
        True,
        False,
        False,
        True,
        write_abac_dev_only,
        False,
    )


PATIENT_SCOPED_ROUTE_INVENTORY: tuple[PatientScopedRoute, ...] = (
    _read("GET", "/api/v1/patients", "patients_index", patient_scoped=False),
    _read("GET", "/api/v1/patients/{patient_id}", "patient"),
    _read("GET", "/api/v1/patients/{patient_id}/record", "patient_record"),
    _read("GET", "/api/v1/patients/{patient_id}/context", "patient_context"),
    _read("GET", "/api/v1/patients/{patient_id}/appointments", "appointments"),
    _read("GET", "/api/v1/patients/{patient_id}/allergies", "allergies"),
    _read("GET", "/api/v1/patients/{patient_id}/problems", "active_problems"),
    _read("GET", "/api/v1/patients/{patient_id}/medications", "medications"),
    _read(
        "GET",
        "/api/v1/patients/{patient_id}/medication-drafting-context",
        "medication_drafting_context",
    ),
    _read("GET", "/api/v1/patients/{patient_id}/encounters", "encounters"),
    _read("GET", "/api/v1/patients/{patient_id}/clinical-entries", "clinical_entries"),
    _read("GET", "/api/v1/patients/{patient_id}/clinical-events", "clinical_events"),
    _read("GET", "/api/v1/patients/{patient_id}/timeline", "clinical_timeline"),
    _read("GET", "/api/v1/patients/{patient_id}/clinical-orders", "clinical_orders"),
    _read("GET", "/api/v1/patients/{patient_id}/clinical-risks", "clinical_risks"),
    _read("GET", "/api/v1/patients/{patient_id}/vital-signs", "vital_signs"),
    _read("GET", "/api/v1/patients/{patient_id}/lab-panels", "lab_panels_results"),
    _read("POST", "/api/v1/patients/{patient_id}/ai/suggestions", "patient_ai"),
    _read("POST", "/api/v1/patients/{patient_id}/ai/clinical-intent", "patient_ai"),
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
    _write(
        "POST",
        "/api/v1/patients/{patient_id}/clinical-entries",
        "clinical_entries",
        write_abac_dev_only=True,
    ),
    _write("POST", "/api/v1/patients/{patient_id}/clinical-events", "clinical_events"),
    _write("POST", "/api/v1/patients/{patient_id}/clinical-orders", "clinical_orders"),
    _write(
        "POST",
        "/api/v1/patients/{patient_id}/vital-signs",
        "vital_signs",
        write_abac_dev_only=True,
    ),
    _write(
        "POST",
        "/api/v1/patients/{patient_id}/clinical-risks",
        "clinical_risks",
        write_abac_dev_only=True,
    ),
    _write("POST", "/api/v1/patients/{patient_id}/medications", "medications"),
    _write("POST", "/api/v1/patients/{patient_id}/allergies", "allergies"),
    _write("POST", "/api/v1/patients/{patient_id}/problems", "active_problems"),
    _write("POST", "/api/v1/patients/{patient_id}/encounters", "encounters"),
    _write("POST", "/api/v1/patients/{patient_id}/appointments", "appointments"),
    _write("POST", "/api/v1/patients/{patient_id}/lab-panels", "lab_panels_results"),
    _write(
        "POST",
        "/api/v1/hospitalization/patients/{patient_id}/daily-sheets",
        "hospital_daily_sheets",
    ),
    _write(
        "POST",
        "/api/v1/hospitalization/patients/{patient_id}/indications",
        "hospital_indications",
    ),
)


def patient_scoped_route_keys() -> tuple[str, ...]:
    return tuple(
        f"{route.method} {route.path_template}" for route in PATIENT_SCOPED_ROUTE_INVENTORY
    )


def read_abac_surface_keys() -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(
            route.surface for route in PATIENT_SCOPED_ROUTE_INVENTORY if route.read_abac_dev_only
        )
    )


def write_surface_keys() -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(
            route.surface for route in PATIENT_SCOPED_ROUTE_INVENTORY if route.write_surface
        )
    )


def write_abac_dev_only_surface_keys() -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(
            route.surface
            for route in PATIENT_SCOPED_ROUTE_INVENTORY
            if route.write_abac_dev_only
        )
    )
