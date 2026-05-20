"""LinkedIn Ads MCP server — stdio transport.

Exposes a handful of read-only tools that Claude can call to inspect
LinkedIn Ads accounts and pull recent performance. Each tool maps to a
single `/linkedin/mcp/*` endpoint on the agency_ads API; the API owns
OAuth + token refresh, so this server stays "always connected" as long
as the worker is running.

Environment:

    AGENCY_API_BASE_URL   default: http://localhost:8000
    AGENCY_SERVICE_TOKEN  required — must match settings.agency_service_token

Run with:

    uv run --directory mcp_servers/linkedin_ads agency-linkedin-mcp

or wire into Claude Desktop / Code via the standard MCP config — see
the README.
"""

from __future__ import annotations

import logging
import os
import sys
from typing import Any

import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

logger = logging.getLogger("agency_linkedin_mcp")

DEFAULT_BASE_URL = "http://localhost:8000"


class AgencyApiError(Exception):
    """Raised when the agency API returns a non-2xx response."""


def _base_url() -> str:
    return os.environ.get("AGENCY_API_BASE_URL", DEFAULT_BASE_URL).rstrip("/")


def _token() -> str:
    token = os.environ.get("AGENCY_SERVICE_TOKEN", "").strip()
    if not token:
        raise AgencyApiError(
            "AGENCY_SERVICE_TOKEN is not set. Generate one and "
            "set it on both the API and the MCP server."
        )
    return token


async def _get(path: str, *, params: dict | None = None) -> Any:
    headers = {"Authorization": f"Bearer {_token()}"}
    url = f"{_base_url()}{path}"
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(url, headers=headers, params=params)
    if response.status_code >= 400:
        raise AgencyApiError(
            f"agency API {response.status_code} on GET {path}: {response.text[:500]}"
        )
    try:
        return response.json()
    except ValueError:
        return response.text


def _format(payload: Any) -> list[TextContent]:
    """Return MCP TextContent with a JSON-stringified payload. Tools
    return structured data — Claude is happier reading JSON than prose
    here because it'll often want to filter or chart it.
    """
    import json

    return [TextContent(type="text", text=json.dumps(payload, indent=2, default=str))]


server: Server = Server("agency-linkedin-ads")


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="linkedin_list_clients",
            description=(
                "List every agency client with their LinkedIn Ads "
                "connection status. Start here to discover which clients "
                "have a working connection and which need re-auth."
            ),
            inputSchema={"type": "object", "properties": {}, "additionalProperties": False},
        ),
        Tool(
            name="linkedin_connection_health",
            description=(
                "Return the LinkedIn connection status for one agency "
                "client: expiry time, last refresh, last error if any."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "client_slug": {
                        "type": "string",
                        "description": "Agency client slug, e.g. 'acme'.",
                    },
                },
                "required": ["client_slug"],
                "additionalProperties": False,
            },
        ),
        Tool(
            name="linkedin_list_ad_accounts",
            description=(
                "List the LinkedIn ad accounts the connected member can "
                "manage for the given agency client. Pass refresh=true "
                "to skip the cached list and re-fetch from LinkedIn."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "client_slug": {"type": "string"},
                    "refresh": {"type": "boolean", "default": False},
                },
                "required": ["client_slug"],
                "additionalProperties": False,
            },
        ),
        Tool(
            name="linkedin_list_campaigns",
            description=(
                "List campaigns under a LinkedIn ad account. Returns "
                "id, name, status, type, objective, budgets, and "
                "schedule. Up to `limit` campaigns (default 50, max 200)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "client_slug": {"type": "string"},
                    "ad_account_id": {
                        "type": "string",
                        "description": "Numeric LinkedIn ad account id (no urn: prefix).",
                    },
                    "limit": {"type": "integer", "default": 50, "minimum": 1, "maximum": 200},
                },
                "required": ["client_slug", "ad_account_id"],
                "additionalProperties": False,
            },
        ),
        Tool(
            name="linkedin_get_analytics",
            description=(
                "Pull aggregated analytics for an ad account, grouped "
                "by pivot (CAMPAIGN, CREATIVE, ...). Returns one row "
                "per pivot per day for the last `days` days."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "client_slug": {"type": "string"},
                    "ad_account_id": {"type": "string"},
                    "days": {"type": "integer", "default": 30, "minimum": 1, "maximum": 365},
                    "pivot": {
                        "type": "string",
                        "default": "CAMPAIGN",
                        "enum": [
                            "CAMPAIGN",
                            "CREATIVE",
                            "CAMPAIGN_GROUP",
                            "ACCOUNT",
                            "COMPANY",
                            "MEMBER_COMPANY_SIZE",
                            "MEMBER_INDUSTRY",
                            "MEMBER_SENIORITY",
                            "MEMBER_JOB_TITLE",
                        ],
                    },
                },
                "required": ["client_slug", "ad_account_id"],
                "additionalProperties": False,
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any] | None) -> list[TextContent]:
    arguments = arguments or {}
    try:
        if name == "linkedin_list_clients":
            return _format(await _get("/linkedin/mcp/clients"))
        if name == "linkedin_connection_health":
            slug = arguments["client_slug"]
            return _format(await _get(f"/linkedin/mcp/clients/{slug}/health"))
        if name == "linkedin_list_ad_accounts":
            slug = arguments["client_slug"]
            params = {"refresh": "true"} if arguments.get("refresh") else None
            return _format(await _get(f"/linkedin/mcp/clients/{slug}/accounts", params=params))
        if name == "linkedin_list_campaigns":
            slug = arguments["client_slug"]
            account_id = arguments["ad_account_id"]
            limit = int(arguments.get("limit", 50))
            return _format(
                await _get(
                    f"/linkedin/mcp/clients/{slug}/accounts/{account_id}/campaigns",
                    params={"limit": str(limit)},
                )
            )
        if name == "linkedin_get_analytics":
            slug = arguments["client_slug"]
            account_id = arguments["ad_account_id"]
            params = {
                "days": str(int(arguments.get("days", 30))),
                "pivot": arguments.get("pivot", "CAMPAIGN"),
            }
            return _format(
                await _get(
                    f"/linkedin/mcp/clients/{slug}/accounts/{account_id}/analytics",
                    params=params,
                )
            )
        return [TextContent(type="text", text=f"Unknown tool: {name}")]
    except AgencyApiError as e:
        return [TextContent(type="text", text=f"Error: {e}")]
    except httpx.HTTPError as e:
        return [TextContent(type="text", text=f"Transport error contacting agency API: {e}")]


async def _run() -> None:
    logging.basicConfig(
        level=os.environ.get("LOG_LEVEL", "INFO"),
        stream=sys.stderr,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )
    logger.info(
        "starting LinkedIn Ads MCP server base_url=%s token_set=%s",
        _base_url(),
        bool(os.environ.get("AGENCY_SERVICE_TOKEN")),
    )
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


def main() -> None:
    import asyncio

    asyncio.run(_run())


if __name__ == "__main__":
    main()
