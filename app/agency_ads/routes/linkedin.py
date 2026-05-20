"""LinkedIn Ads endpoints.

Three audiences, one router:

- Browser (staff session cookie): /linkedin/connect, /linkedin/callback,
  /linkedin/connections.
- Staff UI (session): /linkedin/clients/{slug}/* read endpoints.
- MCP server (static service token): /linkedin/mcp/* — same data,
  authenticated via `Authorization: Bearer $AGENCY_SERVICE_TOKEN`.

Tokens themselves never leave the API — the only way to act as a
LinkedIn user is via these endpoints.
"""

import logging
import uuid
from typing import Annotated
from urllib.parse import quote

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agency_ads.config import settings
from agency_ads.db import session_dependency
from agency_ads.dependencies import current_user
from agency_ads.models import Client, LinkedinConnection, User
from agency_ads.schemas.linkedin import (
    LinkedinAdAccount,
    LinkedinAnalytics,
    LinkedinAnalyticsRow,
    LinkedinCampaign,
    LinkedinCampaignList,
    LinkedinConnectionList,
    LinkedinConnectionRead,
    LinkedinConnectStartResponse,
    LinkedinHealth,
)
from agency_ads.services import linkedin_client, linkedin_connections, linkedin_oauth
from agency_ads.services.linkedin_client import LinkedinApiError

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Auth shims
# ---------------------------------------------------------------------------


async def require_service_token(
    authorization: Annotated[str | None, Header()] = None,
) -> None:
    """Verify the static service token used by the MCP server.

    Refuses with 503 if no token is configured — that way a misconfigured
    deployment fails closed instead of accepting unauthenticated calls.
    """
    if not settings.agency_service_token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AGENCY_SERVICE_TOKEN not configured on the API.",
        )
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing bearer token")
    token = authorization.split(" ", 1)[1].strip()
    # Constant-time compare to avoid token-prefix timing leaks.
    import hmac

    if not hmac.compare_digest(token, settings.agency_service_token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid service token")


def _cookie_kwargs() -> dict:
    return {
        "httponly": True,
        "samesite": "lax",
        "secure": settings.is_production,
        "path": "/",
    }


def _serialize(connection: LinkedinConnection) -> LinkedinConnectionRead:
    return LinkedinConnectionRead.model_validate(
        {
            "id": connection.id,
            "client_id": connection.client_id,
            "linkedin_member_urn": connection.linkedin_member_urn,
            "linkedin_member_name": connection.linkedin_member_name,
            "scope": connection.scope,
            "status": connection.status,
            "expires_at": connection.expires_at,
            "refresh_token_expires_at": connection.refresh_token_expires_at,
            "ad_accounts": [LinkedinAdAccount(**a) for a in (connection.ad_accounts or [])] or None,
            "last_refreshed_at": connection.last_refreshed_at,
            "last_error": connection.last_error,
            "last_error_at": connection.last_error_at,
            "created_at": connection.created_at,
            "updated_at": connection.updated_at,
        }
    )


def _health(client: Client, connection: LinkedinConnection | None) -> LinkedinHealth:
    if connection is None:
        return LinkedinHealth(
            client_id=client.id,
            client_slug=client.slug,
            connected=False,
            status="never",
            expires_at=None,
            seconds_until_expiry=None,
            last_refreshed_at=None,
            last_error=None,
        )
    return LinkedinHealth(
        client_id=client.id,
        client_slug=client.slug,
        connected=connection.status == "connected",
        status=connection.status,
        expires_at=connection.expires_at,
        seconds_until_expiry=linkedin_connections.seconds_until_expiry(connection),
        last_refreshed_at=connection.last_refreshed_at,
        last_error=connection.last_error,
    )


# ---------------------------------------------------------------------------
# OAuth flow (staff session)
# ---------------------------------------------------------------------------


@router.get("/linkedin/connect")
async def linkedin_connect(
    client_id: Annotated[uuid.UUID, Query()],
    session: Annotated[AsyncSession, Depends(session_dependency)],
    user: Annotated[User, Depends(current_user)],
    next: Annotated[str | None, Query()] = None,
) -> RedirectResponse:
    """Begin the LinkedIn OAuth flow for a specific agency client."""
    if not settings.linkedin_client_id or not settings.linkedin_client_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LinkedIn OAuth is not configured. Set LINKEDIN_CLIENT_ID/SECRET.",
        )
    client = (
        await session.execute(select(Client).where(Client.id == client_id))
    ).scalar_one_or_none()
    if client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="client not found")

    state = linkedin_oauth.encode_state(client_id=str(client_id), next_url=next)
    response = RedirectResponse(
        url=linkedin_oauth.authorize_url(state),
        status_code=status.HTTP_302_FOUND,
    )
    response.set_cookie(
        linkedin_oauth.STATE_COOKIE,
        state,
        max_age=linkedin_oauth.STATE_MAX_AGE_SECONDS,
        **_cookie_kwargs(),
    )
    return response


