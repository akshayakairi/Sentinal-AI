"""Event ingestion schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.detection import DetectionResult


class EndpointRegistration(BaseModel):
    """Endpoint metadata sent with every ingestion request."""

    hostname: str = Field(min_length=2, max_length=255)
    operating_system: str = Field(min_length=2, max_length=100)
    agent_version: str = Field(min_length=1, max_length=50)


class EventIngestionRequest(BaseModel):
    """Payload for ingesting a single endpoint event."""

    endpoint: EndpointRegistration
    source: str = Field(min_length=2, max_length=100)
    event_type: str = Field(min_length=2, max_length=100)
    event_name: str = Field(min_length=2, max_length=255)
    severity: str = Field(min_length=2, max_length=20)
    occurred_at: datetime
    payload: dict = Field(default_factory=dict)


class EndpointResponse(BaseModel):
    """Public representation of a monitored endpoint."""

    id: str
    hostname: str
    operating_system: str
    agent_version: str
    last_seen_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EventIngestionResponse(BaseModel):
    """Response returned after an event has been stored."""

    event_id: str
    endpoint_id: str
    event_category: str
    severity: str
    normalized_summary: str
    detection: DetectionResult | None = None
