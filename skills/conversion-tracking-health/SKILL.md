---
name: conversion-tracking-health
description: Deep-dive audit of the conversion tracking spine for a B2B SaaS Google Ads account. Verifies the 7 destructive Google defaults are turned off, Enhanced Conversions for Leads is firing, GCLID is being captured and stored on CRM records, conversion windows match the sales cycle, and OCI uploads are healthy. Run weekly, especially before any bid strategy change.
---

# /conversion-tracking-health

## Why this skill exists

Every B2B SaaS Google Ads source independently identifies tracking as the #1 failure point — Dreamdata, Directive, GrowthSpree, Vehnta, Involve, MRR Unlocked, Dirk Roettges. Smart Bidding cannot work without it. Broad match cannot work without it. "Optimize toward SQL/pipeline, not CPL" cannot work without it.

So this skill audits the spine before any other change is allowed.

## Preconditions

Stop and report if:
- `CLAUDE.md` is missing or §3 (Conversion hierarchy) is unfilled
- `CLAUDE.md` §10 (Tracking and CRM) is incomplete (CRM, GCLID field, lifecycle mapping)

## Inputs (any of these, in priority order)

1. Live data via `cohnen/mcp-google-ads` MCP — preferred
2. CSV exports from Google Ads UI:
   - "Tools → Measurement → Conversions" (export the conversions table)
   - "Tools → Measurement → Conversions → Diagnostics" (recent issues)
   - "Tools → Conversions → Enhanced conversions for leads" (status page screenshot or notes)
3. CRM export: a sample of 50 leads from the last 30 days with columns `created_at, gclid, lifecycle_stage, lifecycle_stage_changed_at`

## Checks to perform

### A. Conversion actions (the structure)

- [ ] **A1** Count of conversion actions categorized as "Primary" — should be ≥ 1 and ≤ 3. If 0, this is a blocker for everything else. If > 3, flag as risk of conflicting signals.
- [ ] **A2** Each primary action's **count setting** is "One" (B2B leads, not "Every"). "Every" is for ecommerce.
- [ ] **A3** Each primary action's **click-through window** ≥ `sales_cycle_days` from CLAUDE.md. **90 days minimum** in B2B.
- [ ] **A4** Each primary action's **view-through window** is 1–7 days only (longer view-through skews B2B attribution).
- [ ] **A5** Each primary action's **value** is set (required for Target ROAS / Max Conv Value).
- [ ] **A6** Conversion hierarchy from CLAUDE.md §3 is mirrored in Google Ads as actions (Lead = secondary, MQL = secondary, SQL = secondary or primary, Opp/Closed-Won = primary).
- [ ] **A7** No "Sessions" / "Page View" / "Scroll Depth" actions are marked Primary.

### B. Enhanced Conversions for Leads (EC4L)

- [ ] **B1** EC4L is enabled at the customer (account) level — Tools → Conversions → Settings.
- [ ] **B2** A conversion action has EC4L enabled (the per-action toggle).
- [ ] **B3** At least one website conversion is sending hashed PII (email, phone) — verify via Diagnostics or GTM container review.
- [ ] **B4** Match rate ≥ 50% over last 30 days (Google reports this in EC settings).
- [ ] **B5** Server-side or GTM implementation, not just Gtag — required for high match rates.

### C. GCLID capture (the join key)

- [ ] **C1** Landing pages have GCLID-capture script (or rely on auto-tagging which is the default — verify Auto-tagging = ON in account settings).
- [ ] **C2** Form submission flow stores GCLID on the lead record in CRM (verify in CRM field defined in CLAUDE.md §10).
- [ ] **C3** Sample 50 leads from last 30 days: what % have a GCLID? Healthy ≥ 60%. (Lower is normal because of direct/organic/dark traffic — but if < 30%, capture is broken.)
- [ ] **C4** GCLID format is valid (alphanumeric + underscores, no truncation, no URL-encoded artifacts).
- [ ] **C5** GCLID is preserved across multi-step funnels (e.g. survey → email → calendar booking).

### D. CRM lifecycle → OCI uploads

- [ ] **D1** OCI sheet (per CLAUDE.md §3) exists and is being updated.
- [ ] **D2** Last OCI upload was within the last 7 days (Google's recommended cadence).
- [ ] **D3** OCI upload success rate ≥ 90% (rejects often mean stale GCLIDs > 90 days old, or missing/wrong conversion action names).
- [ ] **D4** Conversion action names referenced in the sheet match Google Ads UI exactly (case-sensitive).
- [ ] **D5** Values are populated per row (not blank), in the account currency.

### E. The 7 destructive defaults (GrowthSpree)

- [ ] **E1** **Conversion window**: ≥ 90 days for primary actions (also checked in A3, repeat here for emphasis).
- [ ] **E2** **Auto-applied recommendations**: all categories OFF. Tools → Recommendations → Auto-apply page.
- [ ] **E3** **"Include Google Display Network"** flag on every Search campaign: OFF.
- [ ] **E4** **Broad match without OCI prerequisite**: identify any campaign with broad match active where OCI uploads in the last 30 days < 10 → flag as critical.
- [ ] **E5** **Maximize Conversions without a Target CPA cap**: flag any.
- [ ] **E6** **Search partners**: OFF unless proven uplift.
- [ ] **E7** **Auto-applied ad variants**: OFF.

### F. Attribution sanity

- [ ] **F1** Attribution model = Data-driven (or Position-based if conversion volume < 300/30d at the model level).
- [ ] **F2** No "Last Click" — Google removed first-click in 2023 but last-click still selectable and still wrong for B2B.

## Output

Write to `reports/tracking-health-YYYY-MM-DD.md` AND print stdout summary.

```markdown
# Conversion Tracking Health — [CLIENT NAME] — [DATE]

**Tracking Health Score**: [NN]/100

**Verdict**: [Ready for Smart Bidding & broad match | Needs fixes before next bid strategy change | Tracking is broken — STOP all optimization until fixed]

## Critical issues (must fix before any bid strategy / broad match change)

[list, with check ID, evidence, fix]

## High-priority fixes

[list]

## Medium / low

[list]

## What's working

[positive findings — keep these reinforced]

## Draft actions

Write `data/draft-actions-tracking-YYYY-MM-DD.csv` with the same schema as `/account-audit`.

## Next step

[recommend one of: /search-term-audit, /account-audit, or manual fix list]
```

## Decision rules

- If A1=0 (no primary conversion action) → **STOP**. Everything else is moot.
- If C3 (GCLID capture rate) < 30% → **CRITICAL**. Recommend pausing all OCI work until capture is fixed.
- If E4 fails (broad match without OCI) → recommend pausing broad match immediately as L3 draft action.
- If D3 (OCI success rate) < 70% → diagnose the rejection reasons before any other recommendation.
- If F1 fails → recommend Data-Driven if volume allows, else Position-Based.

## Rules

- Do not assume a check passes if the data isn't available. Mark `not_evaluated` and list the export needed.
- Quote actual values: e.g. "Conversion action 'Lead' has click-through window of 30 days; sales cycle in CLAUDE.md is 84 days — fails A3 by 54 days."
- When recommending an EC4L fix, give the exact menu path: "Tools & Settings → Conversions → Settings → Customer data terms → Enhanced conversions for leads."
