---
name: close-variant-checker
description: Identifies search terms that triggered ads as Google "close variants" of exact-match keywords (singulars/plurals, misspellings, similar-intent), computes the share of impressions/clicks/cost served via close variants per keyword, and drafts targeted negatives — with an allowed-phrases whitelist so legitimate variants aren't blocked. Mirrors the AdPulse Close Variant Checker pattern. Run monthly.
---

# /close-variant-checker

## Why this skill exists

Google does not expose an `is_close_variant` boolean in the API. Match-type negatives don't block close variants ("shoes" as a negative doesn't block "sheos"). So an exact-match keyword can quietly receive a large share of its traffic from close variants that drift far from intent. AdPulse's industry estimate: ~20% of budget waste lives here.

We reconstruct close-variant detection by comparing search-term text to triggering-keyword text + match types.

## Preconditions

- `CLAUDE.md` exists with §6 (negative baseline) and any allowed-phrases overrides.
- Search Terms CSV from Google Ads UI with columns: `Search term, Keyword, Keyword match type, Match type (search term match type), Impressions, Clicks, Cost, Conversions, Ad group`.
  - Save as `data/search-terms-YYYY-MM-DD.csv`.
- Or live via `cohnen/mcp-google-ads`:
  - `SELECT search_term_view.search_term, search_term_view.status, segments.search_term_match_type, ad_group_criterion.keyword.text, ad_group_criterion.keyword.match_type, ad_group.id, ad_group.name, metrics.impressions, metrics.clicks, metrics.cost_micros, metrics.conversions, metrics.conversions_value FROM search_term_view WHERE ad_group_criterion.keyword.match_type = 'EXACT' AND segments.date DURING LAST_30_DAYS`

## What to do

### Step 1 — Filter to exact-match keywords only

Close variants are most damaging on Exact-match keywords (because the agency thinks they're getting exact match). Phrase/broad already accept variation.

Keep only rows where triggering keyword match type = `EXACT`.

### Step 2 — Decide if each search term is a "true match" or a "close variant"

A search term is a **true match** to its exact keyword when:
- Identical after lowercasing, trimming, removing punctuation.

A search term is a **close variant** when any of:
- Singular/plural difference (e.g. "dentist" vs "dentists")
- Misspelling (Levenshtein distance ≤ 2 on the longest token, or ≤ 1 on short tokens)
- Function-word difference ("the", "a", "for", "to", "of" added/removed)
- Reordering (same tokens, different order)
- Stemming difference (e.g. "manage" vs "managing")
- Synonym substitution (the hardest — Google does this aggressively; detect via tokens that are not in the keyword but in a synonym list; for B2B SaaS, watch for "software / tool / platform / app / SaaS / system / solution" interchanging)
- "Similar-intent" rephrase that contains at least 60% of the keyword's content tokens

If you can't classify confidently, mark as **uncertain** and surface for human review.

### Step 3 — Per-keyword aggregates

For each exact-match keyword, compute:
- `impressions_total`, `clicks_total`, `cost_total`, `conv_total`, `conv_value_total`
- `impressions_close_variant`, `clicks_close_variant`, `cost_close_variant`, `conv_close_variant`, `conv_value_close_variant`
- Close-variant share of: impressions, clicks, cost
- CPA close variant vs CPA true match
- Conv-value / cost close variant vs true match

### Step 4 — Decision tree per close-variant cluster

For each close-variant **search-term cluster** (terms that resolved to the same exact keyword):

- If close-variant CPA ≤ true-match CPA × 1.2 (within 20%) → **leave alone** or promote variant as a new exact keyword.
- If close-variant CPA between 1.2× and 2× true-match CPA → soft negative candidate; warn but don't auto-recommend.
- If close-variant CPA > 2× true-match CPA OR close-variant has 0 conv AND cost ≥ 1× target CAC → recommend negative (exact match, scoped to ad group).
- If the close variant contains an allowed-phrase token from CLAUDE.md §6 (e.g. "denture" allowed in "dentist" ad group) → do NOT recommend negative.

### Step 5 — Single-word negatives in exact-only ad groups

If an ad group has only exact-match keywords AND a single-word token consistently triggers irrelevant close-variant matches (e.g. ad group target is "[crm software]" but "free" keeps appearing) — recommend adding "free" as a phrase-match negative at ad-group level.

## Output

Write to `reports/close-variants-YYYY-MM-DD.md`:

```markdown
# Close Variant Checker — [CLIENT NAME] — last 30 days

## Headline

- Exact-match keywords analyzed: [N]
- Average close-variant share of impressions: [%]
- Average close-variant share of cost: [%]
- Keywords with > 50% close-variant cost share: [count] (flagged)
- Estimated waste from close variants (CPA > 2× true match): $[X]

## Per-campaign / per-ad-group rollup

| Campaign | Ad group | Keyword | CV impr % | CV cost % | CV CPA | True CPA | Action |
|---|---|---|---|---|---|---|---|
| ... |

## High-impact draft negatives

| Rank | Term | Match type | Scope (ad group) | Source close-variant of | Cost | 0-conv? | Expected monthly savings |
|---|---|---|---|---|---|---|---|

## Close-variant winners worth promoting

(Where conv-value/cost on close variants > true match — add the variant as its own exact keyword)

| Variant | Triggered for | Cost | Conv | Profit | Suggested keyword to add |
|---|---|---|---|---|---|

## Uncertain — human review

| Search term | Triggered keyword | Why uncertain |

## Draft action list

Write `data/draft-actions-close-variants-YYYY-MM-DD.csv` (same schema as `/account-audit`).

## Allowed-phrases whitelist suggestions

Based on what we kept: if any close variant we did NOT block is showing up frequently, propose adding it to CLAUDE.md §6 as an allowed phrase to silence future false alarms.

## Top 3 actions
1.
2.
3.
```

## Rules

- Never auto-apply. Always draft.
- Always surface "Winners worth promoting" — close variants outperforming true match is the most-missed opportunity in this audit.
- Respect CLAUDE.md allowed phrases.
- If `data/close-variants-YYYY-MM-DD.json` (machine-readable) is also useful for downstream skills, write it.
- Show the formula used for any "estimated waste" number.
