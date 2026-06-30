from __future__ import annotations

import uuid
from typing import Literal

from pydantic import Field, field_validator

from oneepis_api.schemas.common import APIModel

DiagnosisCodeSystem = Literal["SNOMED-GPS", "SNOMED-CT", "CIE-10", "ICD-10", "CIE-11", "ICD-11"]
DiagnosisValidationStatus = Literal["validated_reference", "legacy", "external", "needs_review"]
TERMINOLOGY_CODE_SYSTEMS = {"SNOMED-GPS", "SNOMED-CT", "CIE-10", "ICD-10", "CIE-11", "ICD-11"}


def normalize_diagnosis_code_system(value: str | None) -> str | None:
    if not value:
        return None
    normalized = " ".join(value.strip().upper().replace("_", "-").split())
    aliases = {
        "SNOMED": "SNOMED-CT",
        "SNOMED CT": "SNOMED-CT",
        "SCT": "SNOMED-CT",
        "HTTP://SNOMED.INFO/SCT": "SNOMED-CT",
        "SNOMED-GPS": "SNOMED-GPS",
        "SNOMED GPS": "SNOMED-GPS",
        "ICD-10": "ICD-10",
        "CIE-10": "CIE-10",
        "ICD10": "ICD-10",
        "CIE10": "CIE-10",
        "ICD-11": "ICD-11",
        "CIE-11": "CIE-11",
        "ICD11": "ICD-11",
        "CIE11": "CIE-11",
    }
    return aliases.get(normalized, value.strip())


def validate_diagnosis_code_pair(system: str | None, code: str | None) -> None:
    normalized_system = normalize_diagnosis_code_system(system)
    if not code or normalized_system not in TERMINOLOGY_CODE_SYSTEMS:
        return
    value = code.strip()
    if len(value) > 80 or any(marker in value for marker in ("\n", "\r", "\t")):
        raise ValueError("Diagnostic code must be a short single-line value")
    if normalized_system in {"SNOMED-GPS", "SNOMED-CT"} and not value.isdigit():
        raise ValueError("SNOMED diagnostic codes must be numeric")


def legacy_diagnostic_code_reference(
    *,
    system: str | None,
    code: str | None,
    label: str,
) -> DiagnosisCodeReference | None:
    normalized_system = normalize_diagnosis_code_system(system)
    if not normalized_system or not code or normalized_system not in TERMINOLOGY_CODE_SYSTEMS:
        return None
    return DiagnosisCodeReference(
        system=normalized_system,  # type: ignore[arg-type]
        code=code.strip(),
        label=label,
        source_label="Ficha OneEpis",
        source_version="legacy-code-fields",
        validation_status="legacy",
        primary=True,
    )


def diagnostic_code_references_from_payload(
    value: object,
    *,
    fallback_label: str,
) -> list[DiagnosisCodeReference]:
    if not isinstance(value, list):
        return []
    references: list[DiagnosisCodeReference] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        payload = {
            "label": fallback_label,
            "source_label": "Payload diagnostico externo",
            "validation_status": "external",
            "primary": False,
            **item,
        }
        payload["system"] = normalize_diagnosis_code_system(str(payload.get("system") or ""))
        references.append(DiagnosisCodeReference.model_validate(payload))
    return references


class DiagnosisCodeReference(APIModel):
    system: DiagnosisCodeSystem
    code: str = Field(min_length=1, max_length=80)
    label: str = Field(min_length=1, max_length=160)
    source_label: str = Field(min_length=1, max_length=160)
    source_version: str | None = Field(default=None, max_length=80)
    validation_status: DiagnosisValidationStatus = "needs_review"
    primary: bool = False

    @field_validator("code")
    @classmethod
    def validate_code(cls, value: str, info) -> str:
        code = value.strip()
        system = info.data.get("system")
        if system in {"SNOMED-GPS", "SNOMED-CT"} and not code.isdigit():
            raise ValueError("SNOMED diagnostic codes must be numeric")
        if any(marker in code for marker in ("\n", "\r", "\t")):
            raise ValueError("Diagnostic codes must be single-line values")
        return code


class DiagnosticReferenceSource(APIModel):
    source_label: str = Field(min_length=1, max_length=160)
    source_version: str | None = Field(default=None, max_length=80)
    chapter_id: str | None = Field(default=None, max_length=40)
    page_label: str | None = Field(default=None, max_length=80)
    summary: str = Field(min_length=1, max_length=320)


class DiagnosticCandidate(APIModel):
    candidate_id: uuid.UUID
    title: str = Field(min_length=1, max_length=160)
    domain: str = Field(min_length=1, max_length=80)
    certainty: Literal["moderate", "low"] = "low"
    rationale: str = Field(min_length=1, max_length=320)
    evidence: list[str] = Field(default_factory=list)
    missing_data: list[str] = Field(default_factory=list)
    coding_references: list[DiagnosisCodeReference] = Field(default_factory=list)
    reference_sources: list[DiagnosticReferenceSource] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    requires_human_confirmation: bool = True
