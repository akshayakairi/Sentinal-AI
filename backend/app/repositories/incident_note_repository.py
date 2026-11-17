"""Repository for analyst notes on incidents."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.incident_note import IncidentNote


class IncidentNoteRepository:
    """Repository for incident note persistence operations."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def list_by_incident(self, incident_id: str) -> list[IncidentNote]:
        """Return notes for an incident ordered by creation time ascending."""
        statement = (
            select(IncidentNote)
            .where(IncidentNote.incident_id == incident_id)
            .order_by(IncidentNote.created_at.asc())
        )
        return list(self._db.execute(statement).scalars().all())

    def create(self, *, incident_id: str, author_user_id: str, body: str) -> IncidentNote:
        """Create and persist a new incident note."""
        note = IncidentNote(
            incident_id=incident_id,
            author_user_id=author_user_id,
            body=body,
        )
        self._db.add(note)
        self._db.commit()
        self._db.refresh(note)
        return note
