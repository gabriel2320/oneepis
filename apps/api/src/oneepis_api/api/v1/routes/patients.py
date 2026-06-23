from fastapi import APIRouter

from oneepis_api.api.v1.routes.patient_ai import router as ai_router
from oneepis_api.api.v1.routes.patient_allergies import router as allergies_router
from oneepis_api.api.v1.routes.patient_assistant import router as assistant_router
from oneepis_api.api.v1.routes.patient_audit import router as audit_router
from oneepis_api.api.v1.routes.patient_clinical_risks import router as clinical_risks_router
from oneepis_api.api.v1.routes.patient_core import router as core_router
from oneepis_api.api.v1.routes.patient_encounters import router as encounters_router
from oneepis_api.api.v1.routes.patient_entries import router as entries_router
from oneepis_api.api.v1.routes.patient_events import router as events_router
from oneepis_api.api.v1.routes.patient_lab_panels import router as lab_panels_router
from oneepis_api.api.v1.routes.patient_medications import router as medications_router
from oneepis_api.api.v1.routes.patient_problems import router as problems_router
from oneepis_api.api.v1.routes.patient_vitals import router as vitals_router

router = APIRouter()

router.include_router(core_router)
router.include_router(encounters_router)
router.include_router(entries_router)
router.include_router(events_router)
router.include_router(ai_router)
router.include_router(assistant_router)
router.include_router(allergies_router)
router.include_router(medications_router)
router.include_router(problems_router)
router.include_router(vitals_router)
router.include_router(lab_panels_router)
router.include_router(clinical_risks_router)
router.include_router(audit_router)
