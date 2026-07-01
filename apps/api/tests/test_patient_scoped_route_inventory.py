from oneepis_api.core.clinical_write_access_contract import clinical_write_surface_keys
from oneepis_api.core.patient_scoped_route_inventory import (
    PATIENT_SCOPED_ROUTE_INVENTORY,
    patient_scoped_route_keys,
    read_abac_surface_keys,
    write_abac_dev_only_surface_keys,
    write_surface_keys,
)


def test_patient_scoped_route_inventory_tracks_declared_read_abac_surfaces() -> None:
    assert read_abac_surface_keys() == (
        "patients_index",
        "patient",
        "patient_record",
        "patient_context",
        "appointments",
        "allergies",
        "active_problems",
        "medications",
        "medication_drafting_context",
        "encounters",
        "clinical_entries",
        "clinical_events",
        "clinical_timeline",
        "clinical_orders",
        "clinical_risks",
        "vital_signs",
        "lab_panels_results",
        "patient_ai",
        "assistant_timeline",
        "assistant_search",
        "assistant_chart",
        "assistant_correlation",
        "hospital_daily_sheets",
        "hospital_indications",
        "active_hospitalization",
    )


def test_patient_scoped_route_inventory_matches_write_shadow_contract() -> None:
    assert write_surface_keys() == clinical_write_surface_keys()
    assert {
        route.runtime_write_abac for route in PATIENT_SCOPED_ROUTE_INVENTORY if route.write_surface
    } == {False}
    assert write_abac_dev_only_surface_keys() == (
        "clinical_entries",
        "vital_signs",
        "clinical_risks",
        "encounters",
    )


def test_read_abac_routes_require_read_audit() -> None:
    assert all(
        route.read_audit_required
        for route in PATIENT_SCOPED_ROUTE_INVENTORY
        if route.read_abac_dev_only
    )


def test_patient_scoped_route_inventory_has_unique_route_keys() -> None:
    route_keys = patient_scoped_route_keys()
    assert len(route_keys) == len(set(route_keys))
    assert all(
        route.path_template.startswith("/api/v1/")
        for route in PATIENT_SCOPED_ROUTE_INVENTORY
    )
