from starlette.requests import Request

from oneepis_api.api.deps import ABAC_MINIMUM_REQUIREMENTS, AccessContext, build_access_context
from oneepis_api.core.access_context_contract import (
    ACCESS_CONTEXT_REQUIREMENTS,
    ACCESS_CONTEXT_RUNTIME_STATUS,
    ACCESS_REASON_CONTRACTS,
    CONTEXTUAL_ACCESS_HEADER_CONTRACTS,
    access_context_requirement_keys,
    access_reason_audit_metadata,
    access_reason_keys,
    contextual_access_header_names,
)
from oneepis_api.core.access_context_runtime import (
    PATIENT_SCOPE_DRY_RUN_METADATA_KEYS,
    attach_patient_scope_dry_run_metadata,
    evaluate_access_context,
)
from oneepis_api.main import UNSUPPORTED_CONTEXTUAL_ACCESS_HEADERS
from oneepis_api.services.auth import AuthenticatedUser, UserRole


def test_access_context_contract_matches_abac_policy_requirements() -> None:
    assert access_context_requirement_keys() == ABAC_MINIMUM_REQUIREMENTS

    assert all(requirement.label for requirement in ACCESS_CONTEXT_REQUIREMENTS)
    assert all(requirement.criterion for requirement in ACCESS_CONTEXT_REQUIREMENTS)
    assert {requirement.status for requirement in ACCESS_CONTEXT_REQUIREMENTS} == {
        "required_before_phi"
    }


def test_contextual_header_contract_matches_current_runtime_rejections() -> None:
    assert contextual_access_header_names() == UNSUPPORTED_CONTEXTUAL_ACCESS_HEADERS

    mapped_requirement_keys = {
        contract.requirement_key for contract in CONTEXTUAL_ACCESS_HEADER_CONTRACTS
    }
    assert mapped_requirement_keys == set(ABAC_MINIMUM_REQUIREMENTS)

    assert {contract.status for contract in CONTEXTUAL_ACCESS_HEADER_CONTRACTS} == {
        "unsupported_until_runtime_abac"
    }
    assert {contract.audit_metadata for contract in CONTEXTUAL_ACCESS_HEADER_CONTRACTS} == {
        "header_name_only"
    }
    assert {contract.value_retention for contract in CONTEXTUAL_ACCESS_HEADER_CONTRACTS} == {
        "never_store_header_value"
    }


def test_access_context_contract_does_not_claim_runtime_abac() -> None:
    assert ACCESS_CONTEXT_RUNTIME_STATUS == {
        "runtime_abac_enforced": False,
        "development_patient_read_enforcement_available": True,
        "development_patient_read_enforcement_scope": "GET /api/v1/patients/{patient_id}",
        "contextual_headers_accepted": False,
        "break_glass_enabled": False,
        "reason": (
            "Contextual ABAC production enforcement is disabled; development-only "
            "patient read enforcement is available behind ONEEPIS_ABAC_ENFORCEMENT_ENABLED."
        ),
    }


def test_access_reason_contract_declares_future_reviewed_reason_keys() -> None:
    assert access_reason_keys() == (
        "active_care_relationship",
        "temporary_coverage",
        "care_coordination",
        "break_glass",
    )
    assert {contract.status for contract in ACCESS_REASON_CONTRACTS} == {
        "future_review_required"
    }
    assert {contract.free_text_retention for contract in ACCESS_REASON_CONTRACTS} == {
        "never_store_raw_reason_text"
    }
    assert all(contract.requires_patient_scope for contract in ACCESS_REASON_CONTRACTS)
    assert {
        contract.key
        for contract in ACCESS_REASON_CONTRACTS
        if contract.requires_review
    } == {
        "temporary_coverage",
        "care_coordination",
        "break_glass",
    }


def test_access_reason_audit_metadata_retains_only_reason_key() -> None:
    assert access_reason_audit_metadata("care_coordination") == {
        "access_reason_key": "care_coordination",
        "access_reason_known": True,
        "raw_reason_retained": False,
    }
    assert access_reason_audit_metadata("texto libre con PHI no debe quedar") == {
        "access_reason_key": "unknown",
        "access_reason_known": False,
        "raw_reason_retained": False,
    }


def test_access_context_runtime_object_is_rbac_only_until_abac_enforcement() -> None:
    user = AuthenticatedUser(
        email="medico@oneepis.local",
        name="Medico OneEpis",
        roles=frozenset({UserRole.MEDICO}),
        actor_id="medico@oneepis.local",
    )
    request = _request_with_headers(())

    context = build_access_context(user, request)

    assert isinstance(context, AccessContext)
    assert context.actor_id == "medico@oneepis.local"
    assert context.role_names == ("medico",)
    assert context.source == "rbac_only"
    assert context.institution_id is None
    assert context.tenant_id is None
    assert context.care_team_id is None
    assert context.access_reason is None
    assert context.break_glass_requested is False
    assert context.unsupported_contextual_header_names == ()
    assert context.missing_abac_requirements == ABAC_MINIMUM_REQUIREMENTS
    assert context.runtime_abac_enforced is False
    assert context.contextual_headers_accepted is False
    assert context.break_glass_enabled is False


