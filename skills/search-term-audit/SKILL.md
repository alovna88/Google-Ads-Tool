---
name: search-term-audit
description: N-gram analysis of the last 30 days of search terms with profit math, ranked negative-keyword recommendations, and draft bulk-upload CSV. Borrows the Brainlabs search-query-mining pattern and AdPulse's profit framing. Run weekly.
---

# /search-term-audit

## Why this skill exists

GrowthSpree's analysis of 150+ B2B SaaS accounts: ~57% of every $1 in B2B SaaS PPC goes to non-converting queries. The single highest-leverage weekly motion is the search-term audit. Brainlabs's n-gram script is the canonical open-source pattern; AdPulse adds the critical "profit math" lens that prevents false-positive negatives.

The trap: an n-gram analysis that looks at cost-with-zero-conv in isolation will produce false positives. Optmyzr warns about cases where "$8,000 of that spend resulted in $14,500 in profit" — a high-spend n-gram can still be profitable if you look at the right window. So profit-framing is mandatory, not optional.

## Preconditions

- `CLAUDE.md` exists with: ACV, conversion hierarchy (so we can compute profit per conversion), target CAC.
- One of:
  - Search Terms CSV export from Google Ads UI: Reports → Predefined Reports → Search Terms → last 30 days, all campaigns. Save as `data/search-terms-YYYY-MM-DD.csv`.
  - Live data via `cohnen/mcp-google-ads`.

## What to do

### Step 1 — Load and normalize

- Read the search-terms CSV (or run the GAQL: `SELECT search_term_view.search_term, metrics.cost_micros, metrics.clicks, metrics.impressions, metrics.conversions, metrics.conversions_value, ad_group.id, ad_group.name, campaign.id, campaign.name FROM search_term_view WHERE segments.date DURING LAST_30_DAYS`).
- Lowercase, trim, strip punctuation. Keep the original for the output.
- Map cost_micros → cost (currency).

### Step 2 — Build n-grams

- For each search term, generate 1-grams, 2-grams, 3-grams.
- Aggregate by n-gram across all terms: total cost, total clicks, total conversions, total conv_value, term count.
- Compute per-n-gram: cost-per-conv (or ∞ if 0 conv), avg cost-per-click, conv-rate.

### Step 3 — Compute profit per n-gram

Profit per n-gram = `conversions_value × close_rate(stage_to_closed_won) − cost`.

Use the conversion hierarchy from CLAUDE.md §3:
- If conversions_value already reflects Closed-Won values (because OCI is set up), use as-is.
- If it only reflects upstream stages (Lead/MQL/SQL), apply assumed conversion rates from CLAUDE.md §2 (target CAC implies a close rate).

If profit data is unreliable (no OCI, no values set), fall back to cost-vs-conversions and clearly state this is a degraded mode.

### Step 4 — Rank for negative candidacy

An n-gram is a **strong negative candidate** if ALL of the following:
- Total cost over last 30 days ≥ 1× target CAC
- Zero conversions, OR conversions but negative profit
- The n-gram appears in ≥ 3 distinct search terms (otherwise add the specific term as a negative, not the n-gram)
- The n-gram is NOT a substring of any keyword the client is already bidding on (avoid blocking your own ad groups)
- The n-gram does NOT appear in CLAUDE.md "required brand terms" or any allowed-phrases whitelist

An n-gram is a **soft negative candidate** if:
- Cost ≥ 0.5× target CAC and 0 conv, OR
- Conv-rate < 25% of account average for n-grams that fired

A specific **search term** (not n-gram) is a strong candidate if:
- Cost ≥ 0.5× target CAC and 0 conv and not a close variant of any existing keyword

### Step 5 — Close-variant overlap call-out

Cross-reference with `/close-variant-checker` output if present (`data/close-variants-*.json`). If a strong negative candidate is also a close variant of an existing keyword, flag specially: this is the "double-tap" pattern — Google is showing your ad for a close variant that should have been blocked.

### Step 6 — Output

Write to `reports/search-term-audit-YYYY-MM-DD.md`:

```markdown
# Search Term Audit — [CLIENT NAME] — last 30 days ending [DATE]

## Headline

- Total search terms reviewed: [N]
- Total spend reviewed: $[X]
- Spend on terms with 0 conversions: $[Y] ([Y/X %])
- Spend with negative profit (using OCI values): $[Z]
- Negative-keyword candidates surfaced: [count by tier]

## Top 10 wasted-spend n-grams

| Rank | N-gram | Cost | Conv | Profit | Action |
|---|---|---|---|---|---|
| 1 | "free" | $3,420 | 0 | -$3,420 | Add account-level negative (exact) |
| 2 | "what is [category]" | $1,890 | 2 (MQL only) | -$1,790 | Add ad-group negative (phrase) |
| ... |

## Top 10 wasted-spend specific terms

| Rank | Search term | Triggering keyword | Match type | Cost | Conv | Action |
|---|---|---|---|---|---|---|

## Profit gold: high-converting n-grams to *promote* as keywords

| N-gram | Cost | Conv | Profit | Suggested action |
|---|---|---|---|---|
| "[category] for [vertical]" | $480 | 7 SQL | $+2,520 | Add as exact keyword to [ad group] |

## Anomalies

- New terms with unusually high spend velocity (week-over-week)
- Terms that crossed the close-variant boundary (didn't match exactly to a keyword)

## Draft action list

Write `data/draft-actions-search-terms-YYYY-MM-DD.csv` with:
- Negative keywords to add: scope (account/campaign/ad group), match type, term, source n-gram or term, expected monthly savings
- Keywords to promote: ad group target, match type, term, expected monthly contribution
- Bulk-upload-ready: use Google Ads Editor's CSV format

## Top 3 actions this week
1.
2.
3.
```

## Rules

- **Profit math, not cost math.** Always compute and show profit when OCI is available. If not available, label the report "Degraded mode — install OCI for accurate profit framing."
- **Never auto-apply.** This skill produces drafts. The agency reviews before any negative is added.
- **Show the source data.** For every recommended negative, link back to ≥ 3 example search terms that contained the n-gram.
- **Respect brand and allowed phrases.** Read CLAUDE.md §6 and never recommend negatives that overlap with client-required terms.
- **Top 3 actions** must each have estimated monthly $ impact.
