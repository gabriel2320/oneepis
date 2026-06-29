from __future__ import annotations

from oneepis_api.schemas.patient import PatientRecordSnapshot
from oneepis_api.services.clinical_context import (
    clinical_context_sections as _context_sections,
)
from oneepis_api.services.clinical_context import (
    clinical_evidence_marks as _evidence_marks,
)
from oneepis_api.services.clinical_context import (
    clinical_missing_data as _missing_data,
)
from oneepis_api.services.clinical_context import (
    clinical_sources as _sources,
)
from oneepis_api.services.clinical_problem_context_builder import (
    build_problem_contexts as _problem_contexts,
)


def clinical_intent_context_payload(
    snapshot: PatientRecordSnapshot,
    events: list[object],
    lab_results: list[object],
    *,
    missing_data: list[str] | None = None,
    active_risks: list[object] | None = None,
) -> dict[str, object]:
    return {
        "sources": _sources(snapshot, events, lab_results, active_risks),
        "missing_data": missing_data
        if missing_data is not None
        else _missing_data(snapshot, events),
        "evidence_marks": _evidence_marks(snapshot, events, lab_results, active_risks),
        "context_sections": _context_sections(snapshot, events, lab_results, active_risks),
        "problem_contexts": _problem_contexts(snapshot, events, lab_results),
    }
