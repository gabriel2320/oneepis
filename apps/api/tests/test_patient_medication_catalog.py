from fastapi.testclient import TestClient
from patient_ai_helpers import audit_events, create_patient

from oneepis_api.services.medication_catalog import DEMO_ANALGESIC_ID


def test_medication_catalog_validation_and_override_audit(
    client: TestClient,
    auth_headers,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient(client, auth, first_name="Med", last_name="Catalogo")

    catalog_response = client.get("/api/v1/medication-catalog", headers=auth)
    assert catalog_response.status_code == 200
    catalog = catalog_response.json()
    demo_item = next(item for item in catalog if item["id"] == str(DEMO_ANALGESIC_ID))
    assert demo_item["source_system"] == "local_curated"
    assert demo_item["source_label"] == "Fixture demo OneEpis; no uso clinico"
    assert demo_item["dose_rules"][0]["review_status"] == "reviewed"
    assert demo_item["clinical_uses"][0]["indication"] == "Dolor o fiebre demo"
    assert demo_item["administration_routes"] == ["oral"]
    assert demo_item["interaction_alerts"][0]["substance"] == "interaccion-demo"
    assert demo_item["safety_alerts"][0]["title"] == "Alerta demo"
    assert demo_item["monitoring_notes"]

    validation_response = client.post(
        f"/api/v1/patients/{patient_id}/medications/validate-draft",
        headers=auth,
        json={
            "catalog_item_id": str(DEMO_ANALGESIC_ID),
            "name": demo_item["display_name"],
            "dose": "1500 mg",
            "route": "oral",
            "frequency": "cada 8 horas",
        },
    )
    assert validation_response.status_code == 200
    validation = validation_response.json()
    assert validation["blocking"] is True
    assert validation["applies_changes"] is False
    assert validation["warnings"][0]["requires_override"] is True

    blocked_create = client.post(
        f"/api/v1/patients/{patient_id}/medications",
        headers=auth,
        json={
            "catalog_item_id": str(DEMO_ANALGESIC_ID),
            "name": demo_item["display_name"],
            "dose": "1500 mg",
            "route": "oral",
            "frequency": "cada 8 horas",
        },
    )
    assert blocked_create.status_code == 422

    override_create = client.post(
        f"/api/v1/patients/{patient_id}/medications",
        headers=auth,
        json={
            "catalog_item_id": str(DEMO_ANALGESIC_ID),
            "name": demo_item["display_name"],
            "dose": "1500 mg",
            "route": "oral",
            "frequency": "cada 8 horas",
            "dose_override_reason": "Decision clinica documentada en demo.",
        },
    )
    assert override_create.status_code == 201
    medication = override_create.json()
    assert medication["catalog_item_id"] == str(DEMO_ANALGESIC_ID)
    assert medication["dose_check_snapshot"]["blocking"] is True
    assert medication["dose_override_reason"] == "Decision clinica documentada en demo."
    assert medication["source"]["source_system"] == "local_curated"
    assert medication["source"]["source_label"] == "Fixture demo OneEpis; no uso clinico"
    assert medication["source"]["review_status"] == "reviewed"
    assert medication["missing_fields"] == []

    medication_events = [
        item
        for item in audit_events(client, auth, patient_id)
        if item["action"] == "medication.created"
    ]
    assert medication_events[0]["extra_data"]["dose_warning_count"] == 1
    assert medication_events[0]["extra_data"]["dose_override"] is True


def test_medication_read_exposes_missing_fields_for_unlinked_manual_medication(
    client: TestClient,
    auth_headers,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient(client, auth, first_name="Med", last_name="Faltantes")
    create_response = client.post(
        f"/api/v1/patients/{patient_id}/medications",
        headers=auth,
        json={"name": "Medicamento manual sin pauta"},
    )
    assert create_response.status_code == 201
    medication = create_response.json()
    assert medication["source"] is None
    assert medication["missing_fields"] == ["dose", "route", "frequency", "source"]

    list_response = client.get(f"/api/v1/patients/{patient_id}/medications", headers=auth)
    assert list_response.status_code == 200
    listed = list_response.json()[0]
    assert listed["source"] is None
    assert listed["missing_fields"] == ["dose", "route", "frequency", "source"]


def test_medication_drafting_context_readonly_and_no_executable_prescription(
    client: TestClient,
    auth_headers,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient(client, auth, first_name="Med", last_name="Contexto")
    create_response = client.post(
        f"/api/v1/patients/{patient_id}/medications",
        headers=auth,
        json={
            "catalog_item_id": str(DEMO_ANALGESIC_ID),
            "name": "Analgesico demo 500 mg comprimido",
            "dose": "500 mg",
            "route": "oral",
            "frequency": "cada 8 horas",
        },
    )
    assert create_response.status_code == 201

    readonly_auth = auth_headers(client, email="lector@oneepis.local", password="lector")
    context_response = client.get(
        f"/api/v1/patients/{patient_id}/medication-drafting-context",
        headers=readonly_auth,
    )
    readonly_create = client.post(
        f"/api/v1/patients/{patient_id}/medications",
        headers=readonly_auth,
        json={"name": "No permitido"},
    )

    assert context_response.status_code == 200
    context = context_response.json()
    assert context["applies_changes"] is False
    assert "firma ni folio" in context["limitations"][0]
    assert context["active_medications"][0]["name"] == "Analgesico demo 500 mg comprimido"
    assert context["active_medications"][0]["source"]["source_system"] == "local_curated"
    assert context["active_medications"][0]["missing_fields"] == []
    assert context["suggested_catalog_items"]
    assert readonly_create.status_code == 403
