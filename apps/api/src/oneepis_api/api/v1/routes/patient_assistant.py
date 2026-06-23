from __future__ import annotations

from fastapi import APIRouter

from .patient_assistant_chart import router as chart_router
from .patient_assistant_common import date_or_created_at as _date_or_created_at
from .patient_assistant_correlation import router as correlation_router
from .patient_assistant_search import router as search_router
from .patient_assistant_timeline import router as timeline_router
from .patient_shared import PATIENT_ROUTER_OPTIONS

router = APIRouter(**PATIENT_ROUTER_OPTIONS)
router.include_router(timeline_router)
router.include_router(search_router)
router.include_router(chart_router)
router.include_router(correlation_router)

__all__ = ["router", "_date_or_created_at"]
