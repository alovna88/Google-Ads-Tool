"""Thin LinkedIn Marketing API client.

Scope is intentionally narrow: list ad accounts, list campaigns, run
analytics. Each call:

1. Resolves a `LinkedinConnection` for the agency client.
2. Refreshes the access token in place if it's near expiry.
3. Hits the LinkedIn REST API with the standard headers.
4. Marks the connection broken on 401/403 so the UI surfaces re-auth
   rather than silently failing.

Read-only by design until write features are wired through the Action
Queue. The `rw_ads` scope deliberately isn't requested in default
config so a leaked token can't mutate the account.
"""

import logging
from datetime import UTC
from typing import Any

import httpx

from agency_ads.config import settings
from agency_ads.models import LinkedinConnection
from agency_ads.services import linkedin_connections, linkedin_oauth

logger = logging.getLogger(__name__)

LINKEDIN_API_BASE = "https://api.linkedin.com"


class LinkedinApiError(Exception):
    """Raised when the LinkedIn API returns an error that the caller
    should propagate as a 4xx/5xx to the user. Stores the upstream
    status so route handlers can mirror it.
    """

    def __init__(self, status_code: int, message: str, payload: Any | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.message = message
        self.payload = payload


def _headers(access_token: str, *, versioned: bool = True) -> dict[str, str]:
    """Standard LinkedIn API headers. The `LinkedIn-Version` header is
    required on `/rest/*` endpoints; the older `/v2/*` endpoints don't
    accept it.
    """
    headers = {
        "Authorization": f"Bearer {access_token}",
        "X-Restli-Protocol-Version": "2.0.0",
    }
    if versioned:
        headers["LinkedIn-Version"] = settings.linkedin_api_version
    return headers


async def ensure_fresh_token(session, connection: LinkedinConnection) -> LinkedinConnection:
    """Refresh the access token if it's within the skew window. Returns
    the (possibly mutated) connection. Doesn't commit — the caller's
    session lifecycle decides when to persist.
    """
    if not linkedin_connections.needs_refresh(connection):
        return connection
    if not connection.refresh_token:
        await linkedin_connections.mark_error(
            session,
            connection,
            status="needs_reauth",
            message="No refresh token on file; user must re-authorize.",
        )
        return connection

    try:
        token_response = await linkedin_oauth.refresh_access_token(connection.refresh_token)
    except httpx.HTTPStatusError as e:
        body = e.response.text
        logger.warning(
            "linkedin refresh failed client=%s status=%s body=%s",
            connection.client_id,
            e.response.status_code,
            body[:200],
        )
        # 400 invalid_grant means the refresh token was revoked or expired.
        new_status = "needs_reauth" if e.response.status_code == 400 else "error"
        await linkedin_connections.mark_error(
            session, connection, status=new_status, message=f"refresh failed: {body[:500]}"
        )
        return connection
    except httpx.HTTPError as e:
        await linkedin_connections.mark_error(
            session, connection, status="error", message=f"refresh transport error: {e}"
        )
        return connection

    return await linkedin_connections.upsert_from_token_response(
        session,
        client_id=connection.client_id,
        token_response=token_response,
        member_urn=connection.linkedin_member_urn,
        member_name=connection.linkedin_member_name,
        connected_by_user_id=connection.connected_by_user_id,
    )


async def _get(
    session,
    connection: LinkedinConnection,
    path: str,
    *,
    params: dict | None = None,
    versioned: bool = True,
) -> dict[str, Any]:
    connection = await ensure_fresh_token(session, connection)
    if connection.status != "connected":
        raise LinkedinApiError(
            409,
            f"LinkedIn connection is {connection.status}: {connection.last_error or 'unknown'}",
        )

    url = f"{LINKEDIN_API_BASE}{path}"
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(url, params=params, headers=_headers(connection.access_token, versioned=versioned))

    if response.status_code in (401, 403):
        await linkedin_connections.mark_error(
            session,
            connection,
            status="needs_reauth",
            message=f"LinkedIn {response.status_code}: {response.text[:500]}",
        )
        raise LinkedinApiError(response.status_code, "LinkedIn rejected the token — re-auth needed.")
    if response.status_code >= 400:
        raise LinkedinApiError(
            response.status_code,
            f"LinkedIn error {response.status_code}: {response.text[:500]}",
            payload=_safe_json(response),
        )
    return _safe_json(response) or {}


def _safe_json(response: httpx.Response) -> Any:
    try:
        return response.json()
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


async def list_ad_accounts(session, connection: LinkedinConnection) -> list[dict[str, Any]]:
    """List sponsored ad accounts the authorized member can access.

    Uses the v2 `/adAccountUsers` finder; for each row we surface the
    account URN, parsed numeric id, role, and reference fields. Two-call
    pattern: first get the assignments, then optionally batch-load
    account names. We do the assignment call only to keep latency low —
    name resolution happens lazily on demand.
    """
    data = await _get(
        session,
        connection,
        "/v2/adAccountUsersV2",
        params={"q": "authenticatedUser"},
        versioned=False,
    )
    elements = data.get("elements") or []
    out: list[dict[str, Any]] = []
    for el in elements:
        account_urn = el.get("account") or ""
        # account URN format: urn:li:sponsoredAccount:12345
        account_id = account_urn.rsplit(":", 1)[-1] if account_urn else ""
        out.append(
            {
                "urn": account_urn,
                "id": account_id,
                "name": el.get("accountName"),
                "role": el.get("role"),
                "currency": None,
                "status": None,
            }
        )
    return out


async def list_campaigns(
    session,
    connection: LinkedinConnection,
    *,
    ad_account_id: str,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """List campaigns under one ad account."""
    path = f"/rest/adAccounts/{ad_account_id}/adCampaigns"
    data = await _get(
        session,
        connection,
        path,
        params={"q": "search", "count": str(limit)},
    )
    out: list[dict[str, Any]] = []
    for el in data.get("elements") or []:
        run_schedule = el.get("runSchedule") or {}
        daily_budget = (el.get("dailyBudget") or {}).get("amount")
        total_budget = (el.get("totalBudget") or {}).get("amount")
        currency = (el.get("dailyBudget") or el.get("totalBudget") or {}).get("currencyCode")
        out.append(
            {
                "id": str(el.get("id") or ""),
                "name": el.get("name") or "",
                "status": el.get("status") or "",
                "type": el.get("type"),
                "objective_type": el.get("objectiveType"),
                "daily_budget": float(daily_budget) if daily_budget else None,
                "total_budget": float(total_budget) if total_budget else None,
                "currency": currency,
                "run_schedule_start": _ms_to_iso(run_schedule.get("start")),
                "run_schedule_end": _ms_to_iso(run_schedule.get("end")),
            }
        )
    return out


async def get_analytics(
    session,
    connection: LinkedinConnection,
    *,
    ad_account_id: str,
    days: int = 30,
    pivot: str = "CAMPAIGN",
) -> list[dict[str, Any]]:
    """Pull the last `days` of analytics, grouped by `pivot`
    (CAMPAIGN, CREATIVE, MEMBER_COMPANY, ...).

    Uses the `/rest/adAnalytics` finder=analytics endpoint. Date range
    is anchored to today and rounded to whole days, which is what the
    LinkedIn UI does too.
    """
    from datetime import date, timedelta

    end = date.today()
    start = end - timedelta(days=max(days - 1, 0))

    params = {
        "q": "analytics",
        "pivot": pivot,
        "timeGranularity": "DAILY",
        "accounts[0]": f"urn:li:sponsoredAccount:{ad_account_id}",
        "dateRange.start.day": str(start.day),
        "dateRange.start.month": str(start.month),
        "dateRange.start.year": str(start.year),
        "dateRange.end.day": str(end.day),
        "dateRange.end.month": str(end.month),
        "dateRange.end.year": str(end.year),
        "fields": ",".join(
            [
                "pivotValue",
                "impressions",
                "clicks",
                "costInUsd",
                "costInLocalCurrency",
                "externalWebsiteConversions",
                "oneClickLeads",
                "dateRange",
            ]
        ),
    }
    data = await _get(session, connection, "/rest/adAnalytics", params=params)
    out: list[dict[str, Any]] = []
    for row in data.get("elements") or []:
        dr = row.get("dateRange") or {}
        out.append(
            {
                "pivot_value": row.get("pivotValue"),
                "date_range_start": _date_struct_to_iso(dr.get("start")),
                "date_range_end": _date_struct_to_iso(dr.get("end")),
                "impressions": int(row.get("impressions") or 0),
                "clicks": int(row.get("clicks") or 0),
                "cost_in_usd": float(row.get("costInUsd") or 0.0),
                "cost_in_local_currency": float(row.get("costInLocalCurrency") or 0.0),
                "external_website_conversions": int(row.get("externalWebsiteConversions") or 0),
                "one_click_leads": int(row.get("oneClickLeads") or 0),
                "metrics": {
                    k: v
                    for k, v in row.items()
                    if k
                    not in (
                        "pivotValue",
                        "dateRange",
                        "impressions",
                        "clicks",
                        "costInUsd",
                        "costInLocalCurrency",
                        "externalWebsiteConversions",
                        "oneClickLeads",
                    )
                },
            }
        )
    return out


def _ms_to_iso(ms: int | None) -> str | None:
    if not ms:
        return None
    from datetime import datetime

    return datetime.fromtimestamp(int(ms) / 1000, tz=UTC).isoformat()


def _date_struct_to_iso(d: dict | None) -> str | None:
    if not d:
        return None
    try:
        return f"{int(d['year']):04d}-{int(d['month']):02d}-{int(d['day']):02d}"
    except (KeyError, ValueError, TypeError):
        return None
