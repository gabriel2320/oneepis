from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select

from oneepis_api.api.deps import ReadAccessDep
from oneepis_api.models.clinical_record import (
    ActiveProblem,
    Allergy,
    ClinicalEncounter,
    ClinicalEntry,
    ClinicalEntryStatus,
    ClinicalEvent,
    Medication,
    RecordStatus,
    VitalSign,
)
from oneepis_api.schemas.clinical_record import AssistantSearchResponse, AssistantSearchResult

from .patient_assistant_common import (
    like_pattern,
    match_columns,
)
from .patient_assistant_labs import lab_search_results, search_lab_results_for_assistant
from .patient_assistant_scope import enforce_and_record_assistant_read
from .patient_assistant_search_results import (
    allergy_results,
    encounter_results,
    entry_results,
    event_results,
    medication_results,
    problem_results,
    vital_results,
)
from .patient_shared import LimitQuery, SessionDep, SettingsDep, require_patient

router = APIRouter()
AssistantSearchQuery = Annotated[str, Query(alias="q", min_length=2, max_length=120)]


@router.get("/{patient_id}/assistant/search", response_model=AssistantSearchResponse)
def search_assistant_read_layer(
    patient_id: uuid.UUID,
    session: SessionDep,
    user: ReadAccessDep,
    settings: SettingsDep,
    q: AssistantSearchQuery,
    limit: LimitQuery = 20,
) -> AssistantSearchResponse:
    require_patient(session, patient_id)
    query = q.strip()
    if len(query) < 2:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Search query must contain at least 2 non-space characters.",
        )
    enforce_and_record_assistant_read(
        session,
        patient_id=patient_id,
        user=user,
        settings=settings,
        action="assistant_search.read",
    )
    query_limit = limit + 1
    pattern = like_pattern(query)
    encounters = _search_encounters(session, patient_id, pattern, query_limit)
    entries = _search_entries(session, patient_id, pattern, query_limit)
    events = _search_events(session, patient_id, pattern, query_limit)
    vitals = _search_vitals(session, patient_id, pattern, query_limit)
    medications = _search_medications(session, patient_id, pattern, query_limit)
    problems = _search_problems(session, patient_id, pattern, query_limit)
    allergies = _search_allergies(session, patient_id, pattern, query_limit)
    lab_results = search_lab_results_for_assistant(session, patient_id, pattern, query_limit)
    results = [
        *encounter_results(query, patient_id, encounters),
        *entry_results(query, patient_id, entries),
        *event_results(query, patient_id, events),
        *vital_results(query, patient_id, vitals),
        *medication_results(query, patient_id, medications),
        *problem_results(query, patient_id, problems),
        *allergy_results(query, patient_id, allergies),
        *lab_search_results(query, patient_id, lab_results),
    ]
    results.sort(key=lambda item: item.occurred_at, reverse=True)
    has_more = len(results) > limit or any(
        len(domain_items) > limit
        for domain_items in (
            encounters,
            entries,
            events,
            vitals,
            medications,
            problems,
            allergies,
            lab_results,
        )
    )
    return AssistantSearchResponse(
        patient_id=patient_id,
        query=query,
        results=results[:limit],
        missing_data=_search_missing_data(results),
        warnings=_search_warnings(has_more=has_more, limit=limit),
        limit=limit,
        has_more=has_more,
    )


def _search_encounters(session, patient_id: uuid.UUID, pattern: str, limit: int):
    return list(
        session.scalars(
            select(ClinicalEncounter)
            .where(
                ClinicalEncounter.patient_id == patient_id,
                match_columns(
                    pattern,
                    ClinicalEncounter.reason,
                    ClinicalEncounter.location_label,
                    ClinicalEncounter.notes,
                ),
            )
            .order_by(ClinicalEncounter.started_at.desc())
            .limit(limit)
        )
    )


def _search_entries(session, patient_id: uuid.UUID, pattern: str, limit: int):
    return list(
        session.scalars(
            select(ClinicalEntry)
            .where(
                ClinicalEntry.patient_id == patient_id,
                ClinicalEntry.status != ClinicalEntryStatus.ENTERED_IN_ERROR,
                match_columns(
                    pattern,
                    ClinicalEntry.title,
                    ClinicalEntry.subjective,
                    ClinicalEntry.objective,
                    ClinicalEntry.assessment,
                    ClinicalEntry.plan,
                ),
            )
            .order_by(ClinicalEntry.occurred_at.desc())
            .limit(limit)
        )
    )


def _search_events(session, patient_id: uuid.UUID, pattern: str, limit: int):
    return list(
        session.scalars(
            select(ClinicalEvent)
            .where(
                ClinicalEvent.patient_id == patient_id,
                match_columns(pattern, ClinicalEvent.summary),
            )
            .order_by(ClinicalEvent.occurred_at.desc())
            .limit(limit)
        )
    )


def _search_vitals(session, patient_id: uuid.UUID, pattern: str, limit: int):
    return list(
        session.scalars(
            select(VitalSign)
            .where(
                VitalSign.patient_id == patient_id,
                VitalSign.status != RecordStatus.ENTERED_IN_ERROR,
                match_columns(pattern, VitalSign.notes),
            )
            .order_by(VitalSign.measured_at.desc())
            .limit(limit)
        )
    )


def _search_medications(session, patient_id: uuid.UUID, pattern: str, limit: int):
    return list(
        session.scalars(
            select(Medication)
            .where(
                Medication.patient_id == patient_id,
                Medication.status == RecordStatus.ACTIVE,
                match_columns(
                    pattern,
                    Medication.name,
                    Medication.dose,
                    Medication.route,
                    Medication.frequency,
                ),
            )
            .order_by(Medication.created_at.desc())
            .limit(limit)
        )
    )


def _search_problems(session, patient_id: uuid.UUID, pattern: str, limit: int):
    return list(
        session.scalars(
            select(ActiveProblem)
            .where(
                ActiveProblem.patient_id == patient_id,
                ActiveProblem.status == RecordStatus.ACTIVE,
                match_columns(
                    pattern,
                    ActiveProblem.title,
                    ActiveProblem.code,
                    ActiveProblem.notes,
                ),
            )
            .order_by(ActiveProblem.created_at.desc())
            .limit(limit)
        )
    )


def _search_allergies(session, patient_id: uuid.UUID, pattern: str, limit: int):
    return list(
        session.scalars(
            select(Allergy)
            .where(
                Allergy.patient_id == patient_id,
                Allergy.status == RecordStatus.ACTIVE,
                match_columns(pattern, Allergy.substance, Allergy.reaction),
            )
            .order_by(Allergy.recorded_at.desc())
            .limit(limit)
        )
    )


def _search_missing_data(results: list[AssistantSearchResult]) -> list[str]:
    if results:
        return []
    return ["No se encontraron coincidencias clinicas estructuradas para la busqueda."]


def _search_warnings(*, has_more: bool, limit: int) -> list[str]:
    if not has_more:
        return []
    return [f"Busqueda limitada a {limit} resultados; afina la consulta o abre dominios fuente."]
