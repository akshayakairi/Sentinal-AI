"""Incident service tests."""

from dataclasses import dataclass
from datetime import datetime, timezone

import pytest
from fastapi import HTTPException

from app.schemas.incident_management import IncidentNoteCreateRequest, IncidentUpdateRequest
from app.services.incident_service import IncidentService


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
    assigned_to_user_id: str | None
    resolution_summary: str | None
    created_at: datetime
    updated_at: datetime


@dataclass
class FakeNote:
    id: str
    incident_id: str
    author_user_id: str
    body: str
    created_at: datetime


@dataclass
class FakeAlert:
    id: str
    incident_id: str | None
    title: str
    description: str
    created_at: datetime


@dataclass
class FakeUser:
    id: str


class FakeIncidentRepository:
    def __init__(self) -> None:
        now = datetime(2026, 7, 30, 12, 0, tzinfo=timezone.utc)
        self.incident = FakeIncident(
            id="incident-1",
            endpoint_id="endpoint-1",
            title="Suspicious PowerShell Encoded Command",
            summary="Initial summary",
            severity="high",
            status="open",
            correlation_key="script_execution:powershell_encoded",
            first_event_at=now,
            last_event_at=now,
            created_by_alert_id="alert-1",
            assigned_to_user_id=None,
            resolution_summary=None,
            created_at=now,
            updated_at=now,
        )

    def list_all(self) -> list[FakeIncident]:
        return [self.incident]

    def get_by_id(self, incident_id: str) -> FakeIncident | None:
        return self.incident if incident_id == self.incident.id else None

    def update_management(
        self,
        incident: FakeIncident,
        *,
        status: str,
        assigned_to_user_id: str | None,
        resolution_summary: str | None,
    ) -> FakeIncident:
        incident.status = status
        incident.assigned_to_user_id = assigned_to_user_id
        incident.resolution_summary = resolution_summary
        incident.updated_at = datetime.now(timezone.utc)
        return incident


class FakeIncidentNoteRepository:
    def __init__(self) -> None:
        self.notes: list[FakeNote] = []

    def list_by_incident(self, incident_id: str) -> list[FakeNote]:
        return [note for note in self.notes if note.incident_id == incident_id]

    def create(self, *, incident_id: str, author_user_id: str, body: str) -> FakeNote:
        note = FakeNote(
            id=f"note-{len(self.notes) + 1}",
            incident_id=incident_id,
            author_user_id=author_user_id,
            body=body,
            created_at=datetime.now(timezone.utc),
        )
        self.notes.append(note)
        return note


class FakeAlertRepository:
    def list_by_incident(self, incident_id: str) -> list[FakeAlert]:
        return [
            FakeAlert(
                id="alert-1",
                incident_id=incident_id,
                title="Suspicious PowerShell Encoded Command",
                description="Encoded command execution detected.",
                created_at=datetime(2026, 7, 30, 12, 0, tzinfo=timezone.utc),
            )
        ]


class FakeUserRepository:
    def __init__(self) -> None:
        self.users = {"user-1": FakeUser(id="user-1")}

    def get_by_id(self, user_id: str) -> FakeUser | None:
        return self.users.get(user_id)


def build_service() -> IncidentService:
    return IncidentService(
        FakeIncidentRepository(),
        FakeIncidentNoteRepository(),
        FakeAlertRepository(),
        FakeUserRepository(),
    )  # type: ignore[arg-type]


def test_update_incident_assigns_and_progresses() -> None:
    service = build_service()

    updated = service.update_incident(
        "incident-1",
        IncidentUpdateRequest(status="in_progress", assigned_to_user_id="user-1"),
    )

    assert updated.status == "in_progress"
    assert updated.assigned_to_user_id == "user-1"


def test_update_incident_requires_resolution_summary() -> None:
    service = build_service()

    with pytest.raises(HTTPException) as exc_info:
        service.update_incident(
            "incident-1",
            IncidentUpdateRequest(status="resolved", assigned_to_user_id="user-1"),
        )

    assert exc_info.value.status_code == 400


def test_add_note_creates_analyst_note() -> None:
    service = build_service()

    note = service.add_note(
        "incident-1",
        IncidentNoteCreateRequest(author_user_id="user-1", body="Investigating PowerShell ancestry."),
    )

    assert note.author_user_id == "user-1"
    assert "PowerShell" in note.body


def test_timeline_merges_alerts_and_notes() -> None:
    service = build_service()
    service.add_note(
        "incident-1",
        IncidentNoteCreateRequest(author_user_id="user-1", body="Investigating PowerShell ancestry."),
    )

    timeline = service.get_timeline("incident-1")

    assert len(timeline) == 2
    assert timeline[0].entry_type == "alert"
    assert timeline[1].entry_type == "note"
