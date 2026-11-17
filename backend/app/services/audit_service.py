"""Audit logging service."""

from app.repositories.audit_log_repository import AuditLogRepository
from app.schemas.audit import AuditLogCreate, AuditLogResponse


class AuditService:
    """Record and retrieve security-relevant platform activity."""

    def __init__(self, audit_log_repository: AuditLogRepository) -> None:
        self._audit_log_repository = audit_log_repository

    def record(self, payload: AuditLogCreate) -> AuditLogResponse:
        """Append a single audit event."""
        audit_log = self._audit_log_repository.create(
            actor_user_id=payload.actor_user_id,
            action=payload.action,
            resource_type=payload.resource_type,
            resource_id=payload.resource_id,
            details=payload.details,
        )
        return AuditLogResponse.model_validate(audit_log)

    def list_recent(self, *, limit: int = 100) -> list[AuditLogResponse]:
        """Return recent audit events for administrator review."""
        audit_logs = self._audit_log_repository.list_recent(limit=limit)
        return [AuditLogResponse.model_validate(audit_log) for audit_log in audit_logs]
