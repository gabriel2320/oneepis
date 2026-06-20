import uuid

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request

from oneepis_api.api.v1.router import api_router
from oneepis_api.core.config import get_settings
from oneepis_api.services.audit import (
    AuditRequestContext,
    clear_audit_request_context,
    set_audit_request_context,
)


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="OneEpis Clinical API",
        version="0.1.0",
        description="API modular para ficha clinica inteligente y auditable.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def audit_context_middleware(request: Request, call_next):
        correlation_id = _normalize_correlation_id(
            request.headers.get("X-OneEpis-Correlation-ID")
            or request.headers.get("X-Request-ID")
        )
        set_audit_request_context(
            AuditRequestContext(
                correlation_id=correlation_id,
                request_method=request.method,
                request_path=request.url.path,
            )
        )
        try:
            response = await call_next(request)
        finally:
            clear_audit_request_context()
        response.headers["X-OneEpis-Correlation-ID"] = correlation_id
        return response

    app.include_router(api_router, prefix="/api/v1")
    return app


def _normalize_correlation_id(value: str | None) -> str:
    if value:
        normalized = value.strip()[:80]
        if normalized:
            return normalized
    return f"oneepis-{uuid.uuid4()}"


app = create_app()
