"""Incident management API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import require_analyst, require_authenticated
from app.db.session import get_db
from app.models.user import User
from app.repositories.alert_repository import AlertRepository
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.incident_note_repository import IncidentNoteRepository
from app.repositories.incident_repository import IncidentRepository
from app.repositories.user_repository import UserRepository
from app.schemas.audit import AuditLogCreate
from app.schemas.incident_management import (
    IncidentDetailResponse,
    IncidentNoteCreateRequest,
    IncidentNoteResponse,
    IncidentUpdateRequest,
    TimelineEntry,
)
from app.services.audit_service import AuditService
from app.services.incident_service import IncidentService

router = APIRouter(prefix="/incidents", tags=["incidents"])


def get_incident_service(db: Annotated[Session, Depends(get_db)]) -> IncidentService:
    """Build an incident management service for the current request."""
    return IncidentService(
        IncidentRepository(db),
        IncidentNoteRepository(db),
        AlertRepository(db),
        UserRepository(db),
    )


def get_audit_service(db: Annotated[Session, Depends(get_db)]) -> AuditService:
    """Build an audit service for incident workflow activity."""
    return AuditService(AuditLogRepository(db))


@router.get("", response_model=list[IncidentDetailResponse])
async def list_incidents(
    incident_service: Annotated[IncidentService, Depends(get_incident_service)],
    _: Annotated[User, Depends(require_authenticated)],
) -> list[IncidentDetailResponse]:
    """List incidents for authenticated analyst workflows."""
    return incident_service.list_incidents()


@router.get("/{incident_id}", response_model=IncidentDetailResponse)
async def get_incident(
    incident_id: str,
    incident_service: Annotated[IncidentService, Depends(get_incident_service)],
    _: Annotated[User, Depends(require_authenticated)],
) -> IncidentDetailResponse:
    """Retrieve detailed incident information."""
    return incident_service.get_incident(incident_id)


@router.patch("/{incident_id}", response_model=IncidentDetailResponse)
async def update_incident(
    incident_id: str,
    payload: IncidentUpdateRequest,
    incident_service: Annotated[IncidentService, Depends(get_incident_service)],
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
    current_user: Annotated[User, Depends(require_analyst)],
) -> IncidentDetailResponse:
    """Update incident workflow fields such as status and assignment."""
    updated = incident_service.update_incident(incident_id, payload)
    audit_service.record(
        AuditLogCreate(
            actor_user_id=current_user.id,
            action="incident.updated",
            resource_type="incident",
            resource_id=incident_id,
            details={
                "status": payload.status,
                "assigned_to_user_id": payload.assigned_to_user_id,
                "has_resolution_summary": payload.resolution_summary is not None,
            },
        )
    )
    return updated


@router.get("/{incident_id}/notes", response_model=list[IncidentNoteResponse])
async def list_notes(
    incident_id: str,
    incident_service: Annotated[IncidentService, Depends(get_incident_service)],
    _: Annotated[User, Depends(require_authenticated)],
) -> list[IncidentNoteResponse]:
    """List analyst notes for an incident."""
    return incident_service.list_notes(incident_id)


@router.post("/{incident_id}/notes", response_model=IncidentNoteResponse, status_code=201)
async def add_note(
    incident_id: str,
    payload: IncidentNoteCreateRequest,
    incident_service: Annotated[IncidentService, Depends(get_incident_service)],
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
    current_user: Annotated[User, Depends(require_analyst)],
) -> IncidentNoteResponse:
    """Add an analyst note attributed to the authenticated user."""
    if payload.author_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Notes must be authored by the authenticated user.",
        )
    note = incident_service.add_note(incident_id, payload)
    audit_service.record(
        AuditLogCreate(
            actor_user_id=current_user.id,
            action="incident.note_created",
            resource_type="incident",
            resource_id=incident_id,
            details={"note_id": note.id},
        )
    )
    return note


@router.get("/{incident_id}/timeline", response_model=list[TimelineEntry])
async def get_timeline(
    incident_id: str,
    incident_service: Annotated[IncidentService, Depends(get_incident_service)],
    _: Annotated[User, Depends(require_authenticated)],
) -> list[TimelineEntry]:
    """Return the merged investigation timeline for an incident."""
    return incident_service.get_timeline(incident_id)
