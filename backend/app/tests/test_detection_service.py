"""Detection service tests."""

from dataclasses import dataclass
from datetime import datetime, timezone

from app.schemas.detection import DetectionResult
from app.services.detection_service import DetectionService


@dataclass
class FakeEndpoint:
    id: str
    hostname: str


@dataclass
class FakeRawEvent:
    id: str
    endpoint_id: str
    source: str
    event_type: str
    event_category: str
    severity: str
    event_name: str
    occurred_at: datetime
    raw_payload: dict


@dataclass
class FakeAlert:
    id: str
    raw_event_id: str
    endpoint_id: str
    incident_id: str | None
    title: str
    description: str
    severity: str
    status: str
    rule_name: str
    correlation_key: str
    mitre_technique: str | None
    created_at: datetime


@dataclass
class FakeIncident:
    id: str
    endpoint_id: str
    title: str
    summary: str
    severity: str
    status: str
    correlation_key: str
    first_event_at: datetime
    last_event_at: datetime
    created_by_alert_id: str
    created_at: datetime
    updated_at: datetime


class FakeAlertRepository:
    def __init__(self) -> None:
        self.alerts: list[FakeAlert] = []

    def list_all(self) -> list[FakeAlert]:
        return list(self.alerts)

    def create(self, **kwargs: object) -> FakeAlert:
        alert = FakeAlert(
            id=f"alert-{len(self.alerts) + 1}",
            incident_id=None,
            status="open",
            created_at=datetime.now(timezone.utc),
            **kwargs,
        )
        self.alerts.append(alert)
        return alert

    def assign_to_incident(self, alert: FakeAlert, incident_id: str) -> FakeAlert:
        alert.incident_id = incident_id
        return alert


class FakeIncidentRepository:
    def __init__(self) -> None:
        self.incidents: list[FakeIncident] = []

    def list_all(self) -> list[FakeIncident]:
        return list(self.incidents)

    def find_open_by_correlation(self, **kwargs: object) -> FakeIncident | None:
        endpoint_id = kwargs["endpoint_id"]
        correlation_key = kwargs["correlation_key"]
        for incident in self.incidents:
            if incident.endpoint_id == endpoint_id and incident.correlation_key == correlation_key and incident.status == "open":
                return incident
        return None

    def create(self, **kwargs: object) -> FakeIncident:
        incident = FakeIncident(
            id=f"incident-{len(self.incidents) + 1}",
            status="open",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            last_event_at=kwargs["first_event_at"],
            **kwargs,
        )
        self.incidents.append(incident)
        return incident

    def update_correlation(self, incident: FakeIncident, *, severity: str, summary: str, last_event_at: datetime) -> FakeIncident:
        incident.severity = severity if severity == "critical" else incident.severity
        incident.summary = summary
        incident.last_event_at = last_event_at
        incident.updated_at = datetime.now(timezone.utc)
        return incident


def test_process_event_creates_alert_and_incident() -> None:
    service = DetectionService(FakeAlertRepository(), FakeIncidentRepository())  # type: ignore[arg-type]

    result = service.process_event(
        endpoint=FakeEndpoint(id="endpoint-1", hostname="ws-001"),
        raw_event=FakeRawEvent(
            id="event-1",
            endpoint_id="endpoint-1",
            source="powershell",
            event_type="process_creation",
            event_category="script_execution",
            severity="medium",
            event_name="Encoded PowerShell",
            occurred_at=datetime(2026, 7, 30, 12, 0, tzinfo=timezone.utc),
            raw_payload={"command_line": "powershell.exe -enc abc"},
        ),
    )

    assert isinstance(result, DetectionResult)
    assert result.alert is not None
    assert result.incident is not None
    assert result.matched_rule == "suspicious_powershell_encoded_command"
    assert result.incident.correlation_key == "script_execution:powershell_encoded"


def test_process_event_reuses_open_incident() -> None:
    alert_repository = FakeAlertRepository()
    incident_repository = FakeIncidentRepository()
    service = DetectionService(alert_repository, incident_repository)  # type: ignore[arg-type]

    first = service.process_event(
        endpoint=FakeEndpoint(id="endpoint-1", hostname="ws-001"),
        raw_event=FakeRawEvent(
            id="event-1",
            endpoint_id="endpoint-1",
            source="powershell",
            event_type="process_creation",
            event_category="script_execution",
            severity="medium",
            event_name="Encoded PowerShell",
            occurred_at=datetime(2026, 7, 30, 12, 0, tzinfo=timezone.utc),
            raw_payload={"command_line": "powershell.exe -enc abc"},
        ),
    )
    second = service.process_event(
        endpoint=FakeEndpoint(id="endpoint-1", hostname="ws-001"),
        raw_event=FakeRawEvent(
            id="event-2",
            endpoint_id="endpoint-1",
            source="powershell",
            event_type="process_creation",
            event_category="script_execution",
            severity="medium",
            event_name="Encoded PowerShell Second",
            occurred_at=datetime(2026, 7, 30, 12, 5, tzinfo=timezone.utc),
            raw_payload={"command_line": "powershell.exe -enc def"},
        ),
    )

    assert first.incident is not None
    assert second.incident is not None
    assert first.incident.id == second.incident.id
    assert len(incident_repository.incidents) == 1


def test_process_event_returns_no_detection_for_benign_event() -> None:
    service = DetectionService(FakeAlertRepository(), FakeIncidentRepository())  # type: ignore[arg-type]

    result = service.process_event(
        endpoint=FakeEndpoint(id="endpoint-1", hostname="ws-001"),
        raw_event=FakeRawEvent(
            id="event-1",
            endpoint_id="endpoint-1",
            source="system",
            event_type="heartbeat",
            event_category="system_activity",
            severity="low",
            event_name="Agent Heartbeat",
            occurred_at=datetime(2026, 7, 30, 12, 0, tzinfo=timezone.utc),
            raw_payload={"status": "ok"},
        ),
    )

    assert result.alert is None
    assert result.incident is None
