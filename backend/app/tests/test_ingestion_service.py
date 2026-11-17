"""Ingestion service tests."""

from dataclasses import dataclass
from datetime import datetime, timezone

from app.schemas.ingestion import EndpointRegistration, EventIngestionRequest
from app.services.ingestion_service import IngestionService


@dataclass
class FakeEndpoint:
    """Simple endpoint test double."""

    id: str
    hostname: str
    operating_system: str
    agent_version: str
    last_seen_at: datetime
    created_at: datetime


@dataclass
class FakeRawEvent:
    """Simple raw event test double."""

    id: str


class FakeEndpointRepository:
    """In-memory endpoint repository used for service testing."""

    def __init__(self) -> None:
        self._endpoints: dict[str, FakeEndpoint] = {}

    def list_all(self) -> list[FakeEndpoint]:
        return list(self._endpoints.values())

    def get_by_hostname(self, hostname: str) -> FakeEndpoint | None:
        return self._endpoints.get(hostname.lower())

    def create(self, *, hostname: str, operating_system: str, agent_version: str, last_seen_at: datetime) -> FakeEndpoint:
        endpoint = FakeEndpoint(
            id="endpoint-1",
            hostname=hostname.lower(),
            operating_system=operating_system,
            agent_version=agent_version,
            last_seen_at=last_seen_at,
            created_at=datetime.now(timezone.utc),
        )
        self._endpoints[endpoint.hostname] = endpoint
        return endpoint

    def update_last_seen(self, endpoint: FakeEndpoint, *, operating_system: str, agent_version: str, last_seen_at: datetime) -> FakeEndpoint:
        endpoint.operating_system = operating_system
        endpoint.agent_version = agent_version
        endpoint.last_seen_at = last_seen_at
        return endpoint


class FakeRawEventRepository:
    """In-memory raw event repository used for service testing."""

    def create(self, **_: object) -> FakeRawEvent:
        return FakeRawEvent(id="event-1")


def test_ingest_event_normalizes_and_persists() -> None:
    service = IngestionService(FakeEndpointRepository(), FakeRawEventRepository())  # type: ignore[arg-type]

    response = service.ingest_event(
        EventIngestionRequest(
            endpoint=EndpointRegistration(
                hostname="WS-001",
                operating_system="Windows 11",
                agent_version="1.0.0",
            ),
            source="PowerShell",
            event_type="process_creation",
            event_name="Suspicious Script Execution",
            severity="warning",
            occurred_at=datetime(2026, 7, 30, 12, 0, tzinfo=timezone.utc),
            payload={"command_line": "powershell.exe -enc abc"},
        )
    )

    assert response.endpoint_id == "endpoint-1"
    assert response.event_id == "event-1"
    assert response.event_category == "process_activity"
    assert response.severity == "medium"
    assert "Suspicious Script Execution" in response.normalized_summary


def test_categorize_event_uses_source_fallback() -> None:
    category = IngestionService.categorize_event("unknown_type", "dns")

    assert category == "network_activity"
