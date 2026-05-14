# Google Ads Agency Tool

Internal tool for running paid-search across a portfolio of B2B SaaS clients. Built on free tooling — Google Ads API, Claude API, open MCP servers, Wayback Machine, WordStream blended benchmarks — with the agency's own data as the moat.

## What this is

Two artifacts that ship together:

| | Web app | Skills pack |
|---|---|---|
| **Use case** | Multi-client, scheduled, write-safe operations | One-shot creative and research tasks |
| **Status** | Scaffold up: clients CRUD + playbook editor. OAuth, sync, audits coming next. | Shipping (`/skills/`) |
| **Backed by** | FastAPI + Postgres + RQ worker + Claude API | Claude Code + per-client `playbook.md` |
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
├── skills/                  ← Claude Code skills pack (zero-infra, ship today)
│   ├── README.md
│   ├── CLAUDE.md.template
│   └── <10 skills>/SKILL.md
├── app/                     ← web app (FastAPI + Next.js + RQ worker)
│   ├── pyproject.toml
│   ├── Dockerfile.api
│   ├── Dockerfile.worker
│   ├── fly.api.toml
│   ├── fly.worker.toml
│   ├── alembic.ini  alembic/
│   ├── agency_ads/          ← Python package (api + worker share)
│   │   ├── main.py          ← FastAPI entry
│   │   ├── worker.py        ← RQ entry
│   │   ├── config.py  db.py
│   │   ├── models/ schemas/ routes/ services/ jobs/
│   └── web/                 ← Next.js 15 app
│       ├── package.json  Dockerfile  fly.toml
│       ├── app/ components/ lib/
├── docker-compose.yml       ← full local stack
├── Makefile                 ← dev / migrate / logs shortcuts
└── .env.example
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

## Running the web app locally

Requires Docker, Docker Compose, and Make. Node and Python are NOT required on the host — everything runs in containers.

```bash
# 1. Configure environment
cp .env.example .env
# (edit .env to set SESSION_SECRET to a real random value)

# 2. Bring up the stack
make dev

# 3. Apply database migrations (one-time after first start)
make migrate

# 4. Visit
#    Web:        http://localhost:3000
#    API health: http://localhost:8000/health
#    API DB:     http://localhost:8000/health/db
#    API docs:   http://localhost:8000/docs
```

Useful commands:

```bash
make logs                       # tail logs from all services
make ps                         # show running services
make shell-db                   # psql shell against local Postgres
make shell-api                  # bash shell in the api container
make revision m="add foo table" # create a new Alembic migration (autogenerate)
make migrate                    # apply migrations
make down                       # stop the stack
make clean                      # stop + remove local data volumes
```

### Smoke test — create a client and edit its playbook

```bash
curl -s localhost:8000/health
curl -s -X POST localhost:8000/clients \
  -H 'Content-Type: application/json' \
  -d '{"name":"Acme","slug":"acme","currency":"USD","timezone":"America/New_York"}'

# Then visit http://localhost:3000/clients
```

## What's wired in this commit

- ✅ FastAPI app with health endpoints, OpenAPI docs at `/docs`
- ✅ Postgres + Alembic with initial schema (`users`, `clients`, `playbooks`)
- ✅ Redis + RQ worker (stub jobs)
- ✅ Clients CRUD endpoints (list, create, get)
- ✅ Playbook get/save endpoints with parsed JSONB
- ✅ Next.js 15 frontend: home, clients list, new-client form, client detail with playbook editor
- ✅ docker-compose for one-command local dev
- ✅ Dockerfiles + Fly.io configs for production

## What's NOT wired yet (next commits)

- ❌ Authentication — single-user assumption for now; Google OAuth for staff is next
- ❌ Google Ads OAuth + MCC connection — applied for the dev token in parallel
- ❌ Nightly GAQL sync (the `sync_client_account` job is a stub)
- ❌ Audit engine, action queue, reports — see `docs/roadmap.md` P0 list

## Deploying to Fly.io

```bash
# Create the three apps
fly apps create agency-ads-api
fly apps create agency-ads-worker
fly apps create agency-ads-web

# Postgres (Fly's managed Postgres)
fly postgres create --name agency-ads-db
fly postgres attach agency-ads-db --app agency-ads-api
fly postgres attach agency-ads-db --app agency-ads-worker

# Redis (Upstash via Fly)
fly redis create   # follow prompts; copy the REDIS_URL into secrets

# Set shared secrets
fly secrets set --app agency-ads-api SESSION_SECRET=... ANTHROPIC_API_KEY=...
fly secrets set --app agency-ads-worker ANTHROPIC_API_KEY=...

# Deploy each service
cd app && fly deploy --config fly.api.toml
cd app && fly deploy --config fly.worker.toml
cd app/web && fly deploy

# First-time migration
fly ssh console --app agency-ads-api -C "alembic upgrade head"
```

## Research grounding

Every architectural decision is cross-referenced to a real source in [`docs/research-notes.md`](docs/research-notes.md). If a claim is not in that document, it is not load-bearing for the architecture.
