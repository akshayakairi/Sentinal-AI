"""Detection schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AlertResponse(BaseModel):
    """Public representation of a security alert."""

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

    model_config = ConfigDict(from_attributes=True)


class IncidentResponse(BaseModel):
    """Public representation of a security incident."""

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

    model_config = ConfigDict(from_attributes=True)


class DetectionResult(BaseModel):
    """Detection and correlation outcome for an ingested event."""

    alert: AlertResponse | None
    incident: IncidentResponse | None
    matched_rule: str | None
    correlation_key: str | None
