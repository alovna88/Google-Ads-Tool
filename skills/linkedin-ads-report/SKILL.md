---
name: linkedin-ads-report
description: Pull a LinkedIn Ads performance snapshot for an agency client via the linkedin-ads MCP server. Returns campaign-level spend, impressions, clicks, conversions, and lead-form fills for the trailing 7/30/90 days alongside a short narrative summary. Use when an SDR / AE asks "how's LinkedIn doing for {client}?" or before a weekly review.
---

# /linkedin-ads-report

## Preconditions

Refuse to run unless ALL are true. State which is missing and stop.

1. The `linkedin-ads` MCP server is registered with Claude Code (look
   for the `linkedin_list_clients` tool). If not, point the user at
   `mcp_servers/linkedin_ads/README.md`.
2. `CLAUDE.md` exists in the current directory and names the agency
   client by slug — e.g. `slug: acme` — so the skill knows which
   client to pull. If absent, ask the user for the slug.

## What to do

1. **Resolve the client.** Call `linkedin_list_clients`. If the slug
   from CLAUDE.md isn't present, list the available slugs and stop. If
   the matching row has `connected: false`, surface the `status` and
   `last_error` and tell the user how to reconnect:
   `make dev`-time URL: `http://localhost:3000/clients/{slug}` →
   "Connect LinkedIn".

2. **Pick an ad account.** Call `linkedin_list_ad_accounts` for the
   client. If multiple, ask the user which one (unless CLAUDE.md
   specifies `linkedin_ad_account_id:`). If one, use it.

3. **Pull the data.**
   - `linkedin_list_campaigns(client_slug, ad_account_id)`
   - `linkedin_get_analytics(client_slug, ad_account_id, days=7, pivot="CAMPAIGN")`
   - `linkedin_get_analytics(client_slug, ad_account_id, days=30, pivot="CAMPAIGN")`

4. **Compose the report.** Produce a single markdown block with:

   - **Header**: client name, ad account name, "last 7d / 30d", today's date.
   - **Account totals table**: impressions, clicks, CTR, spend, CPM,
     conversions, lead-form fills, CPA. Two columns: 7d and 30d.
   - **Top campaigns (7d)**: top 5 by spend, each row has spend,
     impressions, clicks, conversions, lead-form fills, CTR, CPL.
   - **Movers (7d vs prior 7d)**: campaigns whose spend changed by
     more than 25% in either direction. Mark each ▲ or ▼.
   - **Notes**: 3–5 sentences calling out one or two specific things to
     dig into — e.g. "Campaign X spent $1.2k but converted 0 in 7d;
     pause or reassign budget." Keep it concrete, not generic.

5. **Save the output.** Write the report to
   `reports/linkedin-{client_slug}-{YYYY-MM-DD}.md`. If `reports/`
   doesn't exist, create it.

## Output style

- No emojis. No marketing-speak.
- Numbers with thousands separators. Currency from the ad account's
  currency field — fall back to `cost_in_usd` if unset.
- If a metric is zero everywhere, omit the column rather than
  carrying a column of zeros.
- If LinkedIn returned an error for one of the calls, include a
  "Data quality" footer noting which call failed and skip the
  derived metrics that depended on it. Do not silently fabricate.
