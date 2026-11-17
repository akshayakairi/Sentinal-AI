"""User repository for persistence access."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    """Repository for user persistence operations."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_email(self, email: str) -> User | None:
        """Return a user by email address if present."""
        statement = select(User).where(User.email == email.lower())
        return self._db.execute(statement).scalar_one_or_none()

    def get_by_id(self, user_id: str) -> User | None:
        """Return a user by primary key if present."""
        statement = select(User).where(User.id == user_id)
        return self._db.execute(statement).scalar_one_or_none()

    def create(
        self,
        *,
        email: str,
        full_name: str,
        hashed_password: str,
        role: str = "analyst",
    ) -> User:
        """Create and persist a new user."""
        user = User(
            email=email.lower(),
            full_name=full_name,
            hashed_password=hashed_password,
            role=role,
        )
        self._db.add(user)
        self._db.commit()
        self._db.refresh(user)
        return user
