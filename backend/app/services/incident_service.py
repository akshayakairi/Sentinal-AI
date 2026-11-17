"""Incident management service."""

from fastapi import HTTPException, status

from app.repositories.alert_repository import AlertRepository
from app.repositories.incident_note_repository import IncidentNoteRepository
from app.repositories.incident_repository import IncidentRepository
from app.repositories.user_repository import UserRepository
from app.schemas.incident_management import (
    IncidentDetailResponse,
    IncidentNoteCreateRequest,
    IncidentNoteResponse,
    IncidentUpdateRequest,
    TimelineEntry,
)

ALLOWED_TRANSITIONS = {
    "open": {"open", "in_progress", "resolved", "closed"},
    "in_progress": {"in_progress", "resolved", "closed"},
    "resolved": {"resolved", "closed"},
    "closed": {"closed"},
}


class IncidentService:
    """Manage analyst workflows for correlated incidents."""

    def __init__(
        self,
        incident_repository: IncidentRepository,
        incident_note_repository: IncidentNoteRepository,
        alert_repository: AlertRepository,
        user_repository: UserRepository,
    ) -> None:
        self._incident_repository = incident_repository
        self._incident_note_repository = incident_note_repository
        self._alert_repository = alert_repository
        self._user_repository = user_repository

    def list_incidents(self) -> list[IncidentDetailResponse]:
        """Return all incidents for analyst workflows."""
        incidents = self._incident_repository.list_all()
        return [IncidentDetailResponse.model_validate(incident) for incident in incidents]

    def get_incident(self, incident_id: str) -> IncidentDetailResponse:
        """Return a single incident by id."""
        incident = self._get_existing_incident(incident_id)
        return IncidentDetailResponse.model_validate(incident)

    def update_incident(self, incident_id: str, payload: IncidentUpdateRequest) -> IncidentDetailResponse:
        """Update workflow state for an incident."""
        incident = self._get_existing_incident(incident_id)
        self._validate_transition(current_status=incident.status, requested_status=payload.status)

        if payload.assigned_to_user_id is not None:
            assigned_user = self._user_repository.get_by_id(payload.assigned_to_user_id)
            if assigned_user is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Assigned user was not found.",
                )

        if payload.status in {"resolved", "closed"} and not payload.resolution_summary:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Resolution summary is required when resolving or closing an incident.",
            )

        updated = self._incident_repository.update_management(
            incident,
            status=payload.status,
            assigned_to_user_id=payload.assigned_to_user_id,
            resolution_summary=payload.resolution_summary,
        )
        return IncidentDetailResponse.model_validate(updated)

    def add_note(self, incident_id: str, payload: IncidentNoteCreateRequest) -> IncidentNoteResponse:
        """Add an analyst note to an incident."""
        self._get_existing_incident(incident_id)

        author = self._user_repository.get_by_id(payload.author_user_id)
        if author is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Note author was not found.",
            )

        note = self._incident_note_repository.create(
            incident_id=incident_id,
            author_user_id=payload.author_user_id,
            body=payload.body,
        )
        return IncidentNoteResponse.model_validate(note)

    def list_notes(self, incident_id: str) -> list[IncidentNoteResponse]:
        """List analyst notes for an incident."""
        self._get_existing_incident(incident_id)
        notes = self._incident_note_repository.list_by_incident(incident_id)
        return [IncidentNoteResponse.model_validate(note) for note in notes]

    def get_timeline(self, incident_id: str) -> list[TimelineEntry]:
        """Return a merged timeline of alerts and analyst notes for an incident."""
        self._get_existing_incident(incident_id)
        alerts = self._alert_repository.list_by_incident(incident_id)
        notes = self._incident_note_repository.list_by_incident(incident_id)

        entries = [
            TimelineEntry(
                entry_type="alert",
                occurred_at=alert.created_at,
                title=alert.title,
                detail=alert.description,
                actor_user_id=None,
                related_id=alert.id,
            )
            for alert in alerts
        ]
        entries.extend(
            TimelineEntry(
                entry_type="note",
                occurred_at=note.created_at,
                title="Analyst Note",
                detail=note.body,
                actor_user_id=note.author_user_id,
                related_id=note.id,
            )
            for note in notes
        )
        return sorted(entries, key=lambda entry: entry.occurred_at)

    def _get_existing_incident(self, incident_id: str):
        incident = self._incident_repository.get_by_id(incident_id)
        if incident is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Incident was not found.",
            )
        return incident

    @staticmethod
    def _validate_transition(*, current_status: str, requested_status: str) -> None:
        allowed = ALLOWED_TRANSITIONS.get(current_status, {current_status})
        if requested_status not in allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot transition incident from '{current_status}' to '{requested_status}'.",
            )
