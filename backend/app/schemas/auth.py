"""
Pydantic schemas for authentication endpoints.
"""

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterRequest(BaseModel):
    """Request to create a new account."""

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    display_name: Optional[str] = None


class LoginRequest(BaseModel):
    """Request to log in with email/password."""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """JWT token pair returned on login/register/refresh."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    """Request to refresh an access token."""

    refresh_token: str


class UserResponse(BaseModel):
    """Public user profile."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    oauth_provider: Optional[str] = None
    default_role: Optional[str] = None
    default_experience_level: Optional[str] = None
    plan_tier: str
    evaluations_this_month: int
