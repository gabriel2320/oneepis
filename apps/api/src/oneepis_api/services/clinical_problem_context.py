from __future__ import annotations

from unicodedata import category, normalize

from oneepis_api.schemas.patient import PatientRecordSnapshot


def event_matches_any_problem(snapshot: PatientRecordSnapshot, event: object) -> bool:
    return any(
        problem_event_match_reason(problem, event)
        for problem in snapshot.active_problems
    )


def problem_event_match_reason(problem: object, event: object) -> str | None:
    snomed_reason = _snomed_event_match_reason(problem, event)
    if snomed_reason:
        return snomed_reason

    problem_text = _normalize_text(problem.title)
    summary = _normalize_text(event.summary)
    if problem_text in summary or summary in problem_text:
        return "Evento asociado por coincidencia textual con el problema."

    vocabularies = {
        "respiratorio": {
            "problem": ("neumonia", "respiratorio", "epoc", "asma", "bronquial"),
            "event": ("disnea", "tos", "saturacion", "oxigeno", "respiratorio", "crepit"),
        },
        "dolor": {
            "problem": ("dolor", "algia"),
            "event": ("dolor", "algia", "colico", "molestia"),
        },
        "fiebre": {
            "problem": ("fiebre", "febril", "infeccion"),
            "event": ("fiebre", "febril", "temperatura", "calofrios"),
        },
        "hipertension": {
            "problem": ("hipertension", "hta", "presion arterial"),
            "event": ("presion", "pa ", "sistolica", "diastolica", "hipertension"),
        },
        "diabetes": {
            "problem": ("diabetes", "dm2", "glicemia"),
            "event": ("glicemia", "glucosa", "hipoglicemia", "hiperglicemia", "insulina"),
        },
    }
    for label, terms in vocabularies.items():
        if any(term in problem_text for term in terms["problem"]) and any(
            term in summary for term in terms["event"]
        ):
            if _has_negated_vocabulary_signal(label, summary):
                continue
            return f"Evento asociado por vocabulario clinico local: {label}."
    return None


def _has_negated_vocabulary_signal(label: str, summary: str) -> bool:
    negated_terms = {
        "respiratorio": (
            "sin disnea",
            "niega disnea",
            "sin tos",
            "niega tos",
            "sin dificultad respiratoria",
        ),
        "dolor": (
            "sin dolor",
            "niega dolor",
            "no presenta dolor",
            "descarta dolor",
        ),
        "fiebre": ("sin fiebre", "afebril", "niega fiebre"),
        "hipertension": (
            "presion normal",
            "pa normal",
            "sin hipertension",
            "niega hipertension",
        ),
        "diabetes": ("niega diabetes", "sin diabetes"),
    }
    return any(term in summary for term in negated_terms.get(label, ()))


def problem_domain_label(problem: object) -> str | None:
    code = _snomed_problem_code(problem)
    if code in {"233604007", "267036007", "195967001", "13645005"}:
        return "respiratorio"
    if code in {"73211009", "44054006"}:
        return "metabolico"
    if code in {"38341003", "59621000"}:
        return "hemodinamico"
    if code in {"386661006", "40733004", "6142004"}:
        return "infeccioso"

    title = _normalize_text(problem.title)
    domains = {
        "respiratorio": (
            "neumonia",
            "disnea",
            "epoc",
            "asma",
            "respiratorio",
            "bronquial",
        ),
        "metabolico": (
            "diabetes",
            "dm2",
            "dm1",
            "glicemia",
            "glucosa",
            "hiperglicemia",
            "hipoglicemia",
        ),
        "hemodinamico": (
            "hipertension",
            "hta",
            "presion arterial",
            "hipotension",
        ),
        "infeccioso": ("fiebre", "febril", "infeccion", "sepsis"),
    }
    for label, terms in domains.items():
        if any(term in title for term in terms):
            return label
    return None


def problem_domain_missing_data(
    problem: object,
    snapshot: PatientRecordSnapshot,
    events: list[object],
) -> list[str]:
    domain = problem_domain_label(problem)
    if domain is None:
        return []

    latest_vitals = snapshot.latest_vitals
    missing: list[str] = []
    if domain == "respiratorio":
        if latest_vitals is None or latest_vitals.oxygen_saturation_pct is None:
            missing.append(
                "Falta saturacion O2 reciente para contextualizar problema respiratorio."
            )
        if latest_vitals is None or latest_vitals.respiratory_rate_bpm is None:
            missing.append(
                "Falta frecuencia respiratoria reciente para contextualizar problema respiratorio."
            )
    elif domain == "metabolico":
        if not _events_include_terms(
            events,
            ("glicemia", "glucosa", "hipoglicemia", "hiperglicemia"),
        ):
            missing.append(
                "Falta glicemia o evento metabolico reciente para contextualizar diabetes/metabolico."
            )
    elif domain == "hemodinamico":
        if (
            latest_vitals is None
            or latest_vitals.systolic_bp is None
            or latest_vitals.diastolic_bp is None
        ):
            missing.append(
                "Falta presion arterial reciente para contextualizar problema hemodinamico."
            )
    elif domain == "infeccioso":
        if latest_vitals is None or latest_vitals.temperature_c is None:
            missing.append(
                "Falta temperatura reciente para contextualizar problema infeccioso."
            )
    return missing


def _snomed_event_match_reason(problem: object, event: object) -> str | None:
    problem_code = _snomed_problem_code(problem)
    if problem_code is None:
        return None

    event_concepts = _snomed_payload_concepts(event.payload)
    if problem_code in event_concepts["concept_ids"]:
        return "Evento asociado por mismo concepto SNOMED CT."
    if problem_code in event_concepts["ancestor_ids"]:
        return "Evento asociado por ancestro SNOMED CT desde repositorio terminologico."
    if problem_code in event_concepts["related_ids"]:
        return "Evento asociado por relacion SNOMED CT desde repositorio terminologico."
    return None


def _snomed_problem_code(problem: object) -> str | None:
    code_system = _normalize_text(problem.code_system or "").strip()
    if code_system not in {
        "snomed",
        "snomed ct",
        "snomed-ct",
        "sct",
        "http://snomed.info/sct",
    }:
        return None
    code = str(problem.code or "").strip()
    return code if code.isdigit() else None


def _snomed_payload_concepts(payload: object) -> dict[str, set[str]]:
    concept_ids: set[str] = set()
    ancestor_ids: set[str] = set()
    related_ids: set[str] = set()

    def add_code(target: set[str], value: object) -> None:
        if isinstance(value, int):
            target.add(str(value))
        elif isinstance(value, str) and value.strip().isdigit():
            target.add(value.strip())
        elif isinstance(value, dict):
            add_code(
                target,
                value.get("concept_id")
                or value.get("id")
                or value.get("code")
                or value.get("destinationId")
                or value.get("target"),
            )

    def add_many(target: set[str], value: object) -> None:
        if isinstance(value, list):
            for item in value:
                add_code(target, item)

    def read_concept(value: object) -> None:
        if not isinstance(value, dict):
            add_code(concept_ids, value)
            return
        add_code(
            concept_ids,
            value.get("concept_id") or value.get("id") or value.get("code"),
        )
        add_many(
            ancestor_ids,
            value.get("ancestor_ids") or value.get("ancestors") or value.get("parents"),
        )
        add_many(
            related_ids,
            value.get("related_concept_ids")
            or value.get("related")
            or value.get("relationships"),
        )

    if not isinstance(payload, dict):
        return {
            "concept_ids": concept_ids,
            "ancestor_ids": ancestor_ids,
            "related_ids": related_ids,
        }

    read_concept(payload.get("snomed") or payload.get("snomed_ct") or {})
    raw_concepts = payload.get("snomed_concepts")
    if isinstance(raw_concepts, list):
        for item in raw_concepts:
            read_concept(item)
    return {
        "concept_ids": concept_ids,
        "ancestor_ids": ancestor_ids,
        "related_ids": related_ids,
    }


def _events_include_terms(events: list[object], terms: tuple[str, ...]) -> bool:
    for event in events[:12]:
        text = _normalize_text(event.summary)
        payload = event.payload if isinstance(event.payload, dict) else {}
        payload_terms = " ".join(
            str(value)
            for value in payload.values()
            if isinstance(value, str | int | float)
        )
        normalized_payload = _normalize_text(payload_terms)
        if any(term in text or term in normalized_payload for term in terms):
            return True
    return False


def _normalize_text(value: str) -> str:
    decomposed = normalize("NFD", value.casefold())
    return "".join(char for char in decomposed if category(char) != "Mn")
