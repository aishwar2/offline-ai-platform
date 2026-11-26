"""Pydantic schemas for authentication and user registration."""

from pydantic import BaseModel, EmailStr, Field


class UserRegister(BaseModel):
    """Payload to register a new user account."""

    email: EmailStr
    username: str = Field(min_length=3, max_length=64, pattern=r"^[a-zA-Z0-9_.-]+$")
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=120)


class UserLogin(BaseModel):
    """Payload to authenticate with username/email and password."""

    username_or_email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    """JWT access token response returned on successful login."""

    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int
