import uuid
from collections.abc import Iterator
from contextlib import contextmanager

from fastapi.testclient import TestClient
from patient_ai_helpers import create_patient, create_vitals
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, selectinload, sessionmaker
from sqlalchemy.pool import StaticPool

from oneepis_api import models as _models  # noqa: F401
from oneepis_api.db.base import Base
from oneepis_api.models.medication_catalog import (
    MedicationCatalogItem,
    MedicationCatalogStatus,
    MedicationDoseRule,
    MedicationSourceReviewStatus,
    MedicationSourceSystem,
)
from oneepis_api.services.medication_catalog_farmaco import (
    FARMACO_ACCEPTED_COUNT,
    FARMACO_CANDIDATE_COUNT,
    FARMACO_CURATED_BY,
    FARMACO_SOURCE_LABEL,
    FARMACO_SOURCE_VERSION,
    accepted_farmaco_candidates,
    ensure_farmaco_draft_catalog,
    farmaco_candidate_by_display_name,
    farmaco_evidence_for_catalog_item_id,
    load_farmaco_candidate_evidence_artifact,
    load_farmaco_candidates_artifact,
    load_farmaco_source_map,
)


def test_farmaco_artifacts_keep_explicit_conservative_decisions() -> None:
    artifact = load_farmaco_candidates_artifact()
    candidates = artifact["candidates"]

    assert artifact["candidate_count"] == FARMACO_CANDIDATE_COUNT
    assert artifact["decision_counts"] == {
        "accepted": FARMACO_ACCEPTED_COUNT,
        "needs_review": 5,
        "rejected": 24,
    }
    assert len(candidates) == FARMACO_CANDIDATE_COUNT
    assert len(accepted_farmaco_candidates()) == FARMACO_ACCEPTED_COUNT

    decisions_by_name = {item["display_name"]: item["decision"] for item in candidates}
    assert {
        "AAS": "needs_review",
        "ACTH": "needs_review",
        "Navelbina": "needs_review",
        "Prinatel-pamoato": "needs_review",
        "THC": "needs_review",
        "Helmintos": "rejected",
        "Mercurio": "rejected",
        "Micobacterias": "rejected",
        "Nitrosaminas": "rejected",
    }.items() <= decisions_by_name.items()

    for candidate in candidates:
        assert candidate["decision"] in {"accepted", "needs_review", "rejected"}
        assert candidate["decision_reason"]
        assert candidate["therapeutic_class"]
        assert candidate["catalog_item_id"]


def test_farmaco_source_map_and_evidence_are_metadata_only() -> None:
    source_map = load_farmaco_source_map()
    evidence_artifact = load_farmaco_candidate_evidence_artifact()

    assert source_map["source"]["label"] == FARMACO_SOURCE_LABEL
    assert source_map["source"]["source_version"] == FARMACO_SOURCE_VERSION
    assert source_map["source"]["sha256"]
    assert source_map["source"]["line_count"] == 53677
    assert source_map["source"]["page_marker_count"] == 461
    assert source_map["source"]["chapter_count"] == 71
    assert source_map["source"]["index_start_line"] == 49189
    assert source_map["chapters"]
    assert source_map["page_markers"]

    assert evidence_artifact["candidate_count"] == FARMACO_CANDIDATE_COUNT
    assert evidence_artifact["accepted_count"] == FARMACO_ACCEPTED_COUNT
    assert len(evidence_artifact["items"]) == FARMACO_CANDIDATE_COUNT
    _assert_no_long_text_payload(evidence_artifact)


def test_farmaco_reconciler_imports_only_accepted_drafts_idempotently() -> None:
    with _test_session() as session:
        ensure_farmaco_draft_catalog(session)
        session.commit()
        ensure_farmaco_draft_catalog(session)
        session.commit()

        count = session.scalar(
            select(func.count())
            .select_from(MedicationCatalogItem)
            .where(MedicationCatalogItem.source_label == FARMACO_SOURCE_LABEL)
        )
        assert count == FARMACO_ACCEPTED_COUNT

        names = set(
            session.scalars(
                select(MedicationCatalogItem.display_name).where(
                    MedicationCatalogItem.source_label == FARMACO_SOURCE_LABEL
                )
            )
        )
        assert not {"AAS", "ACTH", "THC", "Helmintos", "Mercurio"}.intersection(names)

        metformina = _catalog_item_by_name(session, "Metformina")
        assert metformina.status == MedicationCatalogStatus.DRAFT
        assert metformina.review_status == MedicationSourceReviewStatus.DRAFT
        assert metformina.source_version == FARMACO_SOURCE_VERSION
        assert metformina.curated_by == FARMACO_CURATED_BY
        assert metformina.clinical_uses == []
        assert metformina.interaction_alerts == []
        assert metformina.safety_alerts == []
        assert metformina.monitoring_notes == []
        assert metformina.dose_rules == []
        assert "farmaco_txt_evidence" in metformina.tags
        assert "farmaco_evidence:renal" in metformina.tags


