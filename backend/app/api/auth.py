"""Authentication API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import TokenResponse, UserLoginRequest, UserRegisterRequest
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


def get_auth_service(db: Annotated[Session, Depends(get_db)]) -> AuthService:
    """Build an auth service for the current request."""
    return AuthService(UserRepository(db))


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(payload: UserRegisterRequest, auth_service: Annotated[AuthService, Depends(get_auth_service)]) -> UserResponse:
    """Register a new platform user."""
    return auth_service.register_user(payload)


@router.post("/login", response_model=TokenResponse)
async def login(payload: UserLoginRequest, auth_service: Annotated[AuthService, Depends(get_auth_service)]) -> TokenResponse:
    """Authenticate a user and issue a JWT access token."""
    return auth_service.login_user(payload)


@router.get("/me", response_model=UserResponse)
async def read_current_user(current_user: Annotated[User, Depends(get_current_user)]) -> UserResponse:
    """Return the currently authenticated user."""
    return UserResponse.model_validate(current_user)
