# Architecture

## 1. Premise

This is an internal agency tool, not a SaaS. Its purpose is to take the weekly/monthly/quarterly motions an agency performs on every B2B SaaS Google Ads account and (a) automate the boring parts, (b) draft the dangerous parts for human approval, and (c) preserve change history so we can learn across the portfolio.

The HeyOz "Claude Skills" approach — local CLAUDE.md plus slash commands — is the right primitive for *creative* and *research* tasks (ICP, ad copy, hook mining). It is the wrong primitive for *operations* (multi-client sync, scheduled audits, OCI uploads, anomaly detection, action queue). Therefore the deliverable is two artifacts:

1. **Skills pack** (`/skills/`) — installable Claude Code skills, ship now.
2. **Web app** (`/app/`) — multi-tenant operations service, ship in phases.

## 2. The spine: Offline Conversion Tracking

Every B2B SaaS source independently converges on this. The clicker is rarely the signer (6–10 person buying committees per Involve Digital). Sales cycles average 84 days (per GrowthSpree). Optimizing toward CPL or demo-request volume teaches Smart Bidding to find people who fill forms — not people who become customers.

So the tool's central data flow is:

```
Google Ad click (GCLID stored on lead)
   ↓
CRM lead created → lifecycle stage transitions (MQL → SQL → Opp → Closed-Won)
   ↓
Daily sync: read CRM, join on GCLID, compute conversion value per stage
   ↓
Google Ads API: ConversionUploadService.UploadClickConversions
   ↓
Smart Bidding trains on pipeline / revenue signal, not lead volume
```

If the tool fails to make this loop trivial to set up, it does not differ from existing dashboards.

**MVP shortcut (per user decision):** in P0, OCI runs from a Google Sheet. Agency manually maintains a sheet with `gclid | stage | value | timestamp` and the tool uploads daily. HubSpot and Salesforce CRM connectors land in P1.

## 3. System diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     WEB APP (Next.js)                           │
│  Action Queue · Audits · Reports · Per-client Playbook · Library│
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                 API SERVER (Python · FastAPI)                   │
│  GAQL builder · Audit engine · Report assembler · OCI pipeline  │
│  Action queue executor · LLM analysis (Claude API + caching)    │
└─────────────────────────────────────────────────────────────────┘
       │                 │                 │                │
       ▼                 ▼                 ▼                ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  Postgres    │  │   Redis      │  │ Cloudflare R2│  │ Worker pool  │
│  metrics,    │  │ queue +      │  │ raw CSVs,    │  │ scheduled    │
│  entities,   │  │ cache        │  │ PDF reports, │  │ syncs +      │
│  changelog   │  │              │  │ Wayback dumps│  │ audits       │
└──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘
       │                                                     │
       ▼                                                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                  EXTERNAL INTEGRATIONS                          │
│  Google Ads API · Google Sheets (OCI input) · Wayback CDX       │
│  WordStream blended benchmark · Transparency Center (P2, gated) │
└─────────────────────────────────────────────────────────────────┘