def test_access_context_runtime_object_does_not_retain_contextual_header_values() -> None:
    user = AuthenticatedUser(
        email="dev@oneepis.local",
        name="Dev OneEpis",
        roles=frozenset({UserRole.ADMIN, UserRole.DEV}),
        actor_id="dev@oneepis.local",
    )
    request = _request_with_headers(
        (
            (b"x-oneepis-tenant", b"tenant-secreto-no-retener"),
            (b"x-oneepis-access-reason", b"motivo-clinico-no-retener"),
        )
    )

    context = build_access_context(user, request)

    assert context.unsupported_contextual_header_names == (
        "X-OneEpis-Access-Reason",
        "X-OneEpis-Tenant",
    )
    assert context.tenant_id is None
    assert context.access_reason is None
    assert "tenant-secreto-no-retener" not in repr(context)
    assert "motivo-clinico-no-retener" not in repr(context)


def test_access_context_denial_contract_is_not_runtime_enforcement_yet() -> None:
    user = AuthenticatedUser(
        email="sololectura@oneepis.local",
        name="Solo Lectura OneEpis",
        roles=frozenset({UserRole.SOLO_LECTURA}),
        actor_id="sololectura@oneepis.local",
    )
    context = build_access_context(user, _request_with_headers(()))

    decision = evaluate_access_context(context)

    assert decision.policy == "contextual_abac"
    assert decision.runtime_enforced is False
    assert decision.allowed is True
    assert decision.would_deny_if_enforced is True
    assert decision.denial_reasons == tuple(
        f"missing_abac_requirement:{requirement}"
        for requirement in ABAC_MINIMUM_REQUIREMENTS
    )
    assert decision.metadata_retention == "requirement_keys_only"


def test_access_context_denial_contract_does_not_retain_header_values() -> None:
    user = AuthenticatedUser(
        email="dev@oneepis.local",
        name="Dev OneEpis",
        roles=frozenset({UserRole.DEV}),
        actor_id="dev@oneepis.local",
    )
    request = _request_with_headers(
        ((b"x-oneepis-access-reason", b"valor-no-debe-quedar-en-decision"),)
    )
    context = build_access_context(user, request)

    decision = evaluate_access_context(context)

    assert "valor-no-debe-quedar-en-decision" not in repr(decision)
    assert decision.denial_reasons == tuple(
        f"missing_abac_requirement:{requirement}"
        for requirement in ABAC_MINIMUM_REQUIREMENTS
    )


def test_access_context_can_carry_minimized_patient_scope_dry_run_metadata() -> None:
    user = AuthenticatedUser(
        email="medico@oneepis.local",
        name="Medico OneEpis",
        roles=frozenset({UserRole.MEDICO}),
        actor_id="medico@oneepis.local",
    )
    context = build_access_context(user, _request_with_headers(()))

    enriched_context = attach_patient_scope_dry_run_metadata(
        context,
        {
            "status": "resolved",
            "matched_care_team_count": 1,
            "actor_active_care_team_count": 2,
            "patient_active_care_team_count": 1,
            "runtime_enforced": False,
        },
    )

    assert enriched_context.patient_scope_dry_run_metadata == {
        "status": "resolved",
        "matched_care_team_count": 1,
        "actor_active_care_team_count": 2,
        "patient_active_care_team_count": 1,
        "runtime_enforced": False,
    }
    assert tuple(enriched_context.patient_scope_dry_run_metadata) == (
        PATIENT_SCOPE_DRY_RUN_METADATA_KEYS
    )
    assert enriched_context.runtime_abac_enforced is False
    assert enriched_context.missing_abac_requirements == ABAC_MINIMUM_REQUIREMENTS


def test_access_context_patient_scope_dry_run_metadata_filters_identifiers() -> None:
    user = AuthenticatedUser(
        email="medico@oneepis.local",
        name="Medico OneEpis",
        roles=frozenset({UserRole.MEDICO}),
        actor_id="medico@oneepis.local",
    )
    context = build_access_context(user, _request_with_headers(()))

    enriched_context = attach_patient_scope_dry_run_metadata(
        context,
        {
            "status": "resolved",
            "matched_care_team_count": 1,
            "patient_id": "7f3d8733-74ba-4a0f-a041-99f957ab6bb6",
            "matched_care_team_ids": ("care-team-no-retener",),
        },
    )

    assert enriched_context.patient_scope_dry_run_metadata == {
        "status": "resolved",
        "matched_care_team_count": 1,
    }
    assert "7f3d8733-74ba-4a0f-a041-99f957ab6bb6" not in repr(enriched_context)
    assert "care-team-no-retener" not in repr(enriched_context)


def _request_with_headers(headers: tuple[tuple[bytes, bytes], ...]) -> Request:
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/api/v1/patients",
            "headers": headers,
        }
    )
