---
name: negative-keyword-builder
description: Builds the standard B2B SaaS negative keyword library (jobs, education, free/open-source, login/support, salary, comparison off-targets) and merges with client-specific exclusions from CLAUDE.md. Outputs a bulk-upload-ready CSV plus per-campaign overlay recommendations. Run at onboarding and quarterly.
---

# /negative-keyword-builder

## Why this skill exists

The same 5–7 categories of negatives recur across every B2B SaaS Google Ads account. Vehnta's analysis: healthy B2B accounts have 200–500 negatives. New accounts typically have <30. Rebuilding from scratch per client is wasted effort.

This skill ships a reusable library, then overlays client-specific exclusions.

## Preconditions

- `CLAUDE.md` exists with §1 (Product, ICP) and §6 (Negative keyword baseline).
- Optional: existing negative keyword lists from Google Ads (Tools → Shared Library → Negative keyword lists) exported to `data/existing-negatives-*.csv`.

## What to do

### Step 1 — Read client context

From CLAUDE.md extract:
- Product category and adjacent terms (for "free / OSS" negatives)
- ICP industry (for off-target verticals)
- Geo (for off-target country/language negatives, if applicable)
- Competitor names (for competitor-employee negatives)
- Brand and product terms that must NEVER be added as negatives (allowed phrases)

### Step 2 — Compose from the starter library

The base library below ships as defaults. For each category, decide:
- **Apply at account level** (broad applicability) — uses Shared Negative Keyword List
- **Apply at campaign level** (some campaigns intentionally target the term, e.g. a "competitor" campaign should NOT have competitor names as negatives)
- **Skip** (incompatible with CLAUDE.md allowed phrases)

#### Standard B2B SaaS negative library

**Jobs / careers** (account-level):
```
job, jobs, career, careers, hiring, recruiter, resume, cv, employment, salary, salaries, "how much does", "pay scale", "wage", "vacancy", "vacancies", glassdoor, indeed, linkedin jobs, internship
```

**Education / informational intent** (account-level — but be careful, some informational queries are commercial-intent precursors):
```
"what is", "how to", "tutorial", "course", "training", "certification", "exam", "study", "learn", "definition", "meaning", "wikipedia", "pdf", "ebook", "ppt", "slides", "examples", "template"
```
Caution: "[category] tutorial" might be a top-of-funnel signal worth keeping in some accounts. Audit before adding. Recommend: add as **campaign-level negative** on bottom-of-funnel campaigns only.

**Free / open-source / DIY**:
```
free, "open source", "open-source", oss, gratis, "no cost", "0 dollar", diy, "build your own", github, "free trial download", crack, torrent, "free version"
```
Caution: many SaaS offer a free trial — do NOT add "free trial" as a negative; in fact add it as a positive keyword.

**Login / support / for-existing-customers**:
```
login, "log in", signin, "sign in", "log on", account, dashboard, support, help, "customer support", "contact us", "technical support", documentation, docs, faq, "user guide", "knowledge base", "release notes", changelog, "status page"
```

**Comparison toward off-targets** (campaign-level — careful):
```
"vs [off-target competitor]", "[off-target] alternative", "review [off-target]"
```
Always pair with positive: keep the "vs" terms where YOU are the alternative being searched.

**Cheap / discount** (B2B SaaS rarely competes on price):
```
cheap, cheapest, "lowest price", discount, coupon, "promo code", "[brand] coupon", clearance, bargain
```

**Industries / verticals OFF-target** (per CLAUDE.md ICP):
```
[derive from ICP exclusions, e.g. if ICP is enterprise, add "small business", "startup", "personal use"]
```

**Competitor employees / branded-only queries**:
```
"[competitor 1] login", "[competitor 1] careers", "[competitor 1] support", "[competitor 1] pricing page", ...
```
Repeat per competitor named in CLAUDE.md.

**Geo off-target** (if account is geo-targeted but search terms suggest off-target locations):
```
[derive from CLAUDE.md geo settings]
```

### Step 3 — Check against existing negatives

If `data/existing-negatives-*.csv` is provided:
- Compute the diff: what's NEW from the starter library that isn't already on file
- Flag duplicates so we don't add them again
- Flag conflicts: any existing negative that contradicts CLAUDE.md allowed phrases

### Step 4 — Match-type guidance

- Default to **phrase match** for category negatives (jobs, education, free).
- Use **exact match** when the negative is a single-token term you only want to block in that exact form.
- Use **broad-match negative** ONLY for tokens that should never appear (e.g. "porn", "adult") — but Google's broad-match-negative behavior is conservative; phrase or exact usually suffice.

### Step 5 — Output

Write to `reports/negative-keyword-library-YYYY-MM-DD.md`:

```markdown
# Negative Keyword Library — [CLIENT NAME]

## Summary
- New negatives recommended: [N]
- Already on file: [N]
- Conflicts with CLAUDE.md allowed phrases (skipped): [N]
- Scope breakdown: [N] account-level / [N] campaign-level / [N] ad-group-level

## Recommended new negatives — Account level

[grouped by category, in bulk-upload-ready table]

| Negative | Match type | Category | Why |
|---|---|---|---|
| job | phrase | Jobs | Block job-search queries from triggering ads |
| ... |

## Recommended new negatives — Campaign level

(Specify which campaign each applies to)

| Campaign | Negative | Match type | Category | Why |
|---|---|---|---|---|
| Non-brand Product | tutorial | phrase | Education | Block informational queries; allow on Brand campaign |
| ... |

## Conflicts to resolve manually

[any term that COULD be a negative but contradicts an allowed phrase from CLAUDE.md §6]

## Bulk-upload CSV

Write `data/negatives-upload-YYYY-MM-DD.csv` in Google Ads Editor's import format:
`Action, Campaign, Ad group, Keyword, Match type`
With Action = `Add`.

## Update CLAUDE.md

If new client-specific exclusions emerged from data (off-target verticals, competitor names), draft an update to CLAUDE.md §6 with the additions.
```

## Rules

- Never recommend a negative that contradicts CLAUDE.md §6 allowed phrases. Skip and explain.
- Always default to phrase match for category negatives unless the term is genuinely single-token / single-meaning.
- For the comparison and competitor-vertical categories, recommend campaign-level (not account-level) because dedicated competitor campaigns INTENTIONALLY target those terms.
- Show the rationale per negative — agency staff will skim hundreds; rationale matters.
- Don't recommend more than 100 in a single draft. If more are warranted, split by category and submit progressive batches.
