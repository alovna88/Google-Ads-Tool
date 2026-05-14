---
name: monthly-report
description: Generates the full client-facing monthly report — pipeline KPIs, spend pacing, what worked / what didn't, learnings, next-month plan. Written for the client (not the agency). One-page-per-section, branded export-ready. Run on the first business day of each month.
---

# /monthly-report

## Why this skill exists

The monthly report is the artifact the client uses to decide whether to renew the agency. It needs to (a) prove the agency understands the business, (b) tie spend to pipeline / revenue, (c) be honest about what didn't work, (d) propose a concrete plan for the next 30 days.

This is NOT a weekly summary scaled up. The framing is different — client-facing, not internal-facing.

## Preconditions

- `CLAUDE.md` exists with §1, §2, §3, §9 (stakeholders).
- CSV exports or live MCP queries for:
  - The full month being reported on
  - The prior month (for MoM comparison)
  - Same month last year (for YoY, if data exists)
- Outputs from `/weekly-report` for each week in the month (if present)
- Output from `/account-audit` from this month or last (if present)
- Output from `/competitor-watch` from this month (if present)
- Output from `/search-term-audit` from this month (if present)

## What to do

### Step 1 — Define the period

- Month being reported: `YYYY-MM`
- Window: first to last day, inclusive
- Comparison windows: prior calendar month, same month previous year (label clearly)

### Step 2 — Compute the pipeline waterfall

The reporting backbone. Lead with this — NOT with platform KPIs.

| Stage | Volume | Value | CAC | LTV:CAC | vs target |
|---|---|---|---|---|---|
| Spend | — | $[X] | — | — | [+/-]% vs budget |
| Clicks | [N] | — | — | — | |
| Lead form submissions | [N] | — | $[X]/lead | — | |
| MQL | [N] | — | $[X]/MQL | — | |
| SQL | [N] | $[V] | $[X]/SQL | — | |
| Opportunity | [N] | $[V] | $[X]/opp | — | |
| Closed-Won | [N] | $[V] | $[X]/customer | [X]:[1] | [color] |

Pull values from CLAUDE.md §3 conversion hierarchy. If OCI isn't fully wired, mark stages "estimated" with the assumption used, and call out as a remediation item.

### Step 3 — Spend allocation breakdown

By campaign category (mapped to CLAUDE.md §4 archetypes):

| Category | Spend | % of total | Conv | CAC | ROAS |
|---|---|---|---|---|---|
| Brand | $[X] | [%] | [N] | $[X] | [X] |
| Competitor | $[X] | [%] | [N] | $[X] | [X] |
| Non-brand product | $[X] | [%] | [N] | $[X] | [X] |
| Non-brand problem | $[X] | [%] | [N] | $[X] | [X] |
| Remarketing (RLSA) | $[X] | [%] | [N] | $[X] | [X] |

### Step 4 — What worked (with evidence)

3–5 things, each with:
- The claim ("We launched a new RSA variant in Non-brand Product on April 8")
- The numbers ("+24% CTR, 11 incremental SQLs over 22 days")
- The mechanism (why it worked — what we learned)

### Step 5 — What didn't (honestly)

2–4 things. Same structure as "What worked". B2B agency clients prefer honesty.

### Step 6 — Tracking & infrastructure health

Pull from `/conversion-tracking-health` output:
- OCI upload success rate this month
- GCLID capture rate (sample)
- Any conversion action that dropped > 30% volume (possible tracking break)
- Status of EC4L match rate
- Status of CRM sync (if applicable)

This section is what separates a real B2B SaaS agency report from a generic agency report.

### Step 7 — Competitor moves this month

Pull from `/competitor-watch` if present. 1 paragraph per competitor of substance. Skip competitors with no observed moves rather than padding.

### Step 8 — Search-term insights

From `/search-term-audit` and `/close-variant-checker`:
- Total spend on non-converting terms this month: $[X] ([%] of total)
- Estimated savings from negatives applied: $[X]
- Top n-gram themes wasted on this month
- Top winners promoted to keywords this month

### Step 9 — Next-month plan (the most important section)

5 specific commitments for the coming 30 days. Each:
- The action
- The expected outcome (with a number — leads, CAC, pipeline)
- The risk and how we'll mitigate
- The deadline within the month

Resist generic plans. "Optimize bids" is not a plan. "Drop Target CPA on Competitor campaign from $250 to $200 on May 6 after Q2 conv data is in" is a plan.

### Step 10 — Open questions for the client

The client provides things the agency can't see (CRM data quality, sales velocity, deal-loss reasons, product roadmap signals). List 3–5 specific questions whose answers would improve next month's plan.

## Output

Write to `reports/monthly-YYYY-MM.md` AND a PDF-ready HTML version `reports/monthly-YYYY-MM.html`.

Section layout (one page per section in PDF):

1. **Cover** — Client name, month, top-line metrics card
2. **Pipeline waterfall**
3. **Spend allocation**
4. **What worked**
5. **What didn't**
6. **Tracking & infrastructure health**
7. **Competitor moves**
8. **Search-term insights**
9. **Next-month plan**
10. **Open questions for [CLIENT]**
11. **Appendix** — Full campaign-level table, conversion-action table, audit score (if run this month)

## Rules

- **Client-facing tone.** This is NOT for agency staff — write for a CMO who knows marketing but not Google Ads internals. Define acronyms first time used.
- **Lead with pipeline / CAC, not platform KPIs.** Click-through-rate goes in the appendix.
- **Honesty in "What didn't"** is a feature. Clients spot manicured reports.
- **No invented numbers.** If a number isn't computable from data, mark "N/A — [reason]" and propose how to fix.
- **Branded export.** Final output should be ready to paste into the agency's PDF template (logo, colors). Default to clean markdown if no template is configured.
- **Next-month plan must be concrete.** Each item has a date, a number, and an owner.
- **Length cap.** Each section fits one page in the PDF. If it doesn't, cut.
