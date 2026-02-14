"""
OAuth authentication endpoints — Google and GitHub.

Flow (Authorization Code Grant):
1. Frontend opens /auth/oauth/{provider} → backend redirects to provider
2. User authenticates at provider → provider redirects to /auth/oauth/{provider}/callback
3. Backend exchanges code for tokens, fetches user profile
4. Backend finds or creates a User, issues JWT tokens
5. Backend redirects to frontend with tokens as URL fragment (not query params)

Security notes:
- Tokens are passed as URL fragments (#access_token=...) so they're not
  sent to the server in subsequent requests or logged in server access logs
- state parameter prevents CSRF
- If a user with the same email exists (from password signup), the accounts
  are linked automatically
"""

import secrets
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models import User
from app.services.auth import create_access_token, create_refresh_token

router = APIRouter(prefix="/auth/oauth", tags=["oauth"])

# In-memory state store for CSRF protection (use Redis in production)
_oauth_states: dict[str, str] = {}


# ---------------------------------------------------------------------------
# Google OAuth
# ---------------------------------------------------------------------------

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"


@router.get("/google")
async def google_login():
    """Redirect user to Google's OAuth consent screen."""
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=501, detail="Google OAuth not configured")

    state = secrets.token_urlsafe(32)
    _oauth_states[state] = "google"

    redirect_uri = f"{settings.OAUTH_REDIRECT_BASE}/auth/oauth/google/callback"
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "offline",
        "prompt": "select_account",
    }
    url = f"{GOOGLE_AUTH_URL}?{'&'.join(f'{k}={v}' for k, v in params.items())}"
    return RedirectResponse(url=url)


@router.get("/google/callback")
async def google_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Handle Google's OAuth callback — exchange code for user profile."""
    # Verify CSRF state
    if state not in _oauth_states or _oauth_states.pop(state) != "google":
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    redirect_uri = f"{settings.OAUTH_REDIRECT_BASE}/auth/oauth/google/callback"

    # Exchange authorization code for tokens
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri,
            },
        )
        if token_resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to exchange code")
        token_data = token_resp.json()

        # Fetch user profile
        userinfo_resp = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {token_data['access_token']}"},
        )
        if userinfo_resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to fetch user info")
        profile = userinfo_resp.json()

    email = profile.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email not provided by Google")

    user = await _find_or_create_oauth_user(
        db=db,
        email=email,
        display_name=profile.get("name"),
        avatar_url=profile.get("picture"),
        provider="google",
        provider_id=str(profile.get("id")),
    )

    return _build_frontend_redirect(user)


# ---------------------------------------------------------------------------
# GitHub OAuth
# ---------------------------------------------------------------------------

GITHUB_AUTH_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_URL = "https://api.github.com/user"
GITHUB_EMAILS_URL = "https://api.github.com/user/emails"


@router.get("/github")
async def github_login():
    """Redirect user to GitHub's OAuth consent screen."""
    if not settings.GITHUB_CLIENT_ID:
        raise HTTPException(status_code=501, detail="GitHub OAuth not configured")

    state = secrets.token_urlsafe(32)
    _oauth_states[state] = "github"

    redirect_uri = f"{settings.OAUTH_REDIRECT_BASE}/auth/oauth/github/callback"
    params = {
        "client_id": settings.GITHUB_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "scope": "user:email",
        "state": state,
    }
    url = f"{GITHUB_AUTH_URL}?{'&'.join(f'{k}={v}' for k, v in params.items())}"
    return RedirectResponse(url=url)


@router.get("/github/callback")
async def github_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Handle GitHub's OAuth callback — exchange code for user profile."""
    if state not in _oauth_states or _oauth_states.pop(state) != "github":
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    redirect_uri = f"{settings.OAUTH_REDIRECT_BASE}/auth/oauth/github/callback"

    async with httpx.AsyncClient() as client:
        # Exchange code for access token
        token_resp = await client.post(
            GITHUB_TOKEN_URL,
            data={
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": redirect_uri,
            },
            headers={"Accept": "application/json"},
        )
        if token_resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to exchange code")
        token_data = token_resp.json()

        access_token = token_data.get("access_token")
        if not access_token:
            raise HTTPException(status_code=400, detail="No access token in response")

        auth_headers = {"Authorization": f"Bearer {access_token}"}

        # Fetch user profile
        user_resp = await client.get(GITHUB_USER_URL, headers=auth_headers)
        if user_resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to fetch user info")
        profile = user_resp.json()

        # GitHub may not include email in profile — fetch from emails endpoint
        email = profile.get("email")
        if not email:
            emails_resp = await client.get(GITHUB_EMAILS_URL, headers=auth_headers)
            if emails_resp.status_code == 200:
                emails = emails_resp.json()
                primary = next(
                    (e for e in emails if e.get("primary") and e.get("verified")),
                    None,
                )
                if primary:
                    email = primary["email"]

    if not email:
        raise HTTPException(
            status_code=400,
            detail="Could not retrieve email from GitHub. Ensure email is public or grant user:email scope.",
        )

    user = await _find_or_create_oauth_user(
        db=db,
        email=email,
        display_name=profile.get("name") or profile.get("login"),
        avatar_url=profile.get("avatar_url"),
        provider="github",
        provider_id=str(profile.get("id")),
    )

    return _build_frontend_redirect(user)


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

async def _find_or_create_oauth_user(
    db: AsyncSession,
    email: str,
    display_name: str | None,
    avatar_url: str | None,
    provider: str,
    provider_id: str,
) -> User:
    """Find existing user by email or create a new OAuth user.

    If a user with the same email already exists (from password signup),
    link the OAuth identity to that account. This prevents duplicate
    accounts and lets users sign in with either method.
    """
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user:
        # Link OAuth to existing account if not already linked
        if not user.oauth_provider:
            user.oauth_provider = provider
            user.oauth_provider_id = provider_id
        if not user.avatar_url and avatar_url:
            user.avatar_url = avatar_url
        if not user.display_name and display_name:
            user.display_name = display_name
        user.last_login = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(user)
    else:
        # Create new user — no password needed for OAuth
        user = User(
            email=email,
            display_name=display_name,
            avatar_url=avatar_url,
            oauth_provider=provider,
            oauth_provider_id=provider_id,
            last_login=datetime.now(timezone.utc),
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    return user


def _build_frontend_redirect(user: User) -> RedirectResponse:
    """Build redirect to frontend with JWT tokens in URL fragment.

    URL fragment (#) is used instead of query params (?) because:
    - Fragments are NOT sent to the server in HTTP requests
    - Fragments are NOT logged in server access logs
    - Only JavaScript on the client can read them
    """
    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))

    redirect_url = (
        f"{settings.FRONTEND_URL}/login"
        f"#access_token={access_token}"
        f"&refresh_token={refresh_token}"
    )
    return RedirectResponse(url=redirect_url)
