from oneepis_api.core.document_custody_contract import (
    DOCUMENT_CUSTODY_REQUIREMENTS,
    DOCUMENT_CUSTODY_RUNTIME_STATUS,
    FUTURE_DOCUMENT_WORKFLOWS,
    document_custody_requirement_keys,
    future_document_workflow_keys,
)


def test_document_custody_contract_tracks_minimum_requirements() -> None:
    assert document_custody_requirement_keys() == (
        "secure_document_storage",
        "malware_scan",
        "document_metadata_versioning",
        "custody_retention_legal_hold",
        "consent_lifecycle",
        "document_access_audit",
    )

    assert all(requirement.label for requirement in DOCUMENT_CUSTODY_REQUIREMENTS)
    assert all(requirement.criterion for requirement in DOCUMENT_CUSTODY_REQUIREMENTS)
    assert {requirement.status for requirement in DOCUMENT_CUSTODY_REQUIREMENTS} == {
        "required_before_document_uploads"
    }


def test_future_document_workflows_remain_disabled_until_custody_exists() -> None:
    assert future_document_workflow_keys() == (
        "external_attachment_upload",
        "productive_consent_management",
        "document_ocr_or_rag",
    )

    requirement_keys = set(document_custody_requirement_keys())
    assert all(not workflow.enabled_at_runtime for workflow in FUTURE_DOCUMENT_WORKFLOWS)
    for workflow in FUTURE_DOCUMENT_WORKFLOWS:
        assert workflow.required_before_enablement
        assert set(workflow.required_before_enablement).issubset(requirement_keys)
        assert "document_access_audit" in workflow.required_before_enablement
        if workflow.key in {
            "external_attachment_upload",
            "productive_consent_management",
            "document_ocr_or_rag",
        }:
            assert "custody_retention_legal_hold" in workflow.required_before_enablement


def test_document_custody_contract_does_not_claim_runtime_storage() -> None:
    assert DOCUMENT_CUSTODY_RUNTIME_STATUS == {
        "document_uploads_enabled": False,
        "productive_consents_enabled": False,
        "document_ocr_or_rag_enabled": False,
        "reason": (
            "Document custody is an executable no-production contract only; "
            "runtime storage and consent workflows are future work."
        ),
    }