@router.get("/linkedin/connect/start", response_model=LinkedinConnectStartResponse)
async def linkedin_connect_start(
    client_id: Annotated[uuid.UUID, Query()],
    session: Annotated[AsyncSession, Depends(session_dependency)],
    user: Annotated[User, Depends(current_user)],
    next: Annotated[str | None, Query()] = None,
) -> LinkedinConnectStartResponse:
    """JSON variant of `/linkedin/connect` for popup-based flows. The
    caller is responsible for setting the state cookie via `/connect`
    instead if it wants the redirect path.
    """
    if not settings.linkedin_client_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LinkedIn OAuth is not configured.",
        )
    client = (
        await session.execute(select(Client).where(Client.id == client_id))
    ).scalar_one_or_none()
    if client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="client not found")
    state = linkedin_oauth.encode_state(client_id=str(client_id), next_url=next)
    return LinkedinConnectStartResponse(
        authorize_url=linkedin_oauth.authorize_url(state),
        state=state,
    )


@router.get("/linkedin/callback")
async def linkedin_callback(
    request: Request,
    session: Annotated[AsyncSession, Depends(session_dependency)],
    code: Annotated[str | None, Query()] = None,
    state: Annotated[str | None, Query()] = None,
    error: Annotated[str | None, Query()] = None,
    error_description: Annotated[str | None, Query()] = None,
) -> RedirectResponse:
    """LinkedIn OAuth redirect target. Validate state, exchange code,
    persist tokens, redirect to the UI.

    We deliberately don't require a staff session here because the
    redirect happens through the user's browser; the state cookie set
    in /linkedin/connect provides CSRF.
    """
    if error:
        logger.info("linkedin oauth error=%s desc=%s", error, error_description)
        return _redirect_to_web(error=f"linkedin_{error}")
    if not code or not state:
        return _redirect_to_web(error="linkedin_missing_code")

    state_cookie = request.cookies.get(linkedin_oauth.STATE_COOKIE)
    if state_cookie != state:
        return _redirect_to_web(error="linkedin_state_mismatch")

    try:
        payload = linkedin_oauth.decode_state(state)
    except Exception:
        return _redirect_to_web(error="linkedin_state_invalid")

    try:
        client_id = uuid.UUID(payload["cid"])
    except (KeyError, ValueError):
        return _redirect_to_web(error="linkedin_state_invalid")

    client = (
        await session.execute(select(Client).where(Client.id == client_id))
    ).scalar_one_or_none()
    if client is None:
        return _redirect_to_web(error="linkedin_client_missing")

    # The staff user who completed the flow — best effort; the row is
    # still useful without it.
    connected_by_user_id: uuid.UUID | None = None
    try:
        from agency_ads.services import auth as auth_service

        session_cookie = request.cookies.get(auth_service.SESSION_COOKIE)
        if session_cookie:
            decoded = auth_service.decode_session(session_cookie)
            if decoded:
                connected_by_user_id = uuid.UUID(decoded["uid"])
    except Exception:  # noqa: BLE001
        pass

    try:
        token_response = await linkedin_oauth.exchange_code(code)
    except Exception as e:  # noqa: BLE001
        logger.exception("linkedin token exchange failed: %s", e)
        return _redirect_to_web(error="linkedin_token_exchange_failed")

    access_token = token_response.get("access_token")
    if not access_token:
        return _redirect_to_web(error="linkedin_token_exchange_failed")

    try:
        profile = await linkedin_oauth.fetch_member_profile(access_token)
    except Exception as e:  # noqa: BLE001
        logger.warning("linkedin userinfo failed: %s", e)
        profile = {}

    member_urn = (
        profile.get("sub")
        and f"urn:li:person:{profile['sub']}"
        or profile.get("urn")
        or "urn:li:person:unknown"
    )
    member_name = profile.get("name") or profile.get("given_name") or None

    await linkedin_connections.upsert_from_token_response(
        session,
        client_id=client_id,
        token_response=token_response,
        member_urn=member_urn,
        member_name=member_name,
        connected_by_user_id=connected_by_user_id,
    )

    next_url = payload.get("next") or f"/clients/{client.slug}"
    response = RedirectResponse(
        url=f"{settings.web_base_url}{next_url}",
        status_code=status.HTTP_302_FOUND,
    )
    response.delete_cookie(linkedin_oauth.STATE_COOKIE, path="/")
    return response


