"""
FastAPI dependencies — shared across routers.

The key dependency is get_current_user, which extracts and validates
the JWT from the Authorization header. Routes that require auth
use Depends(get_current_user). Routes that optionally support auth
use Depends(get_optional_user).
"""

from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User
from app.services.auth import decode_token

# HTTPBearer extracts the token from "Authorization: Bearer <token>"
security = HTTPBearer()
optional_security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Extract and validate the current user from the JWT.

    Raises 401 if token is missing, invalid, or user not found.
    Used by routes that require authentication.
    """
    payload = decode_token(credentials.credentials)

    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    result = await db.execute(
        select(User).where(User.id == UUID(user_id), User.is_active == True)  # noqa: E712
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    return user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_security),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """Optionally extract the current user from the JWT.

    Returns None if no token is provided (anonymous access).
    Returns the user if a valid token is present.
    Raises 401 only if a token IS provided but is invalid.

    Used by routes that work both with and without auth
    (e.g., creating answers pre-auth and post-auth).
    """
    if not credentials:
        return None

    payload = decode_token(credentials.credentials)
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    user_id = payload.get("sub")
    if not user_id:
        return None

    result = await db.execute(
        select(User).where(User.id == UUID(user_id), User.is_active == True)  # noqa: E712
    )
    return result.scalar_one_or_none()


async def get_moderator(
    user: User = Depends(get_current_user),
) -> User:
    """Require the current user to be a moderator.

    Raises 403 if the user exists but isn't a moderator.
    Used by moderation queue endpoints.
    """
    if not user.is_moderator:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Moderator access required",
        )
    return user
