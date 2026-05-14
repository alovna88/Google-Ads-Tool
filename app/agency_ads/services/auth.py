"""Staff Google OAuth + session cookies.

Flow:
1. GET /auth/login: generate a short-lived state token in a signed cookie,
   redirect the browser to Google's authorize endpoint.
2. Google redirects back to /auth/callback with code + state.
3. We validate state, exchange code for tokens, fetch userinfo, check the
   email allowlist, upsert the User, then set a signed session cookie
   and redirect to the web app.

Sessions are stateless: a signed cookie carries the user_id. On every
authenticated request we decode the cookie and load the User. For an
internal tool at agency scale that's plenty; we add Redis cache later if
needed.
"""

import logging
from typing import Any
from urllib.parse import urlencode

import httpx
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agency_ads.config import settings
from agency_ads.models import User

logger = logging.getLogger(__name__)

GOOGLE_AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

OAUTH_SCOPES = ["openid", "email", "profile"]

STATE_COOKIE = "oauth_state"
STATE_MAX_AGE_SECONDS = 10 * 60  # 10 minutes — covers slow logins

SESSION_COOKIE = "session"
# Source of truth for max age = settings.auth_session_max_age_hours.

STATE_SERIALIZER_SALT = "oauth-state-v1"
SESSION_SERIALIZER_SALT = "session-v1"


def _state_serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(settings.session_secret, salt=STATE_SERIALIZER_SALT)


def _session_serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(settings.session_secret, salt=SESSION_SERIALIZER_SALT)


# ---------------------------------------------------------------------------
# State (CSRF protection on the OAuth round-trip)
# ---------------------------------------------------------------------------


def encode_state(next_url: str | None = None) -> str:
    """Encode the OAuth `state` parameter. Carries an optional `next` URL
    we'll redirect to after successful login.
    """
    payload: dict[str, Any] = {}
    if next_url:
        payload["next"] = next_url
    return _state_serializer().dumps(payload)


def decode_state(token: str) -> dict[str, Any]:
    """Decode + validate state. Raises if tampered or expired."""
    return _state_serializer().loads(token, max_age=STATE_MAX_AGE_SECONDS)


# ---------------------------------------------------------------------------
# Session cookies
# ---------------------------------------------------------------------------


def encode_session(user_id: str, email: str) -> str:
    return _session_serializer().dumps({"uid": user_id, "email": email})


def decode_session(token: str) -> dict[str, Any] | None:
    """Decode the session cookie. Returns None when the cookie is invalid,
    expired, or tampered — callers should treat that as logged-out.
    """
    max_age = settings.auth_session_max_age_hours * 3600
    try:
        return _session_serializer().loads(token, max_age=max_age)
    except SignatureExpired:
        logger.info("session cookie expired")
        return None
    except BadSignature:
        logger.warning("session cookie failed signature check")
        return None


# ---------------------------------------------------------------------------
# OAuth URL builders + token exchange
# ---------------------------------------------------------------------------


def authorize_url(state: str) -> str:
    """Build the Google authorize URL the user is redirected to."""
    params = {
        "client_id": settings.google_oauth_client_id,
        "redirect_uri": _redirect_uri(),
        "response_type": "code",
        "scope": " ".join(OAUTH_SCOPES),
        "state": state,
        "access_type": "online",
        "prompt": "select_account",
    }
    return f"{GOOGLE_AUTHORIZE_URL}?{urlencode(params)}"


def _redirect_uri() -> str:
    """The redirect_uri given to Google. Must match the value registered in
    Google Cloud Console. Browser hits this on the web origin; Next.js
    rewrites it through to the API.
    """
    return f"{settings.web_base_url}/api/auth/callback"


async def exchange_code(code: str) -> dict[str, Any]:
    """Exchange an authorization code for tokens. Returns Google's full
    token response.
    """
    data = {
        "code": code,
        "client_id": settings.google_oauth_client_id,
        "client_secret": settings.google_oauth_client_secret,
        "redirect_uri": _redirect_uri(),
        "grant_type": "authorization_code",
    }
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(GOOGLE_TOKEN_URL, data=data)
        response.raise_for_status()
        return response.json()


async def fetch_userinfo(access_token: str) -> dict[str, Any]:
    """Fetch the OIDC userinfo for the access token."""
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        response.raise_for_status()
        return response.json()


# ---------------------------------------------------------------------------
# User upsert
# ---------------------------------------------------------------------------


async def upsert_user(session: AsyncSession, *, email: str, name: str) -> User:
    """Get-or-create the User row by email. Updates `name` if changed."""
    email = email.strip().lower()
    result = await session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(email=email, name=name or email)
        session.add(user)
        await session.flush()
        logger.info("created user %s", email)
    elif name and user.name != name:
        user.name = name
        await session.flush()
    return user