def _redirect_to_web(*, error: str) -> RedirectResponse:
    return RedirectResponse(
        url=f"{settings.web_base_url}/clients?error={quote(error)}",
        status_code=status.HTTP_302_FOUND,
    )


# ---------------------------------------------------------------------------
# Staff-facing read endpoints
# ---------------------------------------------------------------------------


@router.get("/linkedin/connections", response_model=LinkedinConnectionList)
async def list_connections_endpoint(
    session: Annotated[AsyncSession, Depends(session_dependency)],
    user: Annotated[User, Depends(current_user)],
) -> LinkedinConnectionList:
    items = await linkedin_connections.list_connections(session)
    return LinkedinConnectionList(items=[_serialize(c) for c in items], total=len(items))


@router.get("/linkedin/clients/{slug}/health", response_model=LinkedinHealth)
async def client_health(
    slug: str,
    session: Annotated[AsyncSession, Depends(session_dependency)],
    user: Annotated[User, Depends(current_user)],
) -> LinkedinHealth:
    client, connection = await linkedin_connections.get_connection_for_slug(session, slug)
    if client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="client not found")
    return _health(client, connection)


@router.get("/linkedin/clients/{slug}/accounts", response_model=list[LinkedinAdAccount])
async def client_ad_accounts(
    slug: str,
    session: Annotated[AsyncSession, Depends(session_dependency)],
    user: Annotated[User, Depends(current_user)],
    refresh: Annotated[bool, Query()] = False,
) -> list[LinkedinAdAccount]:
    client, connection = await linkedin_connections.get_connection_for_slug(session, slug)
    if client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="client not found")
    if connection is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="LinkedIn not connected for this client"
        )
    if not refresh and connection.ad_accounts:
        return [LinkedinAdAccount(**a) for a in connection.ad_accounts]
    try:
        accounts = await linkedin_client.list_ad_accounts(session, connection)
    except LinkedinApiError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message) from e
    await linkedin_connections.store_ad_accounts(session, connection, accounts)
    return [LinkedinAdAccount(**a) for a in accounts]


@router.get(
    "/linkedin/clients/{slug}/accounts/{account_id}/campaigns",
    response_model=LinkedinCampaignList,
)
async def client_campaigns(
    slug: str,
    account_id: str,
    session: Annotated[AsyncSession, Depends(session_dependency)],
    user: Annotated[User, Depends(current_user)],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> LinkedinCampaignList:
    client, connection = await linkedin_connections.get_connection_for_slug(session, slug)
    if connection is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="not connected")
    try:
        items = await linkedin_client.list_campaigns(
            session, connection, ad_account_id=account_id, limit=limit
        )
    except LinkedinApiError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message) from e
    return LinkedinCampaignList(
        items=[LinkedinCampaign(**c) for c in items], total=len(items)
    )


@router.get(
    "/linkedin/clients/{slug}/accounts/{account_id}/analytics",
    response_model=LinkedinAnalytics,
)
async def client_analytics(
    slug: str,
    account_id: str,
    session: Annotated[AsyncSession, Depends(session_dependency)],
    user: Annotated[User, Depends(current_user)],
    days: Annotated[int, Query(ge=1, le=365)] = 30,
    pivot: Annotated[str, Query()] = "CAMPAIGN",
) -> LinkedinAnalytics:
    client, connection = await linkedin_connections.get_connection_for_slug(session, slug)
    if connection is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="not connected")
    try:
        rows = await linkedin_client.get_analytics(
            session, connection, ad_account_id=account_id, days=days, pivot=pivot
        )
    except LinkedinApiError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message) from e
    return LinkedinAnalytics(items=[LinkedinAnalyticsRow(**r) for r in rows])


