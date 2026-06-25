from fastapi.testclient import TestClient


def test_assistant_timeline_returns_longitudinal_sources_without_writing_audit(
    client: TestClient,
    auth_headers,
) -> None:
    auth = auth_headers(client)
    patient = client.post(
        "/api/v1/patients",
        headers=auth,
        json={
            "first_name": "Asistente",
            "last_name": "Lectura",
            "birth_date": "1980-01-01",
            "sex_at_birth": "unknown",
        },
    ).json()
    patient_id = patient["id"]
    encounter = client.post(
        f"/api/v1/patients/{patient_id}/encounters",
        headers=auth,
        json={
            "type": "hospitalization",
            "status": "in_progress",
            "reason": "Ingreso por control longitudinal",
            "started_at": "2026-06-20T08:00:00Z",
            "location_label": "Medicina / 301",
        },
    ).json()

    client.post(
        f"/api/v1/patients/{patient_id}/clinical-entries",
        headers=auth,
        json={
            "encounter_id": encounter["id"],
            "kind": "progress",
            "status": "signed",
            "occurred_at": "2026-06-20T09:00:00Z",
            "title": "Evolucion de ingreso",
            "subjective": "Paciente refiere disnea.",
            "objective": "SatO2 baja.",
            "assessment": "Cuadro respiratorio en estudio.",
            "plan": "Oxigeno y control.",
        },
    )
    client.post(
        f"/api/v1/patients/{patient_id}/clinical-events",
        headers=auth,
        json={
            "encounter_id": encounter["id"],
            "event_type": "symptom",
            "occurred_at": "2026-06-20T09:10:00Z",
            "summary": "Disnea de esfuerzo",
            "source_type": "manual",
        },
    )
    client.post(
        f"/api/v1/patients/{patient_id}/vital-signs",
        headers=auth,
        json={
            "measured_at": "2026-06-20T09:15:00Z",
            "systolic_bp": 118,
            "diastolic_bp": 72,
            "heart_rate_bpm": 92,
            "oxygen_saturation_pct": "91",
        },
    )
    client.post(
        f"/api/v1/patients/{patient_id}/problems",
        headers=auth,
        json={"title": "Disnea", "onset_date": "2026-06-19", "notes": "Problema activo."},
    )
    client.post(
        f"/api/v1/patients/{patient_id}/medications",
        headers=auth,
        json={
            "name": "Salbutamol",
            "dose": "2 puff",
            "route": "inhalatoria",
            "frequency": "cada 6 horas",
            "started_on": "2026-06-20",
        },
    )
    client.post(
        f"/api/v1/patients/{patient_id}/allergies",
        headers=auth,
        json={
            "substance": "Penicilina",
            "reaction": "Exantema",
            "severity": "moderate",
            "recorded_at": "2026-06-18T12:00:00Z",
        },
    )
    client.post(
        f"/api/v1/hospitalization/patients/{patient_id}/indications",
        headers=auth,
        json={
            "status": "draft",
            "indicated_at": "2026-06-20T10:00:00Z",
            "title": "Oxigenoterapia",
            "indication_text": "Oxigeno por naricera segun saturacion.",
            "rationale": "Hipoxemia documentada.",
        },
    )

    audit_before = client.get(f"/api/v1/patients/{patient_id}/audit-events", headers=auth).json()
    response = client.get(
        f"/api/v1/patients/{patient_id}/assistant/timeline",
        headers=auth,
    )
    audit_after = client.get(f"/api/v1/patients/{patient_id}/audit-events", headers=auth).json()

    assert response.status_code == 200
    timeline = response.json()
    assert timeline["patient_id"] == patient_id
    source_types = {item["source_type"] for item in timeline["items"]}
    assert {
        "encounter",
        "clinical_entry",
        "clinical_event",
        "vital_sign",
        "active_problem",
        "medication",
        "allergy",
        "hospital_indication",
    }.issubset(source_types)
    assert timeline["items"][0]["source_type"] == "hospital_indication"
    assert any(item["summary"] == "Disnea de esfuerzo" for item in timeline["items"])
    assert any("SatO2 91 %" in item["summary"] for item in timeline["items"])
    assert timeline["missing"] == []
    assert "solo lectura" in timeline["limits"][0]
    assert len(audit_after) == len(audit_before)


def test_assistant_timeline_declares_missing_sources_for_empty_patient(
    client: TestClient,
    auth_headers,
) -> None:
    auth = auth_headers(client)
    patient = client.post(
        "/api/v1/patients",
        headers=auth,
        json={
            "first_name": "Sin",
            "last_name": "Fuentes",
            "birth_date": "1990-01-01",
            "sex_at_birth": "unknown",
        },
    ).json()

    response = client.get(
        f"/api/v1/patients/{patient['id']}/assistant/timeline",
        headers=auth,
    )

    assert response.status_code == 200
    timeline = response.json()
    assert timeline["items"] == []
    assert "La historia longitudinal no tiene fuentes disponibles" in timeline["missing"][-1]


def test_readonly_user_can_read_assistant_timeline(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
) -> None:
    patient_id = create_patient_for_permissions(client, auth_headers(client))
    readonly_auth = auth_headers(client, email="lector@oneepis.local", password="lector")

    response = client.get(
        f"/api/v1/patients/{patient_id}/assistant/timeline",
        headers=readonly_auth,
    )

    assert response.status_code == 200
    assert response.json()["patient_id"] == patient_id


def test_assistant_timeline_requires_authentication(client: TestClient) -> None:
    response = client.get(
        "/api/v1/patients/11111111-1111-4111-8111-111111111111/assistant/timeline"
    )

    assert response.status_code == 401
