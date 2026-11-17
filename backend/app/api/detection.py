"""Detection API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.repositories.alert_repository import AlertRepository
from app.repositories.incident_repository import IncidentRepository
from app.schemas.detection import AlertResponse, IncidentResponse
from app.services.detection_service import DetectionService

router = APIRouter(prefix="/detections", tags=["detections"])


def get_detection_service(db: Annotated[Session, Depends(get_db)]) -> DetectionService:
    """Build a detection service for the current request."""
    return DetectionService(AlertRepository(db), IncidentRepository(db))


@router.get("/alerts", response_model=list[AlertResponse])
async def list_alerts(detection_service: Annotated[DetectionService, Depends(get_detection_service)], _: Annotated[User, Depends(get_current_user)]) -> list[AlertResponse]:
    """List generated security alerts for authenticated analysts."""
    return detection_service.list_alerts()


@router.get("/incidents", response_model=list[IncidentResponse])
async def list_incidents(detection_service: Annotated[DetectionService, Depends(get_detection_service)], _: Annotated[User, Depends(get_current_user)]) -> list[IncidentResponse]:
    """List correlated security incidents for authenticated analysts."""
    return detection_service.list_incidents()
