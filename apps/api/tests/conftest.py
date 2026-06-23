from collections.abc import Callable, Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from oneepis_api.core.config import Settings, get_settings
from oneepis_api.db.base import Base
from oneepis_api.db.session import get_session
from oneepis_api.main import app
from oneepis_api.models import audit as _audit_models  # noqa: F401
from oneepis_api.models import clinical_record as _clinical_models  # noqa: F401
from oneepis_api.models import hospitalization as _hospitalization_models  # noqa: F401
from oneepis_api.models import lab as _lab_models  # noqa: F401
from oneepis_api.models import patient as _patient_models  # noqa: F401

AuthHeadersFactory = Callable[..., dict[str, str]]
CreatePatientFactory = Callable[..., str]


@pytest.fixture
def client() -> Iterator[TestClient]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    testing_session = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def override_session() -> Iterator[Session]:
        with testing_session() as session:
            yield session

    def override_settings() -> Settings:
        return Settings(ai_provider="local_rules")

    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[get_settings] = override_settings
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)


@pytest.fixture
def auth_headers(client: TestClient) -> AuthHeadersFactory:
    def login(
        _client: TestClient | None = None,
        email: str = "medico@oneepis.local",
        password: str = "medico",
    ) -> dict[str, str]:
        response = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        assert response.status_code == 200
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    return login


@pytest.fixture
def create_patient_for_permissions(
    client: TestClient,
    auth_headers: AuthHeadersFactory,
) -> CreatePatientFactory:
    def create(
        _client: TestClient | dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
    ) -> str:
        if headers is None and isinstance(_client, dict):
            headers = _client
        active_headers = headers or auth_headers()
        response = client.post(
            "/api/v1/patients",
            headers=active_headers,
            json={
                "first_name": "Permisos",
                "last_name": "Paciente",
                "birth_date": "1990-01-01",
                "sex_at_birth": "unknown",
            },
        )
        assert response.status_code == 201
        return str(response.json()["id"])

    return create
