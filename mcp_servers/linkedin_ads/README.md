# LinkedIn Ads MCP server

A stdio MCP server that exposes the agency's LinkedIn Ads data to
Claude (Code, Desktop, or any MCP-aware client). It's a thin proxy on
top of the `agency_ads` FastAPI app's `/linkedin/mcp/*` endpoints —
the app owns OAuth, token refresh, and the database, so this process
is stateless and the connection stays alive across Claude sessions as
long as the worker is running.

## Architecture

```
┌────────────────────┐         ┌──────────────────────┐
│   Claude (MCP)     │ ◀────── │   linkedin_ads MCP   │
│   - skills / chat  │  stdio  │   (this process)     │
└────────────────────┘         └──────────┬───────────┘
                                          │ HTTPS + Bearer
                                          ▼
                            ┌──────────────────────────────┐
                            │   agency_ads FastAPI         │
                            │   /linkedin/mcp/* endpoints  │
                            └──────────┬───────────────────┘
                                       │
                            ┌──────────▼──────────────┐
                            │   Postgres              │
                            │   linkedin_connections  │
                            └──────────▲──────────────┘
                                       │ refresh tick (hourly)
                            ┌──────────┴──────────────┐
                            │   RQ worker             │
                            │   refresh_linkedin_…    │
                            └─────────────────────────┘
```

## One-time setup

1. **Connect a LinkedIn account through the web app**

   Sign in to the agency tool, open a client, click "Connect LinkedIn".
   The app stores the access + refresh tokens; the worker keeps them
   alive going forward.

2. **Generate a service token** (skip if you already have one in `.env`):

   ```bash
   python -c 'import secrets; print(secrets.token_urlsafe(32))'
   ```

   Set it on the API:

   ```env
   AGENCY_SERVICE_TOKEN=<paste>
   ```

   …and restart the API (`make dev` or `fly deploy`).

3. **Install the MCP server** in the repo's worktree:

   ```bash
   uv pip install -e ./mcp_servers/linkedin_ads
   ```

   Or run it ad-hoc with uv:

   ```bash
   AGENCY_API_BASE_URL=http://localhost:8000 \
   AGENCY_SERVICE_TOKEN=<paste> \
     uv run --directory mcp_servers/linkedin_ads agency-linkedin-mcp
   ```

## Wire it into Claude Code

Add to `~/.claude/mcp_servers.json` (or your project's MCP config):

```json
{
  "mcpServers": {
    "linkedin-ads": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/absolute/path/to/Google-Ads-Tool/mcp_servers/linkedin_ads",
        "agency-linkedin-mcp"
      ],
      "env": {
        "AGENCY_API_BASE_URL": "http://localhost:8000",
        "AGENCY_SERVICE_TOKEN": "<your-token>"
      }
    }
  }
}
```

Then in any Claude Code session:

```
> What's the connection health of all LinkedIn-enabled clients?
> Pull last 30 days of campaign performance for acme.
```

Claude will discover the tools, call `linkedin_list_clients`, etc.

## Wire it into Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`
(macOS) and add the same block under `mcpServers`. Restart Claude
Desktop.

## Tools

| Tool | What it returns |
|---|---|
| `linkedin_list_clients` | All agency clients with connection status. |
| `linkedin_connection_health` | One client: status, expiry, last error. |
| `linkedin_list_ad_accounts` | Ad accounts the connected member can manage. |
| `linkedin_list_campaigns` | Campaigns under one ad account. |
| `linkedin_get_analytics` | Daily metrics for the last N days, by pivot. |

All tools are read-only by design. Writes go through the agency's
Action Queue (draft → approve → push) — that flow is intentionally
not exposed through MCP yet.

## Staying connected

The web app's RQ worker runs `refresh_linkedin_tokens` every hour. For
each connection where the access token expires within the next
`LINKEDIN_REFRESH_SKEW_SECONDS` window (default 7 days), it trades the
refresh token for a new one and updates the row. Connections that
LinkedIn has revoked, or whose refresh tokens have themselves expired
(LinkedIn caps these at 365 days), get flagged `needs_reauth` — the
UI then prompts the user to re-authorize.

As long as someone re-authorizes once, the MCP server keeps working
indefinitely from Claude's perspective.
