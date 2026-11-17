"""Audit logging service tests."""

from dataclasses import dataclass
from datetime import datetime, timezone

from app.schemas.audit import AuditLogCreate
from app.services.audit_service import AuditService


@dataclass
class FakeAuditLog:
    id: str
    actor_user_id: str | None
    action: str
    resource_type: str
    resource_id: str | None
    details: dict
    created_at: datetime


class FakeAuditLogRepository:
    def __init__(self) -> None:
        self.audit_logs: list[FakeAuditLog] = []

    def create(
        self,
        *,
        actor_user_id: str | None,
        action: str,
        resource_type: str,
        resource_id: str | None,
        details: dict,
    ) -> FakeAuditLog:
        audit_log = FakeAuditLog(
            id=f"audit-{len(self.audit_logs) + 1}",
            actor_user_id=actor_user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            created_at=datetime.now(timezone.utc),
        )
        self.audit_logs.append(audit_log)
        return audit_log

    def list_recent(self, *, limit: int = 100) -> list[FakeAuditLog]:
        return list(reversed(self.audit_logs))[:limit]


def test_record_creates_audit_event() -> None:
    repository = FakeAuditLogRepository()
    service = AuditService(repository)  # type: ignore[arg-type]

    audit_log = service.record(
        AuditLogCreate(
            actor_user_id="user-1",
            action="incident.updated",
            resource_type="incident",
            resource_id="incident-1",
            details={"status": "in_progress"},
        )
    )

    assert audit_log.action == "incident.updated"
    assert audit_log.actor_user_id == "user-1"
    assert audit_log.details["status"] == "in_progress"


def test_list_recent_limits_results() -> None:
    repository = FakeAuditLogRepository()
    service = AuditService(repository)  # type: ignore[arg-type]
    service.record(AuditLogCreate(action="action.a", resource_type="incident"))
    service.record(AuditLogCreate(action="action.b", resource_type="incident"))

    audit_logs = service.list_recent(limit=1)

    assert len(audit_logs) == 1
    assert audit_logs[0].action == "action.b"

