---
name: account-audit
description: Run a weighted A-F audit across an entire Google Ads account, covering tracking, structure, bidding, keywords, ads, audiences, and Google's destructive defaults. Output ranked fixes and a draft action list. Use at onboarding, then quarterly.
---

# /account-audit

## Preconditions

Refuse to run unless ALL are true. State which is missing and stop.

1. `CLAUDE.md` exists in the current directory and has these fields filled: ICP, ACV, sales cycle days, target CAC, conversion hierarchy with at least one primary action, account CID.
2. `data/` contains either: (a) a CSV export from Google Ads "Account → Insights & Reports → Reports" covering last 30 days for campaigns, ad groups, keywords, search terms; OR (b) credentials for the `cohnen/mcp-google-ads` MCP server are configured.
3. If neither exists, tell the user exactly which exports to run from Google Ads UI and stop.

## What to do

Run every check below in order. For each, record: `passed (bool)`, `severity (critical/high/medium/low)`, `weight (numeric, see table)`, `evidence (concrete data)`, `fix (1-2 sentences)`, `draft_action (optional, in the format below)`.

### Category weights (when computing the overall score)

| Category | Weight |
|---|---|
| Tracking & Measurement | 0.25 |
| Account Structure | 0.20 |
| Bidding & Budget | 0.15 |
| Keywords & Search Terms | 0.15 |
| Ads & Assets | 0.10 |
| Audience & Targeting | 0.10 |
| Settings & Defaults | 0.05 |

Severity multipliers: Critical 5.0 · High 3.0 · Medium 1.5 · Low 0.5.

Per-check score contribution: `0` if failed, `weight × severity_multiplier` if passed. Normalize to 0–100. Grade: A ≥90, B 80–89, C 70–79, D 60–69, F <60.

### Tracking & Measurement checks (CRITICAL — these are the spine)

- [ ] **T1** Primary conversion action exists. Severity: Critical.
- [ ] **T2** Primary conversion action click-through window is **90 days** (B2B default). Sales cycle from CLAUDE.md ≤ window. Severity: Critical.
- [ ] **T3** Primary conversion action is a later-funnel event (SQL or below in the hierarchy), not "Page View" / "Session Start" / "Form Submit" alone. Severity: Critical.
- [ ] **T4** Enhanced Conversions for Leads (EC4L) is enabled at the customer level. Severity: High.
- [ ] **T5** GCLID is being received and stored — verify by querying the CRM mapping defined in CLAUDE.md §10. Severity: High.
- [ ] **T6** OCI uploads have run in the last 7 days successfully. Severity: High.
- [ ] **T7** Conversion actions have values populated (required for Target ROAS / Max Conv Value). Severity: High.
- [ ] **T8** No duplicate / overlapping conversion actions (e.g. both GA4 import and a native conversion firing on the same event). Severity: Medium.
- [ ] **T9** Conversion delay is within healthy range (median time-to-conversion is reasonable for sales cycle). Severity: Medium.
- [ ] **T10** Attribution model is Data-Driven (or Position-Based if volume too low). Severity: Medium.

### Account Structure checks

