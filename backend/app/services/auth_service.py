"""Authentication service for user registration and login."""

from datetime import datetime, timedelta, timezone

import jwt
from fastapi import HTTPException, status
from passlib.context import CryptContext

from app.core.config import get_settings
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import TokenResponse, UserLoginRequest, UserRegisterRequest
from app.schemas.user import UserResponse

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Service encapsulating authentication business logic."""

    def __init__(self, user_repository: UserRepository) -> None:
        self._user_repository = user_repository

    def register_user(self, payload: UserRegisterRequest) -> UserResponse:
        """Register a new analyst if the email is not already taken."""
        existing_user = self._user_repository.get_by_email(payload.email)
        if existing_user is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this email already exists.",
            )

        hashed_password = self.hash_password(payload.password)
        user = self._user_repository.create(
            email=payload.email,
            full_name=payload.full_name,
            hashed_password=hashed_password,
            role="analyst",
        )
        return UserResponse.model_validate(user)

    def login_user(self, payload: UserLoginRequest) -> TokenResponse:
        """Validate credentials and issue a JWT access token."""
        user = self._user_repository.get_by_email(payload.email)
        if user is None or not self.verify_password(payload.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive.",
            )

        token = self.create_access_token(subject=user.id, role=user.role)
        return TokenResponse(access_token=token, user=UserResponse.model_validate(user))

    def get_current_user(self, token: str) -> User:
        """Resolve the current authenticated user from a JWT token."""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials.",
        )

        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret_key,
                algorithms=[settings.jwt_algorithm],
            )
        except jwt.InvalidTokenError as exc:
            raise credentials_exception from exc

        subject = payload.get("sub")
        if not isinstance(subject, str):
            raise credentials_exception

        user = self._user_repository.get_by_id(subject)
        if user is None or not user.is_active:
            raise credentials_exception

        return user

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a raw password using the configured password hasher."""
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """Verify a raw password against its stored hash."""
        return pwd_context.verify(password, hashed_password)

    @staticmethod
    def create_access_token(subject: str, role: str | None = None) -> str:
        """Create a signed JWT access token for a user."""
        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=settings.access_token_expire_minutes
        )
        payload = {"sub": subject, "exp": expires_at}
        if role is not None:
            payload["role"] = role
        return jwt.encode(
            payload,
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )
