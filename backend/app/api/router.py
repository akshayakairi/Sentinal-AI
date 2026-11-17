"""Top-level API router registration."""

from fastapi import APIRouter

from app.api.audit import router as audit_router
from app.api.auth import router as auth_router
from app.api.detection import router as detection_router
from app.api.health import router as health_router
from app.api.incidents import router as incidents_router
from app.api.ingestion import router as ingestion_router
from app.api.reasoning import router as reasoning_router
from app.api.threat_intelligence import router as threat_intelligence_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(audit_router)
api_router.include_router(detection_router)
api_router.include_router(health_router)
api_router.include_router(incidents_router)
api_router.include_router(ingestion_router)
api_router.include_router(reasoning_router)
api_router.include_router(threat_intelligence_router)
