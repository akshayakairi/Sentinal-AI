"""Audit log schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AuditLogCreate(BaseModel):
    """Internal payload for recording security-relevant activity."""

    actor_user_id: str | None = None
    action: str = Field(min_length=2, max_length=100)
    resource_type: str = Field(min_length=2, max_length=80)
    resource_id: str | None = Field(default=None, max_length=120)
    details: dict[str, Any] = Field(default_factory=dict)


class AuditLogResponse(BaseModel):
    """API representation of an audit event."""

    id: str
    actor_user_id: str | None
    action: str
    resource_type: str
    resource_id: str | None
    details: dict[str, Any]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
