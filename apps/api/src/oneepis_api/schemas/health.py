from oneepis_api.schemas.common import APIModel


class HealthCheck(APIModel):
    status: str
    service: str
    environment: str
    correlation_id: str | None = None
