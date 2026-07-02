from __future__ import annotations

import uuid
from collections.abc import Iterator
from contextlib import contextmanager

from fastapi.testclient import TestClient
from sqlalchemy import Select, select, text
from sqlalchemy.orm import Session

from oneepis_api.db.session import get_session
from oneepis_api.main import app
from oneepis_api.models.clinical_record import RecordStatus, VitalSign


def test_vital_signs_recent_query_uses_patient_measured_at_index(
    client: TestClient,
    auth_headers,
    create_patient_for_permissions,
) -> None:
    auth = auth_headers(client)
    patient_id = create_patient_for_permissions(client, auth)
    for day in range(1, 4):
        response = client.post(
            f"/api/v1/patients/{patient_id}/vital-signs",
            headers=auth,
            json={
                "measured_at": f"2026-06-2{day}T12:00:00Z",
                "heart_rate_bpm": 80 + day,
            },
        )
        assert response.status_code == 201

    with _test_session() as session:
        statement = (
            select(VitalSign)
            .where(
                VitalSign.patient_id == uuid.UUID(patient_id),
                VitalSign.status != RecordStatus.ENTERED_IN_ERROR,
            )
            .order_by(VitalSign.measured_at.desc())
            .limit(10)
        )
        sql = _literal_sql(session, statement)
        old_patient_index_sql = sql.replace(
            "FROM vital_signs",
            "FROM vital_signs INDEXED BY ix_vital_signs_patient_id",
            1,
        )
        old_plan = _explain_sql(session, old_patient_index_sql)
        new_plan = _explain_sql(session, sql)

    assert "USE TEMP B-TREE FOR ORDER BY" in old_plan
    assert "ix_vital_signs_patient_id_measured_at" in new_plan
    assert "USE TEMP B-TREE FOR ORDER BY" not in new_plan


def _literal_sql(session: Session, statement: Select[tuple[VitalSign]]) -> str:
    return str(
        statement.compile(
            dialect=session.get_bind().dialect,
            compile_kwargs={"literal_binds": True},
        )
    )


def _explain_sql(session: Session, sql: str) -> str:
    rows = session.execute(text(f"EXPLAIN QUERY PLAN {sql}")).all()
    return " | ".join(str(row[-1]) for row in rows)


@contextmanager
def _test_session() -> Iterator[Session]:
    session_provider = app.dependency_overrides[get_session]
    session_iterator = session_provider()
    session = next(session_iterator)
    try:
        yield session
    finally:
        session_iterator.close()