def test_farmaco_reconciler_updates_stale_drafts_and_deprecates_obsolete() -> None:
    met_candidate = farmaco_candidate_by_display_name("Metformina")
    assert met_candidate is not None
    met_id = uuid.UUID(met_candidate["catalog_item_id"])

    with _test_session() as session:
        stale = MedicationCatalogItem(
            id=met_id,
            display_name="Metformina antigua",
            generic_name="metformina-antigua",
            status=MedicationCatalogStatus.DRAFT,
            tags=["stale"],
            clinical_uses=[{"indication": "no debe persistir"}],
            interaction_alerts=[{"substance": "x", "effect": "y"}],
            safety_alerts=[{"title": "x", "description": "y"}],
            monitoring_notes=["no debe persistir"],
            source_system=MedicationSourceSystem.LOCAL_CURATED,
            source_label=FARMACO_SOURCE_LABEL,
            source_version="old",
            curated_by="old",
            review_status=MedicationSourceReviewStatus.DRAFT,
        )
        stale.dose_rules = [
            MedicationDoseRule(
                population="adult_general",
                source_system=MedicationSourceSystem.LOCAL_CURATED,
                source_label=FARMACO_SOURCE_LABEL,
                review_status=MedicationSourceReviewStatus.DRAFT,
            )
        ]
        obsolete = MedicationCatalogItem(
            id=uuid.uuid4(),
            display_name="Obsoleto Farmaco",
            generic_name="obsoleto-farmaco",
            status=MedicationCatalogStatus.DRAFT,
            source_system=MedicationSourceSystem.LOCAL_CURATED,
            source_label=FARMACO_SOURCE_LABEL,
            curated_by=FARMACO_CURATED_BY,
            review_status=MedicationSourceReviewStatus.DRAFT,
        )
        session.add_all([stale, obsolete])
        session.commit()

        ensure_farmaco_draft_catalog(session)
        session.commit()

        updated = _catalog_item_by_id(session, met_id)
        assert updated.display_name == "Metformina"
        assert updated.generic_name == "metformina"
        assert updated.clinical_uses == []
        assert updated.interaction_alerts == []
        assert updated.safety_alerts == []
        assert updated.monitoring_notes == []
        assert updated.dose_rules == []

        deprecated = _catalog_item_by_id(session, obsolete.id)
        assert deprecated.status == MedicationCatalogStatus.UNAVAILABLE
        assert deprecated.review_status == MedicationSourceReviewStatus.DEPRECATED


def test_farmaco_reconciler_does_not_modify_reviewed_rows() -> None:
    met_candidate = farmaco_candidate_by_display_name("Metformina")
    assert met_candidate is not None
    met_id = uuid.UUID(met_candidate["catalog_item_id"])

    with _test_session() as session:
        reviewed = MedicationCatalogItem(
            id=met_id,
            display_name="Metformina revisada humana",
            generic_name="metformina-curada",
            status=MedicationCatalogStatus.AVAILABLE,
            tags=["human-reviewed"],
            clinical_uses=[{"indication": "curado humano"}],
            source_system=MedicationSourceSystem.LOCAL_CURATED,
            source_label=FARMACO_SOURCE_LABEL,
            curated_by="humano",
            review_status=MedicationSourceReviewStatus.REVIEWED,
        )
        session.add(reviewed)
        session.commit()

        ensure_farmaco_draft_catalog(session)
        session.commit()

        item = _catalog_item_by_id(session, met_id)
        assert item.display_name == "Metformina revisada humana"
        assert item.status == MedicationCatalogStatus.AVAILABLE
        assert item.review_status == MedicationSourceReviewStatus.REVIEWED
        assert item.tags == ["human-reviewed"]
        assert item.clinical_uses == [{"indication": "curado humano"}]


