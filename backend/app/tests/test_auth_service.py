"""Authentication service tests."""

from dataclasses import dataclass
from datetime import datetime, timezone

import pytest
from fastapi import HTTPException

from app.schemas.auth import UserLoginRequest, UserRegisterRequest
from app.services.auth_service import AuthService


@dataclass
class FakeUser:
    """Lightweight test double matching the service's user contract."""

    id: str
    email: str
    full_name: str
    hashed_password: str
    role: str
    is_active: bool
    created_at: datetime


class FakeUserRepository:
    """In-memory repository used for service-level tests."""

    def __init__(self) -> None:
        self._users: dict[str, FakeUser] = {}

    def get_by_email(self, email: str) -> FakeUser | None:
        return self._users.get(email.lower())

    def get_by_id(self, user_id: str) -> FakeUser | None:
        for user in self._users.values():
            if user.id == user_id:
                return user
        return None

    def create(
        self,
        *,
        email: str,
        full_name: str,
        hashed_password: str,
        role: str = "analyst",
    ) -> FakeUser:
        user = FakeUser(
            id="user-1",
            email=email.lower(),
            full_name=full_name,
            hashed_password=hashed_password,
            role=role,
            is_active=True,
            created_at=datetime.now(timezone.utc),
        )
        self._users[user.email] = user
        return user


def test_register_user_creates_analyst_account() -> None:
    repository = FakeUserRepository()
    service = AuthService(repository)  # type: ignore[arg-type]

    user = service.register_user(
        UserRegisterRequest(
            email="analyst@sentinelai.com",
            full_name="SOC Analyst",
            password="StrongPass123",
        )
    )

    assert user.email == "analyst@sentinelai.com"
    assert user.full_name == "SOC Analyst"
    assert user.role == "analyst"


def test_login_user_returns_access_token() -> None:
    repository = FakeUserRepository()
    service = AuthService(repository)  # type: ignore[arg-type]
    service.register_user(
        UserRegisterRequest(
            email="analyst@sentinelai.com",
            full_name="SOC Analyst",
            password="StrongPass123",
        )
    )

    token_response = service.login_user(
        UserLoginRequest(
            email="analyst@sentinelai.com",
            password="StrongPass123",
        )
    )

    assert token_response.access_token
    assert token_response.user.email == "analyst@sentinelai.com"
    assert token_response.user.role == "analyst"


def test_login_user_rejects_invalid_password() -> None:
    repository = FakeUserRepository()
    service = AuthService(repository)  # type: ignore[arg-type]
    service.register_user(
        UserRegisterRequest(
            email="analyst@sentinelai.com",
            full_name="SOC Analyst",
            password="StrongPass123",
        )
    )

    with pytest.raises(HTTPException) as exc_info:
        service.login_user(
            UserLoginRequest(
                email="analyst@sentinelai.com",
                password="WrongPassword123",
            )
        )

    assert exc_info.value.status_code == 401
