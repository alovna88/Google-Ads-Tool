# Google Ads Agency Tool

Internal tool for running paid-search across a portfolio of B2B SaaS clients. Built on free tooling — Google Ads API, Claude API, open MCP servers, Wayback Machine, WordStream blended benchmarks — with the agency's own data as the moat.

## What this is

Two artifacts that ship together:

| | Web app | Skills pack |
|---|---|---|
| **Use case** | Multi-client, scheduled, write-safe operations | One-shot creative and research tasks |
| **Status** | Architecture committed, scaffolding next | Shipping now (`/skills/`) |
| **Backed by** | Google Ads API + Postgres + Claude API + worker queue | Claude Code + per-client `playbook.md` |
| **Examples** | Weekly audit run, action queue, monthly PDF report, anomaly alerts | "Generate 20 RSA variants", "Mine these Reddit threads for VoC" |

The skills pack works standalone today. The web app supersedes the manual workflows once it's built.

## What this is not

- Not a Meta/LinkedIn/Microsoft Ads tool. Best-in-class on Google Ads first.
- Not a replacement for Optmyzr / Adalysis at feature-checklist count. Differentiates on conversational workflow + action queue + B2B SaaS opinion.
- Not autopilot. Every write goes through a draft → approve → push queue. Practitioner consensus: AI needs a pilot.
- Not multi-tenant SaaS. Internal to one agency.

## Repository layout

```
.
├── README.md                ← you are here
├── docs/
│   ├── architecture.md      ← system design, stack, subsystems
│   ├── roadmap.md           ← P0 / P1 / P2 feature ladder
│   ├── data-model.md        ← Postgres schema sketch
│   └── research-notes.md    ← grounded findings from URL research + practitioner survey
├── skills/                  ← Claude Code skills pack (ship today)
│   ├── README.md            ← install + usage
│   ├── CLAUDE.md.template   ← per-client agency context
│   ├── account-audit/
│   ├── conversion-tracking-health/
│   ├── search-term-audit/
│   ├── close-variant-checker/
│   ├── negative-keyword-builder/
│   ├── icp-research/
│   ├── ad-copy-variants/
│   ├── competitor-watch/
│   ├── weekly-report/
│   └── monthly-report/
└── app/                     ← web app (to be scaffolded)
```

## Getting started with the skills pack

See [`skills/README.md`](skills/README.md). Briefly:

```bash
# Install all skills into your user-level Claude Code skill directory
for d in skills/*/; do
  name=$(basename "$d")
  ln -s "$(pwd)/$d" ~/.claude/skills/$name
done

# Create a per-client folder and copy the CLAUDE.md template
mkdir -p ~/agency/clients/acme && cd ~/agency/clients/acme
cp /path/to/this/repo/skills/CLAUDE.md.template CLAUDE.md
$EDITOR CLAUDE.md  # fill in client context

# Launch Claude Code and invoke any skill
claude
> /account-audit
```

## Stack at a glance

- **Backend**: Python 3.12 + FastAPI
- **Frontend**: Next.js 15 + Tailwind + shadcn/ui
- **Database**: Postgres 16
- **Queue**: Redis + RQ
- **LLM**: Claude API (Sonnet 4.6 default, Opus 4.7 for full audits) with prompt caching + Batch API
- **Hosting**: Fly.io for app + worker, Cloudflare R2 for blob storage
- **Ads data**: Google Ads API (Basic Access dev token), `cohnen/mcp-google-ads` for read, custom write tools
- **Auth**: Google OAuth (agency staff), per-client OAuth to MCC

## Research grounding

Every architectural decision is cross-referenced to a real source in [`docs/research-notes.md`](docs/research-notes.md). If a claim is not in that document, it is not load-bearing for the architecture.
