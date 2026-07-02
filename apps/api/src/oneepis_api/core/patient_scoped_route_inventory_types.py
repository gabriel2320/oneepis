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
