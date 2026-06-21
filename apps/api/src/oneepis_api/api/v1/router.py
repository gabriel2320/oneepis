from fastapi import APIRouter

from oneepis_api.api.v1.routes import (
    ai,
    auth,
    health,
    hospitalization,
    hospitalization_daily_sheets,
    patients,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(patients.router)
api_router.include_router(hospitalization.router)
api_router.include_router(hospitalization_daily_sheets.router)
api_router.include_router(ai.router)
