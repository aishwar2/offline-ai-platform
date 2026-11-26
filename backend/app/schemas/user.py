"""Pydantic schemas for user profile and admin management."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRead(BaseModel):
    """Public representation of a user account."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    email: EmailStr
    username: str
    full_name: str | None
    role: Literal["user", "admin"]
    is_active: bool
    preferred_model: str
    created_at: datetime


class UserUpdateMe(BaseModel):
    """Editable fields for the authenticated user's own profile."""

    full_name: str | None = Field(default=None, max_length=120)
    preferred_model: str | None = Field(default=None, min_length=1, max_length=64)
    password: str | None = Field(default=None, min_length=8, max_length=128)


class UserAdminUpdate(BaseModel):
    """Administrative updates to a user's role or active status."""

    role: Literal["user", "admin"] | None = None
    is_active: bool | None = None
    preferred_model: str | None = Field(default=None, min_length=1, max_length=64)
