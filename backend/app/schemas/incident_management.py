"""Incident management schemas."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

StatusValue = Literal["open", "in_progress", "resolved", "closed"]
TimelineEntryType = Literal["alert", "note"]


class IncidentNoteResponse(BaseModel):
    """Public representation of an analyst note."""

    id: str
    incident_id: str
    author_user_id: str
    body: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class IncidentDetailResponse(BaseModel):
    """Analyst-facing detailed incident representation."""

    id: str
    endpoint_id: str
    title: str
    summary: str
    severity: str
    status: StatusValue
    correlation_key: str
    first_event_at: datetime
    last_event_at: datetime
    created_by_alert_id: str
    assigned_to_user_id: str | None
    resolution_summary: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class IncidentUpdateRequest(BaseModel):
    """Payload for updating workflow fields on an incident."""

    status: StatusValue
    assigned_to_user_id: str | None = None
    resolution_summary: str | None = Field(default=None, max_length=5000)


class IncidentNoteCreateRequest(BaseModel):
    """Payload for adding a note to an incident."""

    author_user_id: str
    body: str = Field(min_length=1, max_length=5000)


class TimelineEntry(BaseModel):
    """Single incident timeline entry."""

    entry_type: TimelineEntryType
    occurred_at: datetime
    title: str
    detail: str
    actor_user_id: str | None = None
    related_id: str