@router.delete(
    "/linkedin/clients/{slug}/connection",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def disconnect(
    slug: str,
    session: Annotated[AsyncSession, Depends(session_dependency)],
    user: Annotated[User, Depends(current_user)],
) -> None:
    client, connection = await linkedin_connections.get_connection_for_slug(session, slug)
    if connection is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not connected")
    await linkedin_connections.delete_connection(session, connection)


@router.post(
    "/linkedin/clients/{slug}/refresh",
    response_model=LinkedinHealth,
)
async def manual_refresh(
    slug: str,
    session: Annotated[AsyncSession, Depends(session_dependency)],
    user: Annotated[User, Depends(current_user)],
) -> LinkedinHealth:
    """Force a token refresh now. Useful for the 'Reconnect' button in
    the UI when the auto-refresher hasn't fired yet.
    """
    client, connection = await linkedin_connections.get_connection_for_slug(session, slug)
    if connection is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not connected")
    connection = await linkedin_client.ensure_fresh_token(session, connection)
    return _health(client, connection)


# ---------------------------------------------------------------------------
# MCP-facing endpoints (static bearer-token auth)
# ---------------------------------------------------------------------------

mcp_router = APIRouter(
    prefix="/linkedin/mcp",
    dependencies=[Depends(require_service_token)],
    tags=["linkedin-mcp"],
)


@mcp_router.get("/clients")
async def mcp_list_clients(
    session: Annotated[AsyncSession, Depends(session_dependency)],
) -> list[LinkedinHealth]:
    """List all agency clients along with their LinkedIn connection
    status. The MCP server uses this as its top-level discovery call.
    """
    clients = (await session.execute(select(Client).order_by(Client.name))).scalars().all()
    out: list[LinkedinHealth] = []
    for client in clients:
        connection = await linkedin_connections.get_connection_for_client(session, client.id)
        out.append(_health(client, connection))
    return out


@mcp_router.get("/clients/{slug}/health", response_model=LinkedinHealth)
async def mcp_client_health(
    slug: str,
    session: Annotated[AsyncSession, Depends(session_dependency)],
) -> LinkedinHealth:
    client, connection = await linkedin_connections.get_connection_for_slug(session, slug)
    if client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="client not found")
    return _health(client, connection)


@mcp_router.get("/clients/{slug}/accounts", response_model=list[LinkedinAdAccount])
async def mcp_ad_accounts(
    slug: str,
    session: Annotated[AsyncSession, Depends(session_dependency)],
    refresh: Annotated[bool, Query()] = False,
) -> list[LinkedinAdAccount]:
    client, connection = await linkedin_connections.get_connection_for_slug(session, slug)
    if connection is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="not connected")
    if not refresh and connection.ad_accounts:
        return [LinkedinAdAccount(**a) for a in connection.ad_accounts]
    try:
        accounts = await linkedin_client.list_ad_accounts(session, connection)
    except LinkedinApiError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message) from e
    await linkedin_connections.store_ad_accounts(session, connection, accounts)
    return [LinkedinAdAccount(**a) for a in accounts]


@mcp_router.get(
    "/clients/{slug}/accounts/{account_id}/campaigns",
    response_model=LinkedinCampaignList,
)
async def mcp_campaigns(
    slug: str,
    account_id: str,
    session: Annotated[AsyncSession, Depends(session_dependency)],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> LinkedinCampaignList:
    client, connection = await linkedin_connections.get_connection_for_slug(session, slug)
    if connection is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="not connected")
    try:
        items = await linkedin_client.list_campaigns(
            session, connection, ad_account_id=account_id, limit=limit
        )
    except LinkedinApiError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message) from e
    return LinkedinCampaignList(
        items=[LinkedinCampaign(**c) for c in items], total=len(items)
    )


@mcp_router.get(
    "/clients/{slug}/accounts/{account_id}/analytics",
    response_model=LinkedinAnalytics,
)
async def mcp_analytics(
    slug: str,
    account_id: str,
    session: Annotated[AsyncSession, Depends(session_dependency)],
    days: Annotated[int, Query(ge=1, le=365)] = 30,
    pivot: Annotated[str, Query()] = "CAMPAIGN",
) -> LinkedinAnalytics:
    client, connection = await linkedin_connections.get_connection_for_slug(session, slug)
    if connection is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="not connected")
    try:
        rows = await linkedin_client.get_analytics(
            session, connection, ad_account_id=account_id, days=days, pivot=pivot
        )
    except LinkedinApiError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message) from e
    return LinkedinAnalytics(items=[LinkedinAnalyticsRow(**r) for r in rows])