Companion: /skills/  — installable Claude Code skill pack (zero-infra)
```

## 4. Stack and rationale

| Layer | Choice | Rationale |
|---|---|---|
| Backend lang | Python 3.12 | `google-ads-python` is mature, `cohnen/mcp-google-ads` is Python, pandas/scikit for n-grams |
| Backend framework | FastAPI | Async, light, OpenAPI for free, fits the request volume |
| Frontend | Next.js 15 + Tailwind + shadcn/ui | Server components for data fetching; no design debt |
| DB | Postgres 16 | Cross-client aggregations for private benchmark; JSONB for change events |
| Queue | Redis + RQ | Simpler than Celery for 50-client scale |
| Object store | Cloudflare R2 | S3-compatible, no egress fee, cheap |
| LLM | Claude API: Sonnet 4.6 default, Opus 4.7 for full audits | Sonnet is the workhorse; Opus for high-stakes weighted-scoring runs |
| LLM ops | Prompt caching + Batch API | ~90% cost reduction on cached per-client context; 50% Batch discount fine for weekly/monthly |
| Hosting (app + worker) | Fly.io | Single-region OK at our scale; ~$50–100/mo all-in |
| Ads read | `cohnen/mcp-google-ads` (Python, FastMCP) | Read-only GAQL + MCC; we layer our own server on top |
| Ads write | Custom — built on `google-ads-python` | No MCP exposes mutations today |
| Auth (staff) | Google OAuth | Agency is already on Google |
| Auth (per client) | Google Ads OAuth → MCC, refresh tokens | Standard developer-token + login-customer-id flow |
| Migrations | Alembic | Standard |
| Tests | pytest + Playwright | API + e2e |

## 5. Subsystems

### 5.1 Read layer (GAQL ingestion)

Daily snapshot per client:
- Account, campaign, ad group, keyword, ad, asset, asset group entities
- 30-day rolling metrics at all levels
- `change_event` for change history (who changed what, when, including Google's auto-applied recommendations)
- `search_term_view` for last 7 days (n-gram analysis)
- `recommendation` resource (current set, dismissed set)

Runs via `GoogleAdsService.SearchStream` to stay under operation quota. Persisted to Postgres normalized tables + raw response JSON in R2 for replay.

### 5.2 Action Queue (the differentiator)

Every proposed change is an `Action`:
```
{
  client_id, type, target, diff, reasoning, evidence, expected_impact,
  confidence, risk_tier, status, approver_id, approved_at, executed_at
}
```

Types include: `pause_campaign`, `add_negative`, `change_budget`, `upload_oci`, `edit_rsa_asset`, `pause_keyword`, `change_target_cpa`, `disable_auto_apply`.

Risk tiers:
- **L1 — low risk** (e.g. negative keyword from search-term audit with profit math): bulk-approvable
- **L2 — medium risk** (e.g. budget shift <20%, asset rotation): individual approve, single click
- **L3 — high risk** (e.g. bid strategy change, campaign pause, structure change): individual approve + MFA + "are you sure" confirmation

Every L2/L3 execution writes a webhook + email to the client's account owner. Account-hijacking is a documented 2025 wave; this is non-negotiable.

### 5.3 Audit engine

Adapted from the claude-ads 250-check taxonomy + Aaron Young STAB + the "7 destructive defaults" + Adalysis's 100+ checks. Each check is a Python callable taking `(client, snapshot) -> CheckResult` where `CheckResult` carries severity, weight, evidence, suggested fix, optional draft `Action`.

Categories:

| Category | Weight | Approx check count |
|---|---|---|
| Tracking & Measurement | 0.25 | 40 |
| Account Structure | 0.20 | 35 |
| Bidding & Budget | 0.15 | 35 |
| Keywords & Search Terms | 0.15 | 35 |
| Ads & Assets | 0.10 | 35 |
| Audience & Targeting | 0.10 | 25 |
| Settings & Defaults | 0.05 | 15 |

Severity multipliers: Critical 5.0 · High 3.0 · Medium 1.5 · Low 0.5. Score normalized to 0–100, mapped to A–F.

### 5.4 OCI pipeline

P0 implementation:
- Source: agency-maintained Google Sheet per client (`gclid | stage | value | timestamp | conversion_action_name`)
- Worker reads sheet at 09:00 local daily
- Validates GCLID format, deduplicates, joins to active conversion actions
- Calls `ConversionUploadService.upload_click_conversions` per client
- Records success/failure per row; surfaces broken uploads in Action Queue

P1: HubSpot connector — listen for lifecycle stage transitions, write to sheet automatically.
P2: Salesforce — Stage Models, multi-object funnel.

### 5.5 Per-client playbook (the steering wheel)

Each client has a `playbook.md` versioned in Git on the server. Pattern borrowed from `karpathy/autoresearch` (`program.md`). Read by every audit run, every Claude analysis call, every draft-action generation. Schema in `docs/data-model.md`.

Key fields:
- ICP, sales cycle days, ACV, target CAC, target LTV:CAC, payback months
- Required campaign archetypes (default for B2B SaaS: Brand, Competitor, Non-brand product, Non-brand problem, Remarketing)
- Bidding rules (e.g. "do not enable broad match without OCI flowing for 30+ days")
- Negative exclusions (client-specific add-ons to the starter library)
- Conversion event hierarchy and values (e.g. SQL=$50, Opp=$500, Closed-Won=ACV)
- Brand voice (tone, banned phrases, required disclaimers)
- Approval thresholds (e.g. "auto-approve L1 actions under $50 wasted spend; everything else requires human")

### 5.6 LLM layer

- **Default model**: Claude Sonnet 4.6
- **Escalation model**: Claude Opus 4.7 for full audits and monthly reports
- **Prompt caching**: cache per-client `playbook.md`, recent 30-day metric summary, and reference docs. 90% cost reduction on cached tokens.
- **Batch API**: weekly summaries and monthly reports run via Batch (50% discount, 24h SLA fine for these cadences).
- **Structured output**: every Claude call uses tool_use with strict JSON schemas — never free-form text into the action queue.

Estimated cost for 50 clients (per agent 2 research): ~$10–20/mo Sonnet baseline; ~$50–80/mo if Opus is used liberally on audits.

### 5.7 Competitor watch (P2)

Free-only sources:

| Source | Method | Caveat |
|---|---|---|
| Their landing pages over time | Wayback Machine CDX API (free, no auth) | Only captured snapshots — not real-time |
| New pages | Diff weekly `/sitemap.xml` fetch | Misses pages outside sitemap |
| Tech stack changes | Wappalyzer CLI (open source) | Detection only, no signal on intent |
| Brand bidding (are they bidding on our brand?) | Auction Insights — UI export upload only | Not in API |
| Their Google Ads creatives | Transparency Center | No official API; scraping is gray-ToS — flag for legal review |
| Their Meta ads | Meta Ad Library API is EU-political-only in 2026 | Effectively unavailable for B2B SaaS |

Honest user-facing message: we monitor what's free and ToS-clean. Keyword-level competitor data requires paid tools (Semrush, Ahrefs) — outside scope.

## 6. Hard constraints and risks

| Constraint | Mitigation |
|---|---|
| Developer token approval has a real backlog (per ppc.land) | Apply day 1. Use Test Access for dev. Have a sandbox MCC. |
| Auction Insights is not in API | Manual UI export → CSV upload flow in the app |
| Meta Ad Library API regression (EU-political only) | Drop Meta competitor watch from scope |
| 2025 account-hijacking wave | MFA on all L2/L3 writes; minimal OAuth scopes; alert account owners on every write |
| Google reps push PMax/AI-Max behind agency's back | "B2B SaaS Guard Mode" in playbook detects + alerts; auto-rec disabling is a P0 check |
| Close-variant false positives in auto-negatives | Show profit math (Optmyzr warning); require approval in MVP — no autopilot |
| Claude Opus 4.7 tokenizer is ~35% heavier per [Finout analysis] | Default Sonnet; budget +35% if escalating to Opus |
| MSAs may not cover cross-client benchmark aggregation | Standard clause; aggregate/anonymize; opt-in per client |

## 7. Non-goals

- Meta / LinkedIn / Microsoft / Amazon Ads
- Public SaaS / multi-agency tenancy
- Replacing Optmyzr/Adalysis on raw feature count
- Autopilot bid management
- Fully managed creative generation (image/video) — that's HeyOz's territory

## 8. Reference architecture lineage

- `karpathy/autoresearch` — single mutable artifact + human-editable `program.md` skill per iteration
- `AgriciDaniel/claude-ads` — 250-check weighted scoring, A–F grade, three-layer skill architecture
- `AdPulse` close variant checker — allowed-phrases whitelist + auto-negative writer pattern
- `Brainlabs Search Query Mining` — n-gram analysis script (open source)
- `cohnen/mcp-google-ads` — read-only MCP, our read baseline
- AdeptAds.ai — decision-log-with-reasoning + approval gates (competitive reference)
- WordStream/LocaliQ 2025 benchmarks — public blended benchmark we cite

Full source citations in `docs/research-notes.md`.
