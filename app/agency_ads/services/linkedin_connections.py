"""CRUD + lifecycle helpers for LinkedinConnection rows.

Kept separate from the HTTP client (`linkedin_client.py`) so the
business logic — "is this connection fresh? when did it last error?
which ad accounts can it see?" — has one home.
"""

import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agency_ads.config import settings
from agency_ads.models import Client, LinkedinConnection
from agency_ads.services import linkedin_oauth

logger = logging.getLogger(__name__)


async def list_connections(session: AsyncSession) -> list[LinkedinConnection]:
    result = await session.execute(
        select(LinkedinConnection).order_by(LinkedinConnection.created_at.desc())
    )
    return list(result.scalars().all())


async def get_connection_for_client(
    session: AsyncSession, client_id: uuid.UUID
) -> LinkedinConnection | None:
    """Return the most recently-created connection for an agency client.

    Multiple LinkedIn members could in theory authorize for the same
    client; the convention is "latest wins" for everyday operations.
    """
    result = await session.execute(
        select(LinkedinConnection)
        .where(LinkedinConnection.client_id == client_id)
        .order_by(LinkedinConnection.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def get_connection_for_slug(
    session: AsyncSession, slug: str
) -> tuple[Client, LinkedinConnection] | tuple[None, None]:
    """Resolve `(Client, LinkedinConnection)` by the agency client slug.

    Returns `(None, None)` if no such client; `(Client, None)` if the
    client exists but has never been connected.
    """
    client_q = await session.execute(select(Client).where(Client.slug == slug))
    client = client_q.scalar_one_or_none()
    if client is None:
        return None, None
    connection = await get_connection_for_client(session, client.id)
    return client, connection  # type: ignore[return-value]


async def upsert_from_token_response(
    session: AsyncSession,
    *,
    client_id: uuid.UUID,
    token_response: dict[str, Any],
    member_urn: str,
    member_name: str | None,
    connected_by_user_id: uuid.UUID | None,
) -> LinkedinConnection:
    """Create or replace the connection for (client, member). Persisted
    fields are taken verbatim from the LinkedIn token response so that
    `expires_at`, `refresh_token_expires_at`, and `scope` always reflect
    what LinkedIn last told us.
    """
    access_token = token_response.get("access_token")
    if not access_token:
        raise ValueError("token response missing access_token")

    expires_at = linkedin_oauth.expires_at_from_response(token_response)
    refresh_expires_at = linkedin_oauth.refresh_expires_at_from_response(token_response)
    scope = token_response.get("scope") or ",".join(settings.linkedin_scopes)
    refresh_token = token_response.get("refresh_token")

    result = await session.execute(
        select(LinkedinConnection).where(
            LinkedinConnection.client_id == client_id,
            LinkedinConnection.linkedin_member_urn == member_urn,
        )
    )
    connection = result.scalar_one_or_none()

    now = datetime.now(UTC)
    if connection is None:
        connection = LinkedinConnection(
            client_id=client_id,
            linkedin_member_urn=member_urn,
            linkedin_member_name=member_name,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at,
            refresh_token_expires_at=refresh_expires_at,
            scope=scope,
            status="connected",
            last_refreshed_at=now,
            connected_by_user_id=connected_by_user_id,
        )
        session.add(connection)
    else:
        connection.access_token = access_token
        # Only overwrite refresh_token if a new one was issued — LinkedIn
        # silently re-uses the existing one on plain refreshes.
        if refresh_token:
            connection.refresh_token = refresh_token
        connection.expires_at = expires_at
        if refresh_expires_at:
            connection.refresh_token_expires_at = refresh_expires_at
        connection.scope = scope
        connection.linkedin_member_name = member_name or connection.linkedin_member_name
        connection.status = "connected"
        connection.last_refreshed_at = now
        connection.last_error = None
        connection.last_error_at = None
        if connected_by_user_id:
            connection.connected_by_user_id = connected_by_user_id

    await session.flush()
    return connection


async def mark_error(
    session: AsyncSession,
    connection: LinkedinConnection,
    *,
    status: str,
    message: str,
) -> None:
    """Flag a connection as broken. Used by the refresh worker and the
    API client when LinkedIn returns 401/403.
    """
    connection.status = status
    connection.last_error = message[:1000]
    connection.last_error_at = datetime.now(UTC)
    await session.flush()


async def store_ad_accounts(
    session: AsyncSession,
    connection: LinkedinConnection,
    accounts: list[dict[str, Any]],
) -> None:
    """Cache the list of ad accounts the connection can see. Trimmed to
    the fields we actually display."""
    connection.ad_accounts = accounts
    await session.flush()


async def delete_connection(session: AsyncSession, connection: LinkedinConnection) -> None:
    await session.delete(connection)
    await session.flush()


def seconds_until_expiry(connection: LinkedinConnection) -> int:
    delta = connection.expires_at - datetime.now(UTC)
    return int(delta.total_seconds())


def needs_refresh(connection: LinkedinConnection) -> bool:
    """True when the access token will expire within the configured
    skew. Connections without a refresh token can't be rotated and are
    reported as `needs_reauth` by the worker instead.
    """
    if connection.status not in ("connected", "expired"):
        return False
    if not connection.refresh_token:
        return False
    return seconds_until_expiry(connection) < settings.linkedin_refresh_skew_seconds
