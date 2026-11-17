"""Authentication request and response schemas."""

from pydantic import BaseModel, EmailStr, Field

from app.schemas.user import UserResponse


class UserRegisterRequest(BaseModel):
    """Payload for creating a new user account."""

    email: EmailStr
    full_name: str = Field(min_length=2, max_length=255)
    password: str = Field(min_length=8, max_length=128)


class UserLoginRequest(BaseModel):
    """Payload for exchanging credentials for an access token."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class TokenResponse(BaseModel):
    """JWT token response."""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse
