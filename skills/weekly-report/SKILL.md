---
name: weekly-report
description: Generates a one-page agency-grade weekly performance summary — headline numbers, what worked, what didn't, anomalies, and 3 specific actions for the coming week. Profit/CAC framing, not platform KPIs. Run every Monday morning.
---

# /weekly-report

## Why this skill exists

The most-cited time win from AI in PPC: weekly reporting cut from 3–4 hours to 30 minutes (Search Engine Land). This skill ships that win.

But: most "AI weekly reports" surface CTR / CPC / CPM. For B2B SaaS those are vanity. The report must lead with CAC, pipeline, SQL volume, and what changed in the funnel — not platform-side metrics.

## Preconditions

- `CLAUDE.md` exists with §2 (Targets) and §3 (Conversion hierarchy) populated.
- Two CSVs (or live MCP queries):
  - `data/this-week-YYYY-MM-DD.csv` — campaign-level metrics for the most recent complete Mon-Sun
  - `data/last-week-YYYY-MM-DD.csv` — same for the prior Mon-Sun
- Optional: outputs from other recent skills (audit, search-term, close-variant) in `reports/`.

If the user invokes without arguments, prompt for which week to report on, then pull the data.

## What to do

### Step 1 — Compute headline metrics

For this week and last week, compute:

| Metric | Source |
|---|---|
| Spend | sum cost |
| Conversions (primary) | sum conv on primary actions only |
| Conv value | sum conv_value on primary actions |
| CAC | spend / Closed-Won count (or whatever primary represents) |
| ROAS | conv_value / spend |
| Pipeline contribution | conv_value × stage→Closed-Won close rate from CLAUDE.md §2 |
| SQL count | sum conv on SQL action |
| Demo / form submission count | sum conv on lead-form action |
| CTR | clicks / impr |
| Impressions | sum |
| Search Impression Share | average weighted by impressions |

Compute deltas: absolute and percentage. Flag any delta > 20%.

### Step 2 — Identify what worked

- Top 3 campaigns by ROAS this week (with absolute conv_value and CAC)
- Top 3 ad groups by conversion-rate lift week-over-week
- Best performing creative format (RSA / Asset Group / etc.)
- Any campaign that hit its target CAC for the first time in the last 90 days — call out specially

### Step 3 — Identify what didn't

- Top 3 campaigns by wasted spend (cost / 0 conv or cost / CAC > 2× target)
- Any campaign with > $X spend and < 0.5% CTR (X = 1/4 of target weekly spend per campaign)
- New keywords / search terms in the last 7 days with cost ≥ 0.5× target CAC and 0 conv (link to `/search-term-audit` output if present)
- Any conversion action whose volume dropped > 30% week-over-week — possible tracking break

### Step 4 — Anomalies

- Spike or drop in impressions / clicks / conv > 2 std-dev of the trailing 8-week baseline
- New competitor in Auction Insights (if AI data was uploaded this week)
- New top search query that didn't appear in the prior 30 days
- "Performance cliff" detection: campaign just exited learning phase and conv-rate dropped > 20% — flag explicitly (this is the Joe Martinez pattern)

### Step 5 — Recommended actions for the coming week

Pick exactly 3. Each must:
- Be specific (which campaign, what change, what magnitude)
- Have a $-impact estimate
- Have a confidence (high/medium/low) and one-sentence rationale
- Be drafted as an entry for the Action Queue when the web app lands

## Output

Write to `reports/weekly-YYYY-WW.md` AND email-friendly HTML to `reports/weekly-YYYY-WW.html`.

```markdown
# Weekly Performance — [CLIENT NAME] — Week of [Mon DATE]

## Headline

| Metric | This week | Last week | Δ | Δ% | Status |
|---|---|---|---|---|---|
| Spend | $[X] | $[X] | $[X] | [%] | [✓ on pace / ⚠ over / ⚠ under] |
| Closed-Won (primary) | [N] | [N] | [N] | [%] | |
| CAC | $[X] | $[X] | $[X] | [%] | [vs target $[CAC]] |
| ROAS | [X] | [X] | [X] | [%] | [vs target] |
| SQL count | [N] | [N] | [N] | [%] | |
| Demo requests | [N] | [N] | [N] | [%] | |
| CTR | [%] | [%] | [pp] | [%] | |
| Search Impression Share | [%] | [%] | [pp] | [%] | |

## What worked

- [Campaign A] hit $[X] CAC vs target $[X] — [N] Closed-Won at [X]× target ROAS. Drivers: [evidence].
- [Ad group B] conversion rate +[X]pp WoW after the [date] negative-keyword push. Now at [X]%.
- [Creative C] is the top RSA — Ad Strength Excellent, [X]% CTR, [N] conversions.

## What didn't

- [Campaign D]: $[X] spent, [N] conv, CAC $[X] ([X]× target). Drivers: [evidence]. Suggest [action].
- [Term E] consumed $[X] with 0 conv this week. Source: [keyword / close variant]. Suggest add as ad-group negative.
- Conversion volume for "[action]" dropped [X]% — investigate tracking before next bid strategy change.

## Anomalies

- [...]

## 3 actions for next week

1. **[Action]** — Campaign [X]. Change [old] → [new]. Expected impact: $[Y] / [N] more SQL / [%] CAC reduction. Confidence: [H/M/L]. Why: [one sentence].
2.
3.

## Things to watch

- [Items not yet actionable but worth keeping eyes on]

---

*Generated [DATETIME]. Data window: [this week start] — [this week end]. Next report: [next Monday].*
```

## Rules

- **One page.** Executives read this. If it's longer than one page, cut.
- **Profit / CAC first.** Platform KPIs (CPC, CTR, CPM) go in supporting rows, not the headline.
- **Show source data** for every claim. No "your campaigns improved" without numbers.
- **Never make up data.** If a metric isn't available (e.g. SQL count because OCI isn't wired), say "not available — set up OCI" and move on.
- **3 actions, exactly.** Not 5, not 7. Force prioritization.
- **No emojis** unless the brand voice in CLAUDE.md §7 allows them.
- **Time-stamped.** Include the data window and report generation time so the agency knows freshness.
