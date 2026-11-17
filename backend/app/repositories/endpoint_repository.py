"""Repository for endpoint persistence operations."""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.endpoint import Endpoint


class EndpointRepository:
    """Repository responsible for endpoint persistence operations."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def list_all(self) -> list[Endpoint]:
        """Return all endpoints ordered by hostname."""
        statement = select(Endpoint).order_by(Endpoint.hostname.asc())
        return list(self._db.execute(statement).scalars().all())

    def get_by_hostname(self, hostname: str) -> Endpoint | None:
        """Return an endpoint by hostname if present."""
        statement = select(Endpoint).where(Endpoint.hostname == hostname.lower())
        return self._db.execute(statement).scalar_one_or_none()

    def create(self, *, hostname: str, operating_system: str, agent_version: str, last_seen_at: datetime) -> Endpoint:
        """Create and persist a new endpoint."""
        endpoint = Endpoint(
            hostname=hostname.lower(),
            operating_system=operating_system,
            agent_version=agent_version,
            last_seen_at=last_seen_at,
        )
        self._db.add(endpoint)
        self._db.commit()
        self._db.refresh(endpoint)
        return endpoint

    def update_last_seen(self, endpoint: Endpoint, *, operating_system: str, agent_version: str, last_seen_at: datetime) -> Endpoint:
        """Update mutable endpoint metadata when new telemetry arrives."""
        endpoint.operating_system = operating_system
        endpoint.agent_version = agent_version
        endpoint.last_seen_at = last_seen_at
        self._db.add(endpoint)
        self._db.commit()
        self._db.refresh(endpoint)
        return endpoint
