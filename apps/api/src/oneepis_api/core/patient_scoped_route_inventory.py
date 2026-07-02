from oneepis_api.core.patient_scoped_route_inventory_reads import PATIENT_SCOPED_READ_ROUTES
from oneepis_api.core.patient_scoped_route_inventory_types import PatientScopedRoute
from oneepis_api.core.patient_scoped_route_inventory_writes import PATIENT_SCOPED_WRITE_ROUTES

PATIENT_SCOPED_ROUTE_INVENTORY: tuple[PatientScopedRoute, ...] = (
    *PATIENT_SCOPED_READ_ROUTES,
    *PATIENT_SCOPED_WRITE_ROUTES,
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
