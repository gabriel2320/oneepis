from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from oneepis_api.api.deps import CurrentUserDep, require_roles
from oneepis_api.services.auth import AuthenticatedUser, UserRole

GLOBAL_CLINICAL_INDEX_ROLES = frozenset({UserRole.ADMIN, UserRole.DEV})
_require_global_clinical_index_role = require_roles(*GLOBAL_CLINICAL_INDEX_ROLES)


def require_global_clinical_index_access(user: CurrentUserDep) -> AuthenticatedUser:
    return _require_global_clinical_index_role(user)


GlobalClinicalIndexAccessDep = Annotated[
    AuthenticatedUser,
    Depends(require_global_clinical_index_access),
]
