"""Repository for raw event persistence operations."""

from datetime import datetime

from sqlalchemy.orm import Session

from app.models.raw_event import RawEvent


class RawEventRepository:
    """Repository responsible for raw event persistence operations."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def create(
        self,
        *,
        endpoint_id: str,
        source: str,
        event_type: str,
        event_category: str,
        severity: str,
        event_name: str,
        occurred_at: datetime,
        raw_payload: dict,
        normalized_summary: str,
    ) -> RawEvent:
        """Create and persist a raw telemetry event."""
        event = RawEvent(
            endpoint_id=endpoint_id,
            source=source,
            event_type=event_type,
            event_category=event_category,
            severity=severity,
            event_name=event_name,
            occurred_at=occurred_at,
            raw_payload=raw_payload,
            normalized_summary=normalized_summary,
        )
        self._db.add(event)
        self._db.commit()
        self._db.refresh(event)
        return event
