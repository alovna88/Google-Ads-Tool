"""FastAPI dependencies shared across routes."""

import uuid
from typing import Annotated

from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agency_ads.db import session_dependency
from agency_ads.models import User
from agency_ads.services import auth as auth_service


async def current_user(
    session: Annotated[AsyncSession, Depends(session_dependency)],
    session_cookie: Annotated[str | None, Cookie(alias=auth_service.SESSION_COOKIE)] = None,
) -> User:
    """Resolve the authenticated user from the session cookie.

    Raises 401 if the cookie is missing, malformed, expired, or points to
    a user that no longer exists.
    """
    if not session_cookie:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="not authenticated")

    payload = auth_service.decode_session(session_cookie)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid session")

    try:
        user_id = uuid.UUID(payload["uid"])
    except (KeyError, ValueError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="malformed session",
        ) from e

    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="user not found")
    return user
