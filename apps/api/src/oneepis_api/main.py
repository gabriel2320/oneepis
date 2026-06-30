import uuid

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from oneepis_api.api.v1.router import api_router
from oneepis_api.core.config import Settings, get_settings
from oneepis_api.services.audit import (
    AuditRequestContext,
    clear_audit_request_context,
    set_audit_request_context,
)
from oneepis_api.services.phi_logging import configure_phi_safe_logging

UNSUPPORTED_CONTEXTUAL_ACCESS_HEADERS = (
    "X-OneEpis-Break-Glass",
    "X-OneEpis-Access-Reason",
    "X-OneEpis-Institution",
    "X-OneEpis-Tenant",
    "X-OneEpis-Care-Team",
)


def create_app() -> FastAPI:
    configure_phi_safe_logging()
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
    async def contextual_access_guard_middleware(request: Request, call_next):
        if _uses_unsupported_contextual_access_header(request):
            return JSONResponse(
                {"detail": "Contextual access override is not enabled."},
                status_code=403,
            )
        return await call_next(request)

    @app.middleware("http")
    async def csrf_cookie_middleware(request: Request, call_next):
        if _requires_csrf(request, settings):
            csrf_cookie = request.cookies.get(settings.auth_csrf_cookie_name)
            csrf_header = request.headers.get("X-OneEpis-CSRF")
            if not csrf_cookie or not csrf_header or csrf_cookie != csrf_header:
                return JSONResponse({"detail": "CSRF token missing or invalid"}, status_code=403)
        return await call_next(request)

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


def _requires_csrf(request: Request, settings: Settings) -> bool:
    if request.method not in {"POST", "PUT", "PATCH", "DELETE"}:
        return False
    if request.url.path in {
        "/api/v1/auth/login",
        "/api/v1/auth/password-recovery-requests",
        "/api/v1/auth/unlock-requests",
        "/api/v1/auth/unlock-confirmations",
    }:
        return False
    if request.headers.get("Authorization", "").lower().startswith("bearer "):
        return False
    return settings.auth_session_cookie_name in request.cookies


def _uses_unsupported_contextual_access_header(request: Request) -> bool:
    if not request.url.path.startswith(
        (
            "/api/v1/patients",
            "/api/v1/appointments",
            "/api/v1/hospitalization",
            "/api/v1/medication-catalog",
            "/api/v1/ai",
        )
    ):
        return False
    return any(request.headers.get(header) for header in UNSUPPORTED_CONTEXTUAL_ACCESS_HEADERS)


app = create_app()
