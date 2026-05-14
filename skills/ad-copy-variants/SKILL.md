---
name: ad-copy-variants
description: Generates Responsive Search Ads (RSA) headline and description variants from the client's Voice-of-Customer brief and brand voice, with guardrails (character limits, banned phrases, required tone). Optionally outputs Google Ads Editor-compatible bulk-upload CSV. Run weekly for creative refresh.
---

# /ad-copy-variants

## Why this skill exists

The hard part is not generating ad copy — Claude can produce 100 headlines in seconds. The hard part is brand-voice fidelity, character limit discipline, no off-brand phrasing, and producing variants that *actually test different angles* (not the same idea rephrased).

This skill enforces those guardrails.

## Preconditions

- `CLAUDE.md` exists with §1, §7 (brand voice), and ideally §11 / ICP research output at `reports/icp-research-*.md`.
- If `reports/icp-research-*.md` is missing, the skill will run with a degraded mode label.
- User specifies in the invocation: target ad group + the angle to test (or the skill will infer from the latest ICP research).

## Inputs to gather

If invoked without arguments, ask the user:
1. Which campaign + ad group is this for?
2. What is the keyword theme of this ad group? (so we don't write copy unrelated to the keywords)
3. What angle to lead with? Default: take the #1 ranked angle from the latest `/icp-research` output.
4. How many headlines / descriptions? Default: 15 headlines + 4 descriptions (the RSA asset count + diversity buffer).
5. Landing page URL — to make sure ad scent will match (`/landing-page-copy` is a separate skill; for now, just confirm consistency).

## What to do

### Step 1 — Read context

- CLAUDE.md §7: tone, banned phrases, required terms, banned topics
- Latest `reports/icp-research-*.md`: VoC paragraph, hook angles, verbatim phrases
- If neither exists: stop and ask the user to populate them first

### Step 2 — Plan the variant grid

For an RSA asset set, produce variants across 5 angles. Even if leading with one, generate diversity for asset-combination testing:

| Angle | What it does | Example seed |
|---|---|---|
| Problem-led | Names the painful symptom | "Spreadsheets breaking at 50 employees?" |
| Outcome-led | Names the desired end-state | "Forecast revenue your CFO trusts" |
| Comparison | Positions against status quo or named competitor | "Switch from [legacy] in 30 minutes" |
| Social-proof | Numbers, customer names, results | "Used by 1,200 mid-market SaaS teams" |
| Differentiator | The one technical or commercial wedge | "Native Slack integration, 2-min setup" |

### Step 3 — Generate headlines

For each angle, generate 3 headlines (15 total). Each headline must:
- Be **≤ 30 characters** (Google Ads hard limit)
- Use the client's brand-voice tone from §7
- Avoid every banned phrase from §7
- Where required, contain the required term/differentiator from §7
- Match the keyword theme of the target ad group (so it scents the search query)
- Not duplicate another headline in spirit (real variation, not paraphrase)

### Step 4 — Generate descriptions

4 descriptions, each ≤ 90 characters. Pair with angles to ensure each description supports multiple headlines (RSA combination logic).

### Step 5 — Self-check pass

After generating, run a validation pass:
- Character count per asset (kill any over limit)
- Banned phrase scan (kill any match)
- Required-term scan (flag missing where required)
- Duplication check (flag any pair with >0.8 cosine similarity in spirit)
- Brand-voice scan: re-read each through the §7 tone lens — would a strict brand reviewer flag this?

Show the validation table; mark which assets pass/fail.

### Step 6 — Optional ad-strength estimate

Estimate Ad Strength (Google's metric: Poor / Average / Good / Excellent) based on:
- Number of unique headlines (15 = good)
- Headline variation (different angles = good)
- Keyword inclusion in headlines (matters for relevance)
- Pinning recommendations (don't pin everything — leaves no room for combinations)

### Step 7 — Output

Write to `reports/ad-copy-variants-YYYY-MM-DD.md`:

```markdown
# Ad Copy Variants — [CLIENT NAME] — [DATE]

## Target

- Campaign: [...]
- Ad group: [...] (keyword theme: [...])
- Lead angle: [...]
- Landing page: [URL]

## Headlines (15) — character-counted

| # | Angle | Headline | Chars | Status |
|---|---|---|---|---|
| 1 | Problem | Spreadsheets breaking at 50? | 27 | ✓ |
| ... |

## Descriptions (4)

| # | Description | Chars | Status |
|---|---|---|---|

## Pinning recommendation

| Position | Pin asset(s) | Why |
|---|---|---|
| H1 | None | Allow Google to test |
| H2 | None | Allow Google to test |
| H3 | [Branded headline] | Ensure brand always appears |
| D1 | None | |
| D2 | [Differentiator description] | Always show the wedge |

## Validation report

[table showing each asset's pass/fail across: char count, banned phrases, required terms, duplication]

## Bulk-upload CSV

Write `data/rsa-upload-YYYY-MM-DD.csv` in Google Ads Editor's format:
`Action, Campaign, Ad group, Ad type, Headline 1, Headline 2, ... Headline 15, Description 1, ... Description 4, Final URL, Path 1, Path 2`

## Top 3 actions

1.
2.
3.
```

## Rules

- **Hard limits**: 30 chars headline, 90 chars description. Anything over is a failure, not a warning.
- **Brand voice is non-negotiable.** A headline that violates §7 banned phrases is killed even if it's brilliant.
- **Real variation.** Three variants on the same angle that differ by punctuation are not three variants.
- **Show your math on character counts** so the agency can spot-check.
- **Never invent customer quotes or statistics.** Numbers must come from VoC research or explicit user input.
- **Always end with one pin recommendation.** RSAs perform best with 0–1 pinned headlines and 0–1 pinned descriptions.
