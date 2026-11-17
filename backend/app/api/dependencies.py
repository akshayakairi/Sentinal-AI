"""Shared API authentication and authorization dependencies."""

from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """Resolve the active JWT identity for protected API operations."""
    return AuthService(UserRepository(db)).get_current_user(token)


def require_roles(*allowed_roles: str) -> Callable[[User], User]:
    """Create a dependency that allows only selected user roles."""

    def dependency(current_user: Annotated[User, Depends(get_current_user)]) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="The current user does not have permission to perform this action.",
            )
        return current_user

    return dependency


require_admin = require_roles("admin")
require_analyst = require_roles("admin", "analyst")
require_authenticated = require_roles("admin", "analyst", "viewer")
