"""Alert persistence repository."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.alert import Alert


class AlertRepository:
    """Repository for alert persistence operations."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def list_all(self) -> list[Alert]:
        """Return all alerts ordered by creation time descending."""
        statement = select(Alert).order_by(Alert.created_at.desc())
        return list(self._db.execute(statement).scalars().all())

    def list_by_incident(self, incident_id: str) -> list[Alert]:
        """Return alerts attached to an incident ordered by creation time ascending."""
        statement = (
            select(Alert)
            .where(Alert.incident_id == incident_id)
            .order_by(Alert.created_at.asc())
        )
        return list(self._db.execute(statement).scalars().all())

    def create(
        self,
        *,
        raw_event_id: str,
        endpoint_id: str,
        title: str,
        description: str,
        severity: str,
        rule_name: str,
        correlation_key: str,
        mitre_technique: str | None,
    ) -> Alert:
        """Create and persist a new alert."""
        alert = Alert(
            raw_event_id=raw_event_id,
            endpoint_id=endpoint_id,
            title=title,
            description=description,
            severity=severity,
            rule_name=rule_name,
            correlation_key=correlation_key,
            mitre_technique=mitre_technique,
        )
        self._db.add(alert)
        self._db.commit()
        self._db.refresh(alert)
        return alert

    def assign_to_incident(self, alert: Alert, incident_id: str) -> Alert:
        """Link an alert to an incident."""
        alert.incident_id = incident_id
        self._db.add(alert)
        self._db.commit()
        self._db.refresh(alert)
        return alert
