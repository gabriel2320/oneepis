from datetime import date

from oneepis_api.models.patient import Patient, SexAtBirth
from oneepis_api.services.audit import audit_snapshot


def test_audit_snapshot_requires_explicit_allowlist() -> None:
    patient = Patient(
        first_name="Campo",
        last_name="Seguro",
        birth_date=date(1990, 1, 1),
        sex_at_birth=SexAtBirth.UNKNOWN,
    )

    assert audit_snapshot(patient, []) == {}
    assert audit_snapshot(patient, ["first_name"]) == {"first_name": "Campo"}
    assert "last_name" not in audit_snapshot(patient, ["first_name"])
