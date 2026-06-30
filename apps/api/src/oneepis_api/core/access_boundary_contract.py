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
    AccessBoundaryStore(
        key="clinical_service",
        model="ClinicalService",
        table="clinical_services",
        purpose="Tenant-scoped clinical service boundary required before care-team ABAC.",
        runtime_enforcement="disabled",
    ),
    AccessBoundaryStore(
        key="care_team",
        model="CareTeam",
        table="care_teams",
        purpose="Service-scoped care team boundary required before patient relationship ABAC.",
        runtime_enforcement="disabled",
    ),
    AccessBoundaryStore(
        key="patient_care_team_relationship",
        model="PatientCareTeamRelationship",
        table="patient_care_team_relationships",
        purpose="Patient-to-care-team relationship store required before scoped PHI access.",
        runtime_enforcement="disabled",
    ),
)


ACCESS_BOUNDARY_RUNTIME_STATUS = {
    "institution_store_available": True,
    "tenant_store_available": True,
    "clinical_service_store_available": True,
    "care_team_store_available": True,
    "patient_care_team_relationship_store_available": True,
    "patient_scoping_enabled": False,
    "abac_runtime_enforced": False,
    "reason": "Access boundary stores are model stubs only; no patient access scoping yet.",
}


def access_boundary_store_keys() -> tuple[str, ...]:
    return tuple(store.key for store in ACCESS_BOUNDARY_STORES)
