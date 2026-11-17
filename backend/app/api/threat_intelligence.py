"""Threat-intelligence enrichment routes."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.models.user import User
from app.repositories.alert_repository import AlertRepository
from app.repositories.incident_repository import IncidentRepository
from app.schemas.threat_intelligence import ThreatIntelligenceRequest, ThreatIntelligenceResponse
from app.services.threat_intelligence import NvdCveLookupProvider
from app.services.threat_intelligence_service import ThreatIntelligenceService

router = APIRouter(prefix="/incidents", tags=["threat-intelligence"])


def get_threat_intelligence_service(
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> ThreatIntelligenceService:
    """Build the threat-intelligence service for the current request."""
    return ThreatIntelligenceService(
        IncidentRepository(db),
        AlertRepository(db),
        NvdCveLookupProvider(
            settings.nvd_cve_api_url,
            settings.nvd_api_key,
            settings.threat_intelligence_timeout_seconds,
        ),
    )


@router.post("/{incident_id}/threat-intelligence", response_model=ThreatIntelligenceResponse)
async def enrich_incident(
    incident_id: str,
    payload: ThreatIntelligenceRequest,
    threat_intelligence_service: Annotated[
        ThreatIntelligenceService, Depends(get_threat_intelligence_service)
    ],
    _: Annotated[User, Depends(get_current_user)],
) -> ThreatIntelligenceResponse:
    """Return external intelligence context for an incident."""
    return threat_intelligence_service.enrich(incident_id, payload)


