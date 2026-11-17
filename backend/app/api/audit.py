"""Audit log API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import require_admin
from app.db.session import get_db
from app.models.user import User
from app.repositories.audit_log_repository import AuditLogRepository
from app.schemas.audit import AuditLogResponse
from app.services.audit_service import AuditService

router = APIRouter(prefix="/audit-logs", tags=["audit"])


def get_audit_service(db: Annotated[Session, Depends(get_db)]) -> AuditService:
    """Build an audit service for the current request."""
    return AuditService(AuditLogRepository(db))


@router.get("", response_model=list[AuditLogResponse])
async def list_audit_logs(
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
    _: Annotated[User, Depends(require_admin)],
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[AuditLogResponse]:
    """List recent audit events for administrators."""
    return audit_service.list_recent(limit=limit)