def test_farmaco_draft_api_and_assistant_use_evidence_as_pending_curation(
    client: TestClient,
    auth_headers,
) -> None:
    auth = auth_headers(client)
    candidate = farmaco_candidate_by_display_name("Metformina")
    assert candidate is not None
    catalog_item_id = candidate["catalog_item_id"]

    detail_response = client.get(f"/api/v1/medication-catalog/{catalog_item_id}", headers=auth)
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["display_name"] == "Metformina"
    assert detail["status"] == "draft"
    assert detail["review_status"] == "draft"
    assert detail["clinical_uses"] == []
    assert detail["interaction_alerts"] == []
    assert detail["safety_alerts"] == []
    assert detail["monitoring_notes"] == []
    assert detail["dose_rules"] == []

    list_response = client.get("/api/v1/medication-catalog?q=Metformina", headers=auth)
    assert list_response.status_code == 200
    assert all(item["id"] != catalog_item_id for item in list_response.json())

    patient_id = create_patient(client, auth, first_name="Farmaco", last_name="TXT")
    create_vitals(client, auth, patient_id, measured_at="2026-06-20T10:00:00Z")
    medication_response = client.post(
        f"/api/v1/patients/{patient_id}/medications",
        headers=auth,
        json={
            "catalog_item_id": catalog_item_id,
            "name": "Metformina",
            "dose": "500 mg",
            "route": "oral",
            "frequency": "cada 12 horas",
            "started_on": "2026-06-20",
        },
    )
    assert medication_response.status_code == 201
    medication = medication_response.json()
    assert medication["source"]["source_label"] == FARMACO_SOURCE_LABEL
    assert medication["source"]["review_status"] == "draft"
    assert any(
        "Sin regla segura disponible" in item
        for item in medication["dose_check_snapshot"]["limitations"]
    )

    suggestions_response = client.post(
        f"/api/v1/patients/{patient_id}/ai/suggestions",
        headers=auth,
        json={"focus": "safety"},
    )
    assert suggestions_response.status_code == 200
    suggestions = suggestions_response.json()["suggestions"]
    titles = [item["title"] for item in suggestions]
    details = " ".join(item["detail"] for item in suggestions)
    assert "Medicacion activa requiere curacion: Metformina" in titles
    assert "Evidencia TXT Farmaco pendiente de curacion humana" in details
    assert "no genera uso, alerta ni dosis automatica" in details
    assert "no propone receta" in details

    intent_response = client.post(
        f"/api/v1/patients/{patient_id}/ai/clinical-intent",
        headers=auth,
        json={"intent_type": "summarize_patient"},
    )
    assert intent_response.status_code == 200
    review_items = intent_response.json()["review_items"]
    farmaco_items = [
        item
        for item in review_items
        if item["label"] == "Metformina: revisar evidencia TXT Farmaco"
    ]
    assert farmaco_items
    assert farmaco_items[0]["source_type"] == "medication"
    assert "No se convirtio en alerta clinica" in farmaco_items[0]["detail"]

    aas = farmaco_candidate_by_display_name("AAS")
    assert aas is not None
    aas_evidence = farmaco_evidence_for_catalog_item_id(aas["catalog_item_id"])
    assert aas_evidence is not None
    assert aas_evidence["decision"] == "needs_review"
    assert aas_evidence["mention_count"] == 0
    assert aas_evidence["evidence_tags"] == []


def _assert_no_long_text_payload(value: object) -> None:
    disallowed_keys = {"text", "excerpt", "fragment", "paragraph", "content"}
    if isinstance(value, dict):
        assert not disallowed_keys.intersection(value.keys())
        for child in value.values():
            _assert_no_long_text_payload(child)
    elif isinstance(value, list):
        for child in value:
            _assert_no_long_text_payload(child)


@contextmanager
def _test_session() -> Iterator[Session]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    testing_session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    with testing_session() as session:
        yield session
    Base.metadata.drop_all(engine)


def _catalog_item_by_name(session: Session, name: str) -> MedicationCatalogItem:
    statement = (
        select(MedicationCatalogItem)
        .options(selectinload(MedicationCatalogItem.dose_rules))
        .where(MedicationCatalogItem.display_name == name)
    )
    item = session.scalar(statement)
    assert item is not None
    return item


def _catalog_item_by_id(session: Session, item_id: uuid.UUID) -> MedicationCatalogItem:
    statement = (
        select(MedicationCatalogItem)
        .options(selectinload(MedicationCatalogItem.dose_rules))
        .where(MedicationCatalogItem.id == item_id)
    )
    item = session.scalar(statement)
    assert item is not None
    return item
