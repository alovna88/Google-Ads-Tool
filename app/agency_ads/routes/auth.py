"""Auth endpoints.

GET  /auth/login    redirect to Google
GET  /auth/callback complete OAuth, set session cookie, redirect to /
POST /auth/logout   clear session cookie
GET  /auth/me       return the current user (or 401)
"""

import logging
from typing import Annotated
from urllib.parse import quote, urljoin

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from agency_ads.config import settings
from agency_ads.db import session_dependency
from agency_ads.dependencies import current_user
from agency_ads.models import User
from agency_ads.schemas.auth import UserMe
from agency_ads.services import auth as auth_service

logger = logging.getLogger(__name__)

router = APIRouter()


def _is_safe_next(url: str | None) -> bool:
    """Allow only relative redirects so an attacker can't bounce the user
    to an external site via `?next=`.
    """
    if not url:
        return False
    return url.startswith("/") and not url.startswith("//")


def _cookie_kwargs() -> dict:
    """Shared cookie attributes. Secure in production only — localhost
    can't set Secure cookies over plain HTTP.
    """
    return {
        "httponly": True,
        "samesite": "lax",
        "secure": settings.is_production,
        "path": "/",
    }


@router.get("/auth/login")
async def login(next: Annotated[str | None, Query()] = None) -> RedirectResponse:
    """Kick off the OAuth flow. Sets a short-lived `oauth_state` cookie
    and redirects to Google.
    """
    if not settings.google_oauth_client_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth is not configured. Set GOOGLE_OAUTH_CLIENT_ID/SECRET.",
        )
    safe_next = next if _is_safe_next(next) else None
    state = auth_service.encode_state(next_url=safe_next)

    response = RedirectResponse(
        url=auth_service.authorize_url(state),
        status_code=status.HTTP_302_FOUND,
    )
    response.set_cookie(
        auth_service.STATE_COOKIE,
        state,
        max_age=auth_service.STATE_MAX_AGE_SECONDS,
        **_cookie_kwargs(),
    )
    return response


@router.get("/auth/callback")
async def callback(
    request: Request,
    code: Annotated[str | None, Query()] = None,
    state: Annotated[str | None, Query()] = None,
    error: Annotated[str | None, Query()] = None,
    session: AsyncSession = Depends(session_dependency),
) -> RedirectResponse:
    """Complete the OAuth round-trip. Validate state, exchange code,
    upsert user, set session cookie, redirect to the web app.
    """
    if error:
        return _redirect_to_login(error="oauth_denied")
    if not code or not state:
        return _redirect_to_login(error="missing_code")

    state_cookie = request.cookies.get(auth_service.STATE_COOKIE)
    if state_cookie != state:
        logger.warning("oauth state cookie mismatch")
        return _redirect_to_login(error="state_mismatch")

    try:
        state_payload = auth_service.decode_state(state)
    except Exception:
        logger.warning("oauth state invalid or expired")
        return _redirect_to_login(error="state_invalid")

    try:
        token_response = await auth_service.exchange_code(code)
        access_token = token_response.get("access_token")
        if not access_token:
            logger.error("token exchange missing access_token: %s", token_response)
            return _redirect_to_login(error="token_exchange_failed")
        userinfo = await auth_service.fetch_userinfo(access_token)
    except httpx.HTTPError as e:
        logger.exception("oauth token/userinfo http error: %s", e)
        return _redirect_to_login(error="provider_error")

    email = (userinfo.get("email") or "").strip().lower()
    if not email or not userinfo.get("email_verified", True):
        return _redirect_to_login(error="email_not_verified")
    if not settings.is_email_allowed(email):
        logger.info("login denied for %s — not on allowlist", email)
        return _redirect_to_login(error="not_allowed")

    user = await auth_service.upsert_user(
        session,
        email=email,
        name=userinfo.get("name") or email,
    )

    session_cookie_value = auth_service.encode_session(str(user.id), user.email)
    next_url = state_payload.get("next") or "/"
    response = RedirectResponse(
        url=urljoin(settings.web_base_url + "/", next_url.lstrip("/")),
        status_code=status.HTTP_302_FOUND,
    )
    response.delete_cookie(auth_service.STATE_COOKIE, path="/")
    response.set_cookie(
        auth_service.SESSION_COOKIE,
        session_cookie_value,
        max_age=settings.auth_session_max_age_hours * 3600,
        **_cookie_kwargs(),
    )
    return response


@router.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout() -> Response:
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    response.delete_cookie(auth_service.SESSION_COOKIE, path="/")
    return response


@router.get("/auth/me", response_model=UserMe)
async def me(user: User = Depends(current_user)) -> UserMe:
    return UserMe.model_validate(user)


def _redirect_to_login(*, error: str) -> RedirectResponse:
    """Send the user back to the web /login screen with an error code in
    the query string the login page can surface.
    """
    return RedirectResponse(
        url=f"{settings.web_base_url}/login?error={quote(error)}",
        status_code=status.HTTP_302_FOUND,
    )
