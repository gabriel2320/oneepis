from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class DocumentCustodyRequirement:
    key: str
    label: str
    criterion: str
    status: Literal["required_before_document_uploads"]


@dataclass(frozen=True)
class FutureDocumentWorkflow:
    key: str
    label: str
    enabled_at_runtime: bool
    required_before_enablement: tuple[str, ...]


DOCUMENT_CUSTODY_REQUIREMENTS: tuple[DocumentCustodyRequirement, ...] = (
    DocumentCustodyRequirement(
        key="secure_document_storage",
        label="Secure document storage",
        criterion=(
            "Attachments and signed documents must use encrypted object storage "
            "with environment-scoped access controls."
        ),
        status="required_before_document_uploads",
    ),
    DocumentCustodyRequirement(
        key="malware_scan",
        label="Malware scan",
        criterion="Every uploaded document must pass malware scanning before clinical use.",
        status="required_before_document_uploads",
    ),
    DocumentCustodyRequirement(
        key="document_metadata_versioning",
        label="Metadata and versioning",
        criterion=(
            "Documents must track type, source, version, checksum, actor, timestamp "
            "and patient scope."
        ),
        status="required_before_document_uploads",
    ),
    DocumentCustodyRequirement(
        key="custody_retention_legal_hold",
        label="Custody, retention and legal hold",
        criterion=(
            "Document retention, deletion, custody transfer and legal hold rules "
            "must be versioned and reviewed."
        ),
        status="required_before_document_uploads",
    ),
    DocumentCustodyRequirement(
        key="consent_lifecycle",
        label="Consent lifecycle",
        criterion=(
            "Consent documents must track template version, signer, validity, "
            "revocation and custody."
        ),
        status="required_before_document_uploads",
    ),
    DocumentCustodyRequirement(
        key="document_access_audit",
        label="Document access audit",
        criterion=(
            "Document reads, writes, downloads, exports and custody actions must "
            "emit minimized audit events."
        ),
        status="required_before_document_uploads",
    ),
)


FUTURE_DOCUMENT_WORKFLOWS: tuple[FutureDocumentWorkflow, ...] = (
    FutureDocumentWorkflow(
        key="external_attachment_upload",
        label="External attachment upload",
        enabled_at_runtime=False,
        required_before_enablement=(
            "secure_document_storage",
            "malware_scan",
            "document_metadata_versioning",
            "custody_retention_legal_hold",
            "document_access_audit",
        ),
    ),
    FutureDocumentWorkflow(
        key="productive_consent_management",
        label="Productive consent management",
        enabled_at_runtime=False,
        required_before_enablement=(
            "secure_document_storage",
            "document_metadata_versioning",
            "custody_retention_legal_hold",
            "consent_lifecycle",
            "document_access_audit",
        ),
    ),
    FutureDocumentWorkflow(
        key="document_ocr_or_rag",
        label="Document OCR or RAG",
        enabled_at_runtime=False,
        required_before_enablement=(
            "secure_document_storage",
            "malware_scan",
            "document_metadata_versioning",
            "document_access_audit",
        ),
    ),
)


DOCUMENT_CUSTODY_RUNTIME_STATUS = {
    "document_uploads_enabled": False,
    "productive_consents_enabled": False,
    "document_ocr_or_rag_enabled": False,
    "reason": (
        "Document custody is an executable no-production contract only; "
        "runtime storage and consent workflows are future work."
    ),
}


def document_custody_requirement_keys() -> tuple[str, ...]:
    return tuple(requirement.key for requirement in DOCUMENT_CUSTODY_REQUIREMENTS)


def future_document_workflow_keys() -> tuple[str, ...]:
    return tuple(workflow.key for workflow in FUTURE_DOCUMENT_WORKFLOWS)
