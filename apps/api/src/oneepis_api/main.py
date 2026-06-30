import uuid

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from oneepis_api.api.v1.router import api_router
from oneepis_api.core.clinical_access import PROTECTED_CLINICAL_ROUTE_PREFIXES
from oneepis_api.core.config import Settings, get_settings
from oneepis_api.db.session import get_session
from oneepis_api.services.audit import (
    AuditRequestContext,
    clear_audit_request_context,
    record_audit_event,
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
        blocked_headers = _unsupported_contextual_access_headers(request)
        if blocked_headers:
            _record_contextual_access_header_block(request, blocked_headers)
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


def _unsupported_contextual_access_headers(request: Request) -> tuple[str, ...]:
    if not request.url.path.startswith(PROTECTED_CLINICAL_ROUTE_PREFIXES):
        return ()
    return tuple(
        header for header in UNSUPPORTED_CONTEXTUAL_ACCESS_HEADERS if request.headers.get(header)
    )


def _record_contextual_access_header_block(
    request: Request,
    blocked_headers: tuple[str, ...],
) -> None:
    session_provider = request.app.dependency_overrides.get(get_session, get_session)
    session_iterator = session_provider()
    session = next(session_iterator)
    try:
        record_audit_event(
            session,
            action="security.contextual_access_header_blocked",
            entity_type="security",
            entity_id=None,
            actor_id="system",
            metadata={
                "blocked_headers": sorted(blocked_headers),
                "header_count": len(blocked_headers),
            },
        )
        session.commit()
    finally:
        session_iterator.close()


app = create_app()
