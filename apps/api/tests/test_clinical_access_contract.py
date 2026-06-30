from oneepis_api.core.clinical_access import PROTECTED_CLINICAL_ROUTE_PREFIXES


def test_protected_clinical_route_prefixes_are_explicit() -> None:
    assert PROTECTED_CLINICAL_ROUTE_PREFIXES == (
        "/api/v1/patients",
        "/api/v1/appointments",
        "/api/v1/hospitalization",
        "/api/v1/medication-catalog",
        "/api/v1/ai",
    )
