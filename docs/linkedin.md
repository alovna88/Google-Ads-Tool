# LinkedIn Ads integration

Three-part integration despite the README's "Google Ads first" stance:

1. **Web app** — OAuth + token storage + background refresh.
2. **MCP server** — read-only tools the agent calls.
3. **Skill** — `/linkedin-ads-report` drives the MCP.

The split keeps secrets in one place: only the FastAPI app sees
LinkedIn access/refresh tokens, and only the worker rotates them.

## What "always connected" means

The web app stores `(access_token, refresh_token, expires_at,
refresh_token_expires_at)` per `(Client, LinkedIn member)` pair in
`linkedin_connections`. An RQ job runs every hour and, for every
connection whose access token expires within
`LINKEDIN_REFRESH_SKEW_SECONDS` (default 7 days), trades the refresh
token for a fresh access token in place. The job re-enqueues itself at
the end of each run; the worker reseeds it on startup if the chain
breaks.

So the connection stays alive without any user action until either:

- LinkedIn revokes the token (user clicked "Disconnect app" on their
  side, or the app's permissions changed), or
- The refresh token itself expires — LinkedIn caps refresh tokens at
  365 days from the original authorization.

When either happens the worker flips the row to `status =
'needs_reauth'` and stores `last_error`. The UI surfaces this on the
client page; one click of "Reconnect" walks the user back through
OAuth and the loop continues.

## One-time setup

1. **Create a LinkedIn app**

   - Go to <https://www.linkedin.com/developers/apps>, create an app
     under your LinkedIn page.
   - Add the **Advertising API** product (manual approval; days to
     weeks).
   - Add redirect URLs:
     - Dev: `http://localhost:3000/api/linkedin/callback`
     - Prod: `https://<your-fly-app>/api/linkedin/callback`
   - Note the Client ID and Client Secret.

2. **Apply for refresh tokens (optional but recommended)**

   Refresh tokens are only issued to apps in the **Marketing Developer
   Platform**. Without them you'll re-auth every ~60 days per client.
   Apply at
   <https://www.linkedin.com/developers/programs/marketing-developer-platform>.

3. **Set env vars**

   ```env
   LINKEDIN_CLIENT_ID=...
   LINKEDIN_CLIENT_SECRET=...
   LINKEDIN_OAUTH_SCOPES=r_ads,r_ads_reporting,r_basicprofile
   LINKEDIN_API_VERSION=202405
   LINKEDIN_REFRESH_SKEW_SECONDS=604800

   AGENCY_SERVICE_TOKEN=<openssl rand -base64 32>
   ```

   Restart `make dev`.

4. **Apply the migration**

   ```bash
   make migrate
   ```

   Creates the `linkedin_connections` table.

5. **Connect a client**

   - Sign in to <http://localhost:3000>.
   - Open or create a client.
   - Click "Connect LinkedIn" (calls `/api/linkedin/connect?client_id=…`).
   - Authorize the app on LinkedIn.
   - On return you'll see the connection's expiry + the ad accounts
     the connected member can manage.

## Wiring the MCP server

See `mcp_servers/linkedin_ads/README.md`. TL;DR: install with
`uv pip install -e mcp_servers/linkedin_ads`, register it in your MCP
config with `AGENCY_API_BASE_URL` and `AGENCY_SERVICE_TOKEN` env vars,
and Claude can call the five tools right away.

## Endpoints

### Staff session (cookie auth)

| Method | Path | Notes |
|---|---|---|
| GET | `/linkedin/connect?client_id=…` | Browser redirect to LinkedIn |
| GET | `/linkedin/connect/start?client_id=…` | JSON variant for popup flows |
| GET | `/linkedin/callback` | OAuth redirect target |
| GET | `/linkedin/connections` | All connections, all clients |
| GET | `/linkedin/clients/{slug}/health` | Status + expiry |
| GET | `/linkedin/clients/{slug}/accounts` | Ad accounts (cached) |
| GET | `/linkedin/clients/{slug}/accounts/{id}/campaigns` | List campaigns |
| GET | `/linkedin/clients/{slug}/accounts/{id}/analytics?days=30&pivot=CAMPAIGN` | Daily metrics |
| POST | `/linkedin/clients/{slug}/refresh` | Force a refresh now |
| DELETE | `/linkedin/clients/{slug}/connection` | Disconnect |

### Service-token (MCP / scripts)

Same data, different prefix and `Authorization: Bearer
$AGENCY_SERVICE_TOKEN` instead of a cookie.

| Method | Path |
|---|---|
| GET | `/linkedin/mcp/clients` |
| GET | `/linkedin/mcp/clients/{slug}/health` |
| GET | `/linkedin/mcp/clients/{slug}/accounts` |
| GET | `/linkedin/mcp/clients/{slug}/accounts/{id}/campaigns` |
| GET | `/linkedin/mcp/clients/{slug}/accounts/{id}/analytics` |

## Known gaps

- **No write features yet.** `rw_ads` is intentionally not in the
  default scope; mutations will go through the Action Queue when they
  ship.
- **Tokens are plain in Postgres.** Production should layer pgcrypto
  or app-side Fernet on `access_token` and `refresh_token`. The shape
  of the table is friendly to a later migration: add `*_ciphertext`
  columns, dual-write, flip readers, drop plaintext.
- **One member per client.** The schema supports multiple LinkedIn
  members per agency client, but the UI surfaces only the latest.
- **No webhook for revocations.** We discover broken connections on
  the next API call or refresh tick. That's typically fine for a
  weekly-report cadence but adds latency for live ops.
