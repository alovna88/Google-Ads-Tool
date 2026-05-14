---
name: icp-research
description: Mines Reddit threads, G2 reviews, and competitor testimonial pages for verbatim Voice-of-Customer language, then produces a targeting brief — high-intent search queries, audience signals, hook angles — for Google Ads (and Meta if relevant). Run quarterly or at new-campaign launch.
---

# /icp-research

## Why this skill exists

The strongest hooks come from customer language, not the agency's framing. Reddit + G2 + competitor testimonials are the three richest free sources of unfiltered B2B buyer voice. This skill turns those URLs into a structured brief: their words, their problems, their objections, their triggers.

Adapted and B2B-tightened from the HeyOz "Research Your ICP" skill (#6).

## Preconditions

- `CLAUDE.md` exists with §1 (Product, ICP, ACV) and §2 (Targets).
- User provides 3–6 URLs in `competitor/` folder as a plaintext file `competitor/icp-sources.txt` — one URL per line, with optional inline label after a comma (e.g. `https://reddit.com/r/devops/comments/abc, devops pain thread`).
  - Required mix: at least 1 Reddit thread, at least 1 G2/Capterra/TrustRadius review page, at least 1 competitor testimonials/case-study page.

## What to do

### Step 1 — Read every URL

Use WebFetch on each. If the URL returns 403 (Reddit, sometimes), try the `.json` version (e.g. `https://reddit.com/r/.../comments/abc.json`) or an alternative front-end. Note any URL that failed.

### Step 2 — Extract structured signals

For each source, extract:

1. **Problem language** — exact phrases customers use to describe what they're trying to solve. Quote verbatim, with attribution and source URL.
2. **Outcome language** — exact phrases for what they want at the end (e.g. "ship faster", "stop firefighting", "give my CFO a number she trusts").
3. **Trigger events** — what made them start looking. ("We hit 50 employees and the spreadsheet broke.")
4. **Objections / hesitations** — what almost stopped them from buying. ("Worried about migration costs", "Boss said we already have a tool.")
5. **Competitor comparisons** — who they evaluated against and why they switched / chose. Verbatim.
6. **Decision-maker signals** — who in their org makes the call vs writes the check (B2B buying committees: 6–10 people per Involve Digital).
7. **Pricing pain** — exact mentions of "too expensive", "billing surprise", "per-seat creep".

### Step 3 — Cluster

Group across sources:
- Top 5 recurring problems (with verbatim quote support for each)
- Top 5 recurring desired outcomes
- Top 3 recurring objections
- Top 3 recurring competitor switches and why

If a claim appears in only one source, label it "single-source". If it appears in 3+ sources, label it "high-confidence."

### Step 4 — Translate to Google Ads queries

For each recurring problem/outcome, produce 2–4 high-intent search queries that a buyer would type when ready to act:

| Problem / outcome cluster | Buyer mindset | High-intent queries (≥3) | Match type to launch with |
|---|---|---|---|
| "We hit 50 employees, spreadsheets broke" | They're ready to buy a tool | "[category] software for 50+ employees", "best [category] tool for mid-market", "spreadsheet to [category] migration" | Exact + Phrase |
| ... |

Avoid informational queries ("what is X", "how to X") — those are not high-intent.

### Step 5 — Translate to audience signals (for Smart Bidding observation)

Google Ads native targeting for B2B is weak. We use audience **signals** (Observation only) to feed Smart Bidding.

- In-market audiences: pick from Google's in-market audience taxonomy that map to the clusters (e.g. "Business Software → CRM Software"). Name them.
- Affinity audiences: usually too broad for B2B; mention only if highly relevant.
- Customer Match: recommend lists to upload (from CRM) — "Closed-Won similar," "Tier-1 ICP companies."
- Detailed demographics: company size, employer industry — apply where the option exists.

Note that Google does NOT have native firmographic targeting like LinkedIn — be explicit about this limitation.

### Step 6 — Hook angle ranking

Based on language frequency and emotional charge, rank the angles for ad copy:

1. Lead angle — the single hook that appears most frequently AND has the most emotional charge.
2. Secondary angle — useful for variant testing.
3. Tertiary angles — defensible but less proven.

For each angle:
- Verbatim phrase from sources (the seed)
- Suggested headline (≤30 chars) in the brand voice from CLAUDE.md §7
- Suggested description (≤90 chars)

### Step 7 — Voice-of-Customer paragraph

Write a single 4–6 sentence paragraph in the customer's own language, weaving in verbatim phrases. This is the cornerstone reusable asset — for ad copy, landing-page hero sections, sales-enablement.

### Step 8 — Output

Write to `reports/icp-research-YYYY-MM-DD.md`:

```markdown
# ICP Research — [CLIENT NAME] — [DATE]

## Sources analyzed

| URL | Source type | Quotes extracted | Fetched? |
|---|---|---|---|
| ... |

## Voice-of-Customer paragraph

[the 4-6 sentence paragraph]

## Top 5 recurring problems

| Rank | Problem (verbatim cluster) | Confidence | Example quote (+ source) |
|---|---|---|---|

## Top 5 recurring desired outcomes

[same structure]

## Top 3 objections

[same structure]

## Top 3 competitor switch stories

[same structure, including who they switched from/to and why]

## Recommended Google Ads queries (high-intent)

[table from Step 4]

## Recommended audience signals (Observation)

[list, with in-market category names]

## Hook angle ranking

| Rank | Angle | Verbatim seed | Suggested headline | Suggested description |
|---|---|---|---|---|

## Update to CLAUDE.md

Draft additions to CLAUDE.md §1 (ICP refinement) and §7 (brand voice) based on findings.
```

## Rules

- Always quote verbatim. Customer's words > the agency's paraphrase.
- Cite the source URL for every quote.
- Avoid summarizing into agency jargon. If a customer says "spreadsheet hell," put "spreadsheet hell" in the brief, not "data management challenges."
- B2B-specific: surface the buying-committee signal — who's the user, who's the buyer, who's the budget approver.
- If a source URL returned an error, list it and skip — don't invent content for a source you couldn't read.
- Never use generated examples in place of real quotes. If you don't have a quote, say "no quotes available for this cluster."
