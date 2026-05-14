# Roadmap

Three tiers. Each tier is a coherent release that delivers user-visible value on its own.

## P0 — MVP (target: ~8 weeks engineering)

The minimum that's better than running everything in spreadsheets + Looker Studio.

### 0.1 Skills pack (shipping today)
- 10 Claude Code skills installable into `~/.claude/skills/`
- Per-client `CLAUDE.md.template` with B2B SaaS defaults
- See `skills/` directory

### 0.2 Multi-client onboarding + read sync
- Google OAuth flow to agency MCC
- Pick which client CIDs to include
- Nightly read sync via `SearchStream`:
  - Account, campaign, ad group, keyword, ad, asset, asset group
  - Last-30-days metrics at each level
  - `change_event` for change history (incl. Google's auto-applied recommendations)
  - `search_term_view` last 7 days
  - `recommendation` resource (current + dismissed)
- Persist normalized + raw to Postgres / R2

### 0.3 Per-client playbook
- Markdown editor in app (CodeMirror)
- Version history (each save creates a Git commit on the server)
- Validation: required fields (ICP, sales cycle, target CAC, conversion hierarchy)

### 0.4 Search-term auditor
- N-gram analysis (1/2/3 grams) over last 30 days
- Close-variant inference (string distance + match-type comparison)
- Profit math: cost vs estimated profit per n-gram (using playbook's stage values)
- Output: ranked draft negatives with reasoning, evidence sample, expected savings
- Feeds Action Queue

### 0.5 Conversion tracking health audit
- The 7 destructive defaults (GrowthSpree):
  1. 30-day click-through conversion window (should be 90 for B2B)
  2. Auto-applied recommendations ON
  3. "Include Google Display Network" on new Search campaigns
  4. Broad match without OCI prerequisite
  5. Maximize Conversions without Target CPA cap
  6. Search partners enabled (with no proven uplift evidence)
  7. Auto-applied ad variants
- Plus: EC4L firing check, GCLID-to-CRM match rate, conversion-action primary/secondary hierarchy sanity
- Output: per-account health score + draft actions to fix each

### 0.6 Action Queue
- Schema: `actions` table with type, target, diff, reasoning, evidence, expected_impact, confidence, risk_tier, status
- UI: queue grouped by client, sortable by impact, filterable by risk
- L1 bulk-approve, L2 single-click, L3 single-click + MFA + confirm
- On execute: call Google Ads API via `google-ads-python`, write to changelog, notify account owner
- Reject / Edit-and-approve flows
- Approved actions are immutable; rejected actions stay searchable

### 0.7 Weekly summary report
- Per-client, auto-generated each Monday 06:00 local
- Sections: headline metrics + delta, top wins, top losses, anomalies, recommended actions for the week
- Format: HTML email + Markdown export
- Generated via Claude (Sonnet, Batch API for cost)

### 0.8 Budget pacing alerts
- Compare MTD spend vs ideal pacing per campaign
- Alert thresholds configurable per client in playbook
- Drafts a budget redistribution Action when over/under by >15%

### 0.9 Anomaly detection
- Z-score on CPA, CTR, conv-rate, impression share, spend (per campaign, 14-day window)
- Special handling: "learning phase exit" detection (Performance Cliff pattern from Joe Martinez)
- Alerts feed cross-client Insights tab

### 0.10 Google Sheets OCI uploader
- Per-client sheet ID configured in playbook
- Daily 09:00 sync: read sheet, validate, dedupe, upload to `ConversionUploadService`
- Failure surfacing: which rows failed and why → Action Queue
- Template Google Sheet provided for clients to populate

---

## P1 — V2 (target: ~8 weeks after P0)

Builds the moat on top of MVP.

### 1.1 Full audit engine with weighted A-F score
- 200+ checks across 7 categories (see `architecture.md` §5.3)
- Each check: severity, weight, evidence, fix suggestion, optional draft Action
- Monthly auto-run + on-demand
- Score history chart per client

### 1.2 Branded monthly client report (PDF)
- Configurable agency template (logo, colors, footer)
- Sections: exec summary, spend pacing, pipeline KPIs (CAC, SQL, LTV:CAC), top wins/losses, search-term insights, action plan
- Generated via Claude Opus (one shot per client per month — quality > cost)
- Scheduled delivery via email; PDF stored in R2

### 1.3 Negative keyword starter library
- B2B SaaS reusable categories: jobs/careers/salary, education/tutorial, free/open-source, competitor employees, login/support
- "Apply library to client" with diff preview → Action Queue
- Client-specific overlays kept in playbook

### 1.4 HubSpot CRM connector for OCI
- OAuth to HubSpot
- Listen for lifecycle stage changes (Lead → MQL → SQL → Opp → Closed-Won)
- Auto-populate the OCI sheet (or upload directly, configurable)

### 1.5 Ad copy generation with brand-voice guardrails
- Generate RSA variants per ad group from playbook brand voice
- Banned phrase list, required tone keywords, character limit enforcement
- Output: drafts in Action Queue with diff vs current RSA

### 1.6 PMax cannibalization detector
- Compare PMax brand-traffic share vs Search Brand campaign share
- Flag overlap; suggest brand exclusion list for PMax
- Cites the Optmyzr "91.45% of accounts have overlap" finding

### 1.7 Auction Insights uploader (UI workaround)
- Manual CSV drop zone — parse Google's Auction Insights export
- Persist per-campaign competitor presence over time
- Surface "new competitor appeared on brand keywords" alerts

---

## P2 — V3 (target: ~12 weeks after P1)

Earns its place once the spine is solid.

### 2.1 Competitor watch
- Wayback Machine CDX API: weekly landing-page diffs per competitor URL
- Sitemap diff: new URLs detected weekly
- Wappalyzer CLI: tech stack change detection
- Transparency Center: optional, gray-ToS — explicit opt-in per agency
- Output: weekly "competitor moves" digest

### 2.2 Salesforce CRM connector
- Stage Models (multi-object funnel beyond Lead)
- Same OCI write path

### 2.3 Private cross-client benchmarks
- Aggregate (anonymized) CAC, CPL, CPC, CVR by industry/ACV-band
- Opt-in per client via playbook flag
- Combined with WordStream/LocaliQ blended numbers for context

### 2.4 Experiments runner
- karpathy/autoresearch-inspired: one mutable campaign artifact + bounded iteration
- Uses Google Ads Experiments / Campaign Drafts API
- 30-day window default; auto-promote winner to base via Action Queue
- Constrained to a fixed evaluation metric defined in playbook

### 2.5 B2B SaaS strategy templates
- Pre-built campaign-build templates by ACV band (sub-$10k, $10–50k, $50k+)
- Conversion hierarchy templates by sales cycle (<30 days, 30–90, 90+)
- Negative library by vertical (DevTools, MarTech, HRTech, FinTech, Security)

---

## Things explicitly deferred

| Item | Reason |
|---|---|
| Meta / LinkedIn / Microsoft / Amazon | Single-platform excellence first |
| Public SaaS launch | Internal only |
| Mobile app | Web-only is fine |
| Built-in creative generation (images/video) | HeyOz territory |
| Replicating Optmyzr's 80-recipe library | Losing competition; differentiate on workflow |
| Multi-agency / white-label | Increases complexity 5x; explicit non-goal |
