"""LinkedIn Ads OAuth 2.0 — authorize URL, code exchange, refresh.

LinkedIn's flow is standard authorization-code OAuth with one quirk:
refresh tokens are gated by the "Marketing Developer Platform" tier.
When the app is on the basic tier the token response omits
`refresh_token` and the access token simply expires after ~60 days, at
which point the user must re-auth. We persist whatever LinkedIn returns
and let the refresh job decide what's possible.

State is a signed itsdangerous token that round-trips the agency
client_id we're connecting for, so the callback knows which row to
upsert.
"""

import logging
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import urlencode

import httpx
from itsdangerous import URLSafeTimedSerializer

from agency_ads.config import settings

logger = logging.getLogger(__name__)

LINKEDIN_AUTHORIZE_URL = "https://www.linkedin.com/oauth/v2/authorization"
LINKEDIN_TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
# OpenID Connect userinfo (works when "openid profile" or
# "r_basicprofile" / "r_liteprofile" is in scope). Used to identify the
# LinkedIn member who authorized the connection.
LINKEDIN_USERINFO_URL = "https://api.linkedin.com/v2/userinfo"

STATE_COOKIE = "linkedin_oauth_state"
STATE_MAX_AGE_SECONDS = 10 * 60

STATE_SERIALIZER_SALT = "linkedin-oauth-state-v1"


def _state_serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(settings.session_secret, salt=STATE_SERIALIZER_SALT)


def encode_state(*, client_id: str, next_url: str | None = None) -> str:
    payload: dict[str, Any] = {"cid": client_id}
    if next_url:
        payload["next"] = next_url
    return _state_serializer().dumps(payload)


def decode_state(token: str) -> dict[str, Any]:
    return _state_serializer().loads(token, max_age=STATE_MAX_AGE_SECONDS)


def redirect_uri() -> str:
    """Browser-visible callback. Must match the value registered in
    LinkedIn Developer Console exactly.
    """
    return f"{settings.web_base_url}/api/linkedin/callback"


def authorize_url(state: str) -> str:
    """Build the LinkedIn authorize URL the user is redirected to."""
    params = {
        "response_type": "code",
        "client_id": settings.linkedin_client_id,
        "redirect_uri": redirect_uri(),
        "scope": " ".join(settings.linkedin_scopes),
        "state": state,
    }
    return f"{LINKEDIN_AUTHORIZE_URL}?{urlencode(params)}"


async def exchange_code(code: str) -> dict[str, Any]:
    """Exchange the auth code for an access (+ optional refresh) token."""
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": settings.linkedin_client_id,
        "client_secret": settings.linkedin_client_secret,
        "redirect_uri": redirect_uri(),
    }
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(
            LINKEDIN_TOKEN_URL,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response.raise_for_status()
        return response.json()


async def refresh_access_token(refresh_token: str) -> dict[str, Any]:
    """Trade a refresh token for a new access token. LinkedIn returns
    the same shape as the auth-code exchange. May rotate the refresh
    token; callers must persist whatever comes back.
    """
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": settings.linkedin_client_id,
        "client_secret": settings.linkedin_client_secret,
    }
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(
            LINKEDIN_TOKEN_URL,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response.raise_for_status()
        return response.json()


async def fetch_member_profile(access_token: str) -> dict[str, Any]:
    """Get the member URN + name for the user who just authorized."""
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(
            LINKEDIN_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        response.raise_for_status()
        return response.json()


def expires_at_from_response(payload: dict[str, Any]) -> datetime:
    """Compute an absolute expiry from the `expires_in` (seconds) field
    LinkedIn returns. Skew by 60s to avoid edge-case 401s the moment a
    token would otherwise be considered fresh.
    """
    expires_in = int(payload.get("expires_in") or 0)
    return datetime.now(UTC) + timedelta(seconds=max(expires_in - 60, 0))


def refresh_expires_at_from_response(payload: dict[str, Any]) -> datetime | None:
    """LinkedIn returns `refresh_token_expires_in` only for apps on the
    Marketing Developer Platform. Returns None otherwise.
    """
    expires_in = payload.get("refresh_token_expires_in")
    if not expires_in:
        return None
    return datetime.now(UTC) + timedelta(seconds=int(expires_in))