- [ ] **S1** Required campaign archetypes from CLAUDE.md §4 are present (Brand / Competitor / Non-brand product / Non-brand problem / Remarketing). Severity: High.
- [ ] **S2** Brand campaign exists and is separated from non-brand (so Smart Bidding doesn't confuse them). Severity: High.
- [ ] **S3** No single ad group has > 20 keywords (themed ad groups, not SKAG soup). Severity: Medium.
- [ ] **S4** No keyword duplication across ad groups (Google's "duplicates" tool or own diff). Severity: Medium.
- [ ] **S5** Match-type spread within each ad group is healthy (not 100% broad without OCI). Severity: High.

### Bidding & Budget checks

- [ ] **B1** Bid strategy fits conversion volume: Smart Bidding only if ≥ 30 conv / 30 days at campaign level. Severity: High.
- [ ] **B2** Maximize Conversions has a Target CPA cap. Severity: High.
- [ ] **B3** Maximize Conversion Value has a Target ROAS. Severity: High.
- [ ] **B4** Budget pacing on track: MTD spend within ±10% of monthly target. Severity: Medium.
- [ ] **B5** No campaign limited by budget that has good ROAS (= flag as scale opportunity). Severity: Medium.
- [ ] **B6** No campaign with `cost > 30%` of total spend and below-target CAC. Severity: High.

### Keywords & Search Terms checks

- [ ] **K1** Negative keyword count at account level ≥ 100 (B2B SaaS healthy floor — vehnta.com). Severity: Medium.
- [ ] **K2** Standard B2B negatives present: jobs/careers, education, free/OSS, login/support, salary, "what is". Severity: Medium.
- [ ] **K3** Broad match used only where OCI is flowing + Target CPA is set. Severity: High.
- [ ] **K4** Last-30d search-term report shows < 25% spend on terms with 0 conversions. Severity: High.
- [ ] **K5** No single search term consumes > 5% of campaign spend with 0 conversions. Severity: High.

### Ads & Assets checks

- [ ] **A1** Every ad group has ≥ 2 RSAs. Severity: Medium.
- [ ] **A2** No RSA with Ad Strength "Poor". Severity: Medium.
- [ ] **A3** Sitelinks: ≥ 6 active at account or campaign level. Severity: Low.
- [ ] **A4** Callouts: ≥ 4. Severity: Low.
- [ ] **A5** Structured snippets: ≥ 1 set. Severity: Low.
- [ ] **A6** Image extensions used for B2B SaaS (if eligible). Severity: Low.
- [ ] **A7** No ads with banned phrases from CLAUDE.md brand voice. Severity: Medium.

### Audience & Targeting checks

- [ ] **AU1** Geo targets aligned with ICP (no off-target countries inflating impressions). Severity: High.
- [ ] **AU2** Language targets aligned (don't target "all languages" by default). Severity: Medium.
- [ ] **AU3** Audience signals applied as Observation (not Targeting) on all non-Remarketing campaigns. Severity: Medium.
- [ ] **AU4** Device bid modifiers applied based on device-level performance. Severity: Low.

### Settings & Defaults checks (the 7 destructive defaults — GrowthSpree)

- [ ] **D1** Auto-applied recommendations: **all OFF**. Severity: Critical.
- [ ] **D2** "Include Google Display Network" on Search campaigns: **OFF**. Severity: Critical.
- [ ] **D3** Search partners: **OFF** unless data justifies. Severity: High.
- [ ] **D4** Auto-applied ad variants: **OFF**. Severity: High.
- [ ] **D5** Final URL Expansion (PMax): **OFF** unless tested. Severity: High.
- [ ] **D6** Conversion window matches sales cycle (≥ sales_cycle_days). Severity: Critical (duplicate of T2 — keep both).
- [ ] **D7** Optimization score auto-apply: **OFF**. Severity: Critical.

## Output format

Write to `reports/audit-YYYY-MM-DD.md` AND print to stdout.

```markdown
# Account Audit — [CLIENT NAME] — [DATE]

**Overall Score**: [NN]/100 — Grade [A/B/C/D/F]

| Category | Score | Grade |
|---|---|---|
| Tracking & Measurement | [NN/100] | [A-F] |
| Account Structure | [NN/100] | [A-F] |
| Bidding & Budget | [NN/100] | [A-F] |
| Keywords & Search Terms | [NN/100] | [A-F] |
| Ads & Assets | [NN/100] | [A-F] |
| Audience & Targeting | [NN/100] | [A-F] |
| Settings & Defaults | [NN/100] | [A-F] |

## Top 5 fixes (ranked by impact × ease)

1. **[CHECK_ID]** [Title]. Evidence: [...]. Fix: [...]. Expected impact: [...].
2. ...

## All findings

[group by category, sorted by severity desc, severity icon prefix:]
- 🔴 Critical
- 🟠 High
- 🟡 Medium
- ⚪ Low

[for each check that failed, show: ID, title, evidence, fix, draft action if any]

## Draft action list

Also write `data/draft-actions-YYYY-MM-DD.csv` with columns:
`action_id, type, target_resource, current_value, proposed_value, reasoning, risk_tier, expected_impact`

## Required exports (if any data was missing)

[explicit list of CSVs the user should pull from Google Ads UI to deepen the next audit run]
```

## Rules

- Never invent data. If a check can't be evaluated from available data, mark it `not_evaluated` and list it in "Required exports".
- Quote real values from the CSVs / API responses. No placeholders.
- If the account is below 30 conv/30 days at campaign level, the audit must recommend pausing Smart Bidding in favor of Maximize Clicks + Exact Match per Dirk Roettges's guidance (in CLAUDE.md §5).
- Draft actions for L3 risk tier (campaign pause, structure change) must be tagged accordingly so the agency knows they're high-risk.
- Always end with: "Run `/conversion-tracking-health` next to deep-dive tracking, or `/search-term-audit` to deep-dive keywords."
