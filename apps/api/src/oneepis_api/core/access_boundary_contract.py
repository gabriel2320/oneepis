from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class AccessBoundaryStore:
    key: str
    model: str
    table: str
    purpose: str
    runtime_enforcement: Literal["disabled"]


ACCESS_BOUNDARY_STORES: tuple[AccessBoundaryStore, ...] = (
    AccessBoundaryStore(
        key="institution",
        model="ClinicalInstitution",
        table="clinical_institutions",
        purpose="Top-level clinical data boundary required before PHI use.",
        runtime_enforcement="disabled",
    ),
    AccessBoundaryStore(
        key="tenant",
        model="ClinicalTenant",
        table="clinical_tenants",
        purpose="Institution-scoped operational tenant boundary required before PHI use.",
        runtime_enforcement="disabled",
    ),
)


ACCESS_BOUNDARY_RUNTIME_STATUS = {
    "institution_store_available": True,
    "tenant_store_available": True,
    "patient_scoping_enabled": False,
    "abac_runtime_enforced": False,
    "reason": "Institution and tenant stores are model stubs only; no patient access scoping yet.",
}


def access_boundary_store_keys() -> tuple[str, ...]:
    return tuple(store.key for store in ACCESS_BOUNDARY_STORES)
