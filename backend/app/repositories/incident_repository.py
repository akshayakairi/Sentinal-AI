"""Incident persistence repository."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.models.incident import Incident


class IncidentRepository:
    """Repository for incident persistence operations."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def list_all(self) -> list[Incident]:
        """Return all incidents ordered by last activity descending."""
        statement = select(Incident).order_by(Incident.last_event_at.desc())
        return list(self._db.execute(statement).scalars().all())

    def get_by_id(self, incident_id: str) -> Incident | None:
        """Return an incident by primary key if present."""
        statement = select(Incident).where(Incident.id == incident_id)
        return self._db.execute(statement).scalar_one_or_none()

    def find_open_by_correlation(
        self,
        *,
        endpoint_id: str,
        correlation_key: str,
        occurred_at: datetime,
        lookback_hours: int = 24,
    ) -> Incident | None:
        """Find a recent open incident matching the correlation key."""
        threshold = occurred_at.astimezone(timezone.utc) - timedelta(hours=lookback_hours)
        statement = select(Incident).where(
            and_(
                Incident.endpoint_id == endpoint_id,
                Incident.correlation_key == correlation_key,
                Incident.status == "open",
                Incident.last_event_at >= threshold,
            )
        )
        return self._db.execute(statement).scalar_one_or_none()

    def create(
        self,
        *,
        endpoint_id: str,
        title: str,
        summary: str,
        severity: str,
        correlation_key: str,
        first_event_at: datetime,
        created_by_alert_id: str,
    ) -> Incident:
        """Create and persist a new incident."""
        incident = Incident(
            endpoint_id=endpoint_id,
            title=title,
            summary=summary,
            severity=severity,
            correlation_key=correlation_key,
            first_event_at=first_event_at,
            last_event_at=first_event_at,
            created_by_alert_id=created_by_alert_id,
        )
        self._db.add(incident)
        self._db.commit()
        self._db.refresh(incident)
        return incident

    def update_correlation(
        self,
        incident: Incident,
        *,
        severity: str,
        summary: str,
        last_event_at: datetime,
    ) -> Incident:
        """Update an existing incident with a newly correlated alert."""
        incident.severity = self._max_severity(incident.severity, severity)
        incident.summary = summary
        incident.last_event_at = last_event_at
        self._db.add(incident)
        self._db.commit()
        self._db.refresh(incident)
        return incident

    def update_management(
        self,
        incident: Incident,
        *,
        status: str,
        assigned_to_user_id: str | None,
        resolution_summary: str | None,
    ) -> Incident:
        """Update workflow-related incident fields."""
        incident.status = status
        incident.assigned_to_user_id = assigned_to_user_id
        incident.resolution_summary = resolution_summary
        self._db.add(incident)
        self._db.commit()
        self._db.refresh(incident)
        return incident

    @staticmethod
    def _max_severity(current: str, incoming: str) -> str:
        order = {"low": 1, "medium": 2, "high": 3, "critical": 4}
        return incoming if order.get(incoming, 0) > order.get(current, 0) else current
