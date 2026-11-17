"""Endpoint event ingestion API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.repositories.alert_repository import AlertRepository
from app.repositories.endpoint_repository import EndpointRepository
from app.repositories.incident_repository import IncidentRepository
from app.repositories.raw_event_repository import RawEventRepository
from app.schemas.ingestion import EndpointResponse, EventIngestionRequest, EventIngestionResponse
from app.services.detection_service import DetectionService
from app.services.ingestion_service import IngestionService

router = APIRouter(prefix="/ingestion", tags=["ingestion"])


def get_ingestion_service(db: Annotated[Session, Depends(get_db)]) -> IngestionService:
    """Build an ingestion service for the current request."""
    return IngestionService(EndpointRepository(db), RawEventRepository(db), DetectionService(AlertRepository(db), IncidentRepository(db)))


@router.post("/events", response_model=EventIngestionResponse, status_code=201)
async def ingest_event(payload: EventIngestionRequest, ingestion_service: Annotated[IngestionService, Depends(get_ingestion_service)]) -> EventIngestionResponse:
    """Ingest a single endpoint event from a trusted endpoint-agent channel."""
    return ingestion_service.ingest_event(payload)


@router.get("/endpoints", response_model=list[EndpointResponse])
async def list_endpoints(ingestion_service: Annotated[IngestionService, Depends(get_ingestion_service)], _: Annotated[User, Depends(get_current_user)]) -> list[EndpointResponse]:
    """List monitored endpoints for authenticated analysts."""
    return ingestion_service.list_endpoints()
