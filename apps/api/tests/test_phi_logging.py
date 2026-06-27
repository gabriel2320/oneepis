import logging

from oneepis_api.services.phi_logging import (
    REDACTED,
    PhiSafeLoggingFilter,
    configure_phi_safe_logging,
    sanitize_for_log,
)


def test_sanitize_for_log_redacts_patient_identity_fields() -> None:
    payload = {
        "first_name": "Elena",
        "last_name": "Rojas",
        "clinical_identifier": "ONE-001",
        "birth_date": "1981-04-12",
        "status": "active",
    }

    sanitized = sanitize_for_log(payload)

    assert sanitized["first_name"] == REDACTED
    assert sanitized["last_name"] == REDACTED
    assert sanitized["clinical_identifier"] == REDACTED
    assert sanitized["birth_date"] == REDACTED
    assert sanitized["status"] == "active"


def test_sanitize_for_log_redacts_clinical_free_text() -> None:
    payload = {
        "subjective": "Refiere dolor toracico.",
        "objective": "TA 120/80.",
        "assessment": "Angina estable.",
        "plan": "Control en 7 dias.",
        "kind": "progress",
    }

    sanitized = sanitize_for_log(payload)

    assert sanitized["subjective"] == REDACTED
    assert sanitized["objective"] == REDACTED
    assert sanitized["assessment"] == REDACTED
    assert sanitized["plan"] == REDACTED
    assert sanitized["kind"] == "progress"


def test_sanitize_for_log_redacts_nested_structures() -> None:
    payload = {
        "patient": {
            "email": "paciente@example.com",
            "id": "11111111-1111-4111-8111-111111111111",
        },
        "entries": [
            {"title": "Evolucion", "notes": "Texto clinico"},
            {"title": "Control", "notes": "Otro texto"},
        ],
    }

    sanitized = sanitize_for_log(payload)

    assert sanitized["patient"]["email"] == REDACTED
    assert sanitized["patient"]["id"] == "11111111-1111-4111-8111-111111111111"
    assert sanitized["entries"][0]["notes"] == REDACTED
    assert sanitized["entries"][0]["title"] == "Evolucion"


def test_sanitize_for_log_redacts_auth_secrets() -> None:
    payload = {
        "password": "medico",
        "access_token": "jwt-token",
        "refresh_token": "refresh-token",
        "actor_id": "medico@oneepis.local",
    }

    sanitized = sanitize_for_log(payload)

    assert sanitized["password"] == REDACTED
    assert sanitized["access_token"] == REDACTED
    assert sanitized["refresh_token"] == REDACTED
    assert sanitized["actor_id"] == "medico@oneepis.local"


def test_sanitize_for_log_redacts_flat_string_fields() -> None:
    message = (
        'patient first_name=Elena last_name="Rojas" '
        "clinical_identifier: ONE-001 status=active actor_id=medico@oneepis.local"
    )

    sanitized = sanitize_for_log(message)

    assert "Elena" not in sanitized
    assert "Rojas" not in sanitized
    assert "ONE-001" not in sanitized
    assert "first_name=[REDACTED]" in sanitized
    assert 'last_name="[REDACTED]"' in sanitized
    assert "clinical_identifier: [REDACTED]" in sanitized
    assert "status=active" in sanitized
    assert "actor_id=medico@oneepis.local" in sanitized


def test_sanitize_for_log_redacts_flat_json_like_string_fields() -> None:
    message = '{"email": "paciente@example.com", "event": "login", "access_token": "secret"}'

    sanitized = sanitize_for_log(message)

    assert "paciente@example.com" not in sanitized
    assert "secret" not in sanitized
    assert '"email": "[REDACTED]"' in sanitized
    assert '"access_token": "[REDACTED]"' in sanitized
    assert '"event": "login"' in sanitized


def test_phi_safe_logging_filter_sanitizes_log_record() -> None:
    record = logging.LogRecord(
        name="oneepis.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg={"first_name": "Elena", "action": "patient.read"},
        args=(),
        exc_info=None,
    )

    assert PhiSafeLoggingFilter().filter(record) is True
    assert record.msg == {"first_name": REDACTED, "action": "patient.read"}


def test_phi_safe_logging_filter_sanitizes_flat_message_and_args() -> None:
    record = logging.LogRecord(
        name="oneepis.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="patient first_name=Elena action=%s",
        args=("clinical_identifier=ONE-001",),
        exc_info=None,
    )

    assert PhiSafeLoggingFilter().filter(record) is True
    assert record.msg == "patient first_name=[REDACTED] action=%s"
    assert record.args == ("clinical_identifier=[REDACTED]",)


def test_configure_phi_safe_logging_is_idempotent() -> None:
    root = logging.getLogger()

    configure_phi_safe_logging()
    count_after_first = sum(isinstance(item, PhiSafeLoggingFilter) for item in root.filters)
    configure_phi_safe_logging()
    count_after_second = sum(isinstance(item, PhiSafeLoggingFilter) for item in root.filters)

    assert count_after_first >= 1
    assert count_after_second == count_after_first
