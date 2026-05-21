# Skills pack

Twelve Claude skills for running a B2B SaaS Google Ads agency workflow (with a Reddit Ads complement). Each is a self-contained `SKILL.md`. Ten target Claude Code (`~/.claude/skills/`, invoked as `/<skill-name>`); the Reddit Ads workflow also ships a **Desktop variant** (`reddit-ads-campaign-dev-desktop/`) that can be zipped and uploaded into Claude Desktop / Claude.ai under Settings → Capabilities → Skills.

## Installation

```bash
# Clone or pull this repo somewhere stable
cd /path/to/Google-Ads-Tool

# Symlink every skill into your user-level Claude Code skill directory
mkdir -p ~/.claude/skills
for d in skills/*/; do
  name=$(basename "$d")
  if [ -f "$d/SKILL.md" ]; then
    ln -sfn "$(pwd)/$d" ~/.claude/skills/$name
    echo "Installed /$name"
  fi
done
```

Then create a per-client workspace:

```bash
mkdir -p ~/agency/clients/acme
cp /path/to/Google-Ads-Tool/skills/CLAUDE.md.template ~/agency/clients/acme/CLAUDE.md
$EDITOR ~/agency/clients/acme/CLAUDE.md   # fill in client context

cd ~/agency/clients/acme && claude
> /account-audit
```

## The skills

| Skill | When | What it produces |
|---|---|---|
| `/account-audit` | Onboarding, quarterly health check | Weighted A–F audit across 80+ checks, ranked fixes, draft action list |
| `/conversion-tracking-health` | Weekly, before any bid strategy change | The 7 destructive defaults audit + EC4L + OCI sanity; required for the "broad match prerequisite" |
| `/search-term-audit` | Weekly | N-gram analysis of last 30d search terms with profit math, ranked negative-keyword recommendations |
| `/close-variant-checker` | Monthly | AdPulse-style close-variant detection per ad group with allowed-phrases whitelist and draft negatives |
| `/negative-keyword-builder` | Onboarding, then maintenance | B2B SaaS starter negative library + client-specific overlays, formatted for bulk upload |
| `/icp-research` | Quarterly audience refresh, new campaign launch | Mines Reddit/G2/competitor reviews into a Voice-of-Customer brief + Meta/Google targeting + hook angle |
| `/ad-copy-variants` | Weekly creative refresh | RSA / asset variants with brand-voice guardrails and psychological angle labels |
| `/competitor-watch` | Monthly | Wayback diffs + sitemap diff + Transparency Center snapshot summary for 3–5 competitors |
| `/reddit-ads-campaign-dev` | New Reddit campaign launch, paid-social expansion | End-to-end Reddit Ads brief: subreddit shortlist, layered targeting, structure, native-voice creative, Pixel + CAPI setup, launch checklist, scaling framework |
| `reddit-ads-campaign-dev-desktop` | Same use case, but running in Claude Desktop / Claude.ai | Desktop-native variant of the above — no `CLAUDE.md` gate, all output inline as Markdown for copy-paste |
| `/weekly-report` | Every Monday 6am | One-page agency-grade weekly performance summary with deltas, anomalies, and 3 specific actions |
| `/monthly-report` | First business day of month | Branded one-page-per-section monthly client report covering pipeline, spend, learnings, plan |

## Workspace expectation

Every skill assumes you are running Claude Code in a folder that contains:

```
.
├── CLAUDE.md          ← per-client context (see CLAUDE.md.template)
├── data/              ← CSVs / Google Ads exports
├── reports/           ← generated outputs land here
├── competitor/        ← competitor URLs + Wayback snapshots
└── creative/          ← ad copy + landing-page drafts
```

If `CLAUDE.md` is missing, every skill will refuse to run and tell you to set it up.

## How skills interact

```
                  ┌─────────────────┐
                  │   CLAUDE.md     │  ← the steering wheel; read by every skill
                  └─────────────────┘
                          │
            ┌─────────────┼─────────────────────────────────────┐
            ▼             ▼                                     ▼
  Diagnostic skills   Build skills                       Reporting skills
  ──────────────────  ─────────────                      ───────────────
  /account-audit       /negative-keyword-builder         /weekly-report
  /conversion-...      /icp-research                     /monthly-report
  /search-term-audit   /ad-copy-variants
  /close-variant-...   /reddit-ads-campaign-dev
  /competitor-watch
```

Diagnostic skills output a `data/audit-results.json` and a Markdown report. Reporting skills read from those when present.

## Conventions every skill follows

- **Profit framing, not CPC.** Every metric is converted to CAC / ROAS / pipeline $ using the playbook's conversion hierarchy.
- **Evidence-first.** Every claim references the exact rows / queries / keywords that informed it.
- **Draft, don't apply.** Skills produce a draft action list. Until the web app's Action Queue exists, these are exported as a `data/draft-actions-YYYY-MM-DD.csv` for manual bulk-upload to Google Ads.
- **Top 3, every time.** Skills end with a "Top 3 actions for this week" list.
- **No invented data.** If a required input is missing (e.g. ACV, sales cycle), the skill stops and asks rather than guess.

## Costs

These skills run on whatever Claude plan you're on (Pro / Max). They use:
- Web fetch (free)
- File read/write (free)
- Optionally MCP servers like `cohnen/mcp-google-ads` for live API reads (free, dev token required)

No additional paid tooling.
