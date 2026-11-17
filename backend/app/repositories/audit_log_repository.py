"""Audit log persistence repository."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


class AuditLogRepository:
    """Repository for append-only audit records."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def create(
        self,
        *,
        actor_user_id: str | None,
        action: str,
        resource_type: str,
        resource_id: str | None,
        details: dict,
    ) -> AuditLog:
        """Persist a new audit event."""
        audit_log = AuditLog(
            actor_user_id=actor_user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
        )
        self._db.add(audit_log)
        self._db.commit()
        self._db.refresh(audit_log)
        return audit_log

    def list_recent(self, *, limit: int = 100) -> list[AuditLog]:
        """Return recent audit events newest first."""
        statement = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
        return list(self._db.execute(statement).scalars().all())
