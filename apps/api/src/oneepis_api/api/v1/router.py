from fastapi import APIRouter

from oneepis_api.api.v1.routes import ai, health, patients

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(patients.router)
api_router.include_router(ai.router)
