---
name: competitor-watch
description: Monthly competitor monitoring using only free, ToS-clean sources — Wayback Machine landing-page diffs, sitemap diff for new pages, Wappalyzer for tech-stack changes, and (optionally, with explicit opt-in) Google Ads Transparency Center for creative snapshots. Honest about what's NOT available free.
---

# /competitor-watch

## What we CAN do for free / ToS-clean

| Signal | Source | Method |
|---|---|---|
| New / changed landing pages over time | Wayback Machine CDX API | Free, no auth, no scraping ToS issue |
| New pages added to a site | `/sitemap.xml` weekly diff | Standard, ToS-clean |
| Tech stack changes | Wappalyzer CLI (open source) | Local detection, no third-party |
| Are they bidding on YOUR brand? | Google Ads Auction Insights | UI export — not API |
| Their ad creatives (Google) | Google Ads Transparency Center | No API; manual look-up; scraping = ToS gray. Opt-in only. |

## What we CANNOT do free / honestly

| Want | Why not free |
|---|---|
| Competitor keyword list | No free reliable source. Paid: Semrush/Ahrefs/SpyFu. Out of scope. |
| Competitor bid changes over time | Not exposed. |
| Competitor Meta creatives | Meta Ad Library API is EU-political-only since 2026. Manual UI only. |
| Competitor landing page conversion rates | Not observable from outside. |
| Competitor budget / spend | Not observable. |

Be explicit about these limits in the report — don't pretend otherwise.

## Preconditions

- `CLAUDE.md` exists with the client's identity (so we don't accidentally analyze the client as their own competitor).
- A file `competitor/competitors.txt` with one competitor per line, each entry: `name, root_url, [optional Transparency Center advertiser ID]`. Example:
  ```
  Acme Software, https://acmesoftware.com, AR12345
  Globex Tools, https://globex.io
  Initech Cloud, https://initech.cloud, AR67890
  ```

## What to do

### Step 1 — Wayback landing-page diffs

For each competitor, for their root URL + key landing pages (`/`, `/pricing`, `/product`, `/features`, `/demo`, `/`):

1. Query Wayback CDX API:
   ```
   https://web.archive.org/cdx/search/cdx?url=<url>&from=<YYYYMMDD>&to=<YYYYMMDD>&output=json&fl=timestamp,original,statuscode,digest&filter=statuscode:200&collapse=digest
   ```
   - `collapse=digest` collapses unchanged content
   - `from` = 90 days ago, `to` = today
2. For each captured snapshot, fetch the snapshot URL: `https://web.archive.org/web/<timestamp>/<original>`
3. Compare to previous snapshot — note changes in: H1, hero subhead, primary CTA, pricing numbers, customer logos, navigation structure.

### Step 2 — Sitemap diff for new pages

For each competitor:
- Fetch `<root>/sitemap.xml` and any nested sitemaps.
- Compare URL set to last run (stored in `competitor/<slug>/sitemap-last.json`).
- List new URLs and removed URLs.

### Step 3 — Tech stack detection

Run `wappalyzer <url> --json` (if installed locally) for each competitor home page.
Compare to last run. Note adds/removes (e.g. "Added Segment", "Removed Drift, added Intercom").
If Wappalyzer is not installed, skip with a note — don't substitute scraping.

### Step 4 — Google Ads Transparency Center (optional, agency opt-in)

If `competitor/transparency-opt-in.txt` exists in the client folder (one-time agency consent file):
- For each competitor with an advertiser ID, note the URL: `https://adstransparency.google.com/advertiser/<ID>?region=anywhere`
- Provide the link for manual review; do NOT scrape.
- Optionally summarize what the agency staff observes after visiting (paste-in pattern).

If the opt-in file does not exist, skip Transparency Center and put a note in the report.

### Step 5 — Auction Insights (manual upload)

If the agency has uploaded an Auction Insights CSV export to `competitor/auction-insights-YYYY-MM-DD.csv`, parse it and surface:
- New competitors that appeared on the client's brand campaign in the last 30 days
- Competitors whose Impression Share increased > 10pp on any campaign
- Competitors whose Overlap Rate increased significantly

### Step 6 — Cluster into a story

For each competitor, write 1–3 sentences summarizing the month: "Acme rewrote /pricing in week 2 — moved to a usage-based tier from per-seat. Added 4 new pages in the /resources tree. Stack: added Segment, removed Heap. Now bidding on our brand (+18pp Impression Share)."

## Output

Write to `reports/competitor-watch-YYYY-MM-DD.md`:

```markdown
# Competitor Watch — [CLIENT NAME] — last 30 days

## Quick read (one paragraph)

[3–4 sentences summarizing the most important competitor moves this month]

## What's available vs not

[paragraph noting which signals we DID and DIDN'T monitor this month, and why — managed expectations]

## Per competitor

### [Competitor A] (acmesoftware.com)

**Landing-page changes**
- `/pricing` updated 2026-04-12: moved from per-seat ($20/mo) to usage-based ("starts at $0.01/event").
- `/product` headline changed from "Operational analytics" to "Customer 360 in one place".

**New pages**
- `/resources/ebook-cdp-buyers-guide` — published 2026-04-20
- `/case-studies/contoso` — published 2026-04-25

**Tech-stack changes**
- Added: Segment, Mutiny
- Removed: Heap

**Brand bidding** (from Auction Insights)
- Impression Share on our Brand campaign: +18pp month-over-month — actively bidding.

**Action implications**
- [What this means for our client + what we should consider]

### [Competitor B] ...

## Implications for client

| Move | Implication | Suggested action |
|---|---|---|
| Acme moved to usage-based pricing | Pricing-conscious buyers will compare | Update value-prop on our pricing page; test "predictable per-seat" angle |
| Acme bidding on our brand | Brand defense | Tighten Brand campaign max CPC, raise IS target |

## Top 3 actions
1.
2.
3.
```

## Rules

- **Do not scrape Transparency Center** without the explicit opt-in file. The data is public but Google's ToS is restrictive on automated access; this is a legal-review decision, not an engineering one.
- **Wayback Machine is free and fine** — but rate-limit (1 req / sec) and cite snapshots by timestamp.
- **Sitemap diffing assumes the competitor publishes a sitemap.** If not, skip with a note. Don't crawl.
- **Wappalyzer CLI must be installed locally** — if not, skip cleanly.
- **Always state what is and isn't available** at the top of the report. Set expectations.
- **Persist state** between runs in `competitor/<slug>/last-run.json` so next run can do diffs without re-fetching Wayback history.
- **No invented insights.** If Wayback only had one snapshot in the period, you have no "change" to report — say so.
