# Research notes

Every architectural decision in this repo traces to one of these findings. If a claim is not here, it is not load-bearing.

## 1. B2B SaaS Google Ads playbooks (URL list research)

### Sources
- [adconversion.com/blog/b2b-google-ads-saas](https://www.adconversion.com/blog/b2b-google-ads-saas) — framework: 5 campaign themes (NonBrand, Brand, Competitive, RLSA, Content). Light on tactics.
- [involvedigital.com/insights/google-ads-b2b-saas](https://www.involvedigital.com/insights/google-ads-b2b-saas) — non-branded SaaS CPC up 29% YoY to $5.34 avg; B2B buying committees 6–10 people; LTV:CAC 3:1 min, 5:1 top quartile.
- [dirkroettges.de — default settings post](https://www.dirkroettges.de/why-default-google-search-ads-settings-are-costing-your-b2b-service-leads-and-how-to-fix-it/) — 800+ B2B audits; recommends Max Clicks + Exact Match when conversion volume is too low to train Smart Bidding.
- [directiveconsulting.com — How B2B SaaS Loses](https://directiveconsulting.com/blog/how-b2b-saas-companies-lose-with-google-ads-and-how-to-fix-it/) — $65M+ B2B SaaS spend managed. Key insight: optimize toward SQLs / pipeline / revenue rather than CPL.
- [adeptads.ai](https://adeptads.ai/) — competitive reference: multi-agent AI with decision log + reasoning + approval gates.
- [github.com/karpathy/autoresearch](https://github.com/karpathy/autoresearch) — pattern: agent edits one mutable artifact per iteration under fixed wall-clock budget, single comparable metric. `program.md` is human-editable "skill".
- [github.com/cohnen/mcp-google-ads](https://github.com/cohnen/mcp-google-ads) — read-only MCP, FastMCP + google-ads Python. Confirmed: no mutations exposed. We build write tools.
- [agricidaniel.com / AgriciDaniel/claude-ads](https://agricidaniel.com/blog/claude-code-ad-agency) — 250+ checks across 6 ad platforms, 3-layer skill architecture, weighted A-F scoring.
- [dreamdata.io/blog/dreamdata-google-offline-conversions](https://dreamdata.io/blog/dreamdata-google-offline-conversions) — OCI implementation: GCLID on lead, daily upload, value per stage, multi-object funnel beyond Lead.
- [growthspreeofficial.com — B2B SaaS Why Different 2026](https://www.growthspreeofficial.com/blogs/google-ads-for-b2b-saas-why-different-what-agency-must-know-2026) — companion "Waste Report" claims $11.3M wasted across 43 enterprise B2B SaaS accounts; the 7 destructive defaults framework.
- [vehnta.com — PPC Playbook](https://vehnta.com/google-ads-b2b-saas-ppc-playbook/) — negative keyword math: 200–500 per account, 20–50 added monthly.
- [mrrunlocked.com](https://www.mrrunlocked.com/p/google-ads-guide) — budget split: 60–70% high-intent product, 20–30% competitor; max 2 campaigns at start.
- [adpulse.app close variant checker](https://adpulse.app/blog/how-to-guides/adpulse-close-variant-checker-google-ads-script-instructions/) — pattern: per-ad-group close-variant detection, allowed-phrases whitelist, auto-negative writer. ~20% budget waste rule of thumb.

### Synthesis: what every source agrees on
1. **OCI / EC4L is the spine.** Cited by Dreamdata, Directive, GrowthSpree, Vehnta, MRR Unlocked, Involve.
2. **Don't trust Google defaults.** 30-day window, broad match, auto-recommendations, display-network expansion, search partners.
3. **Optimize toward later funnel stages**, not CPL.
4. **Account structure: Brand / Competitor / High-intent / Problem-aware** as separate campaigns.
5. **Sales cycle ≥84 days → 90-day conversion window** is the right B2B default.

### Tensions across sources
- **Smart Bidding**: Roettges says Max Clicks + Exact Match when volume is low; everyone else assumes Smart Bidding once OCT is wired. Resolution: volume-dependent decision; tool detects conversion density.
- **Broad match**: AdConversion treats as viable, GrowthSpree reports 73% median waste, Vehnta says "only with negatives + ECfL." Resolution: gate broad match on precondition checklist.

## 2. Technical foundations

### Google Ads API
- **Developer token access tiers** (free, gated by review): Test Access (instant, test accounts only) → Basic Access (15,000 ops/day) → Standard Access (unlimited, harder to obtain, known backlog per ppc.land).
- **Rate limits**: QPS per CID + per developer token. Mutate requests capped at 10,000 operations/request. Hourly limits at all tiers.
- **Close variants**: no explicit `is_close_variant` field on `search_term_view`. Must compare search term text to triggering keyword text + match types to infer.
- **Auction Insights**: not generally available via API (`metrics.auction_insight_search_*` fields exist but allowlist-gated). Practical workaround: UI export.
- **PMax**: `asset_group_top_combination_view` exposes asset combinations; `campaign_search_term_view` exposes aggregated PMax search terms — but the rich "Search Term Insights" categorization is UI-only.
- **Recommendations**: fully accessible via `recommendation` resource + `RecommendationService.Apply/Dismiss`.

Sources:
- [Access Levels](https://developers.google.com/google-ads/api/docs/access-levels)
- [Quotas](https://developers.google.com/google-ads/api/docs/best-practices/quotas)
- [Developer Token Backlog](https://ppc.land/google-faces-developer-token-application-backlog-as-new-api-tier-debuts/)
- [search_term_view fields](https://developers.google.com/google-ads/api/fields/v22/search_term_view)
- [Close variants help](https://support.google.com/google-ads/answer/9342105)

### Google Ads Scripts
- Cannot be triggered externally; only Google's scheduler (hourly/daily/weekly/monthly).
- Can hit arbitrary HTTPS endpoints — viable as edge agents that POST back to our server.
- Public open-source close-variant scripts:
  - [Nils Rooijmans — close variant monitor](https://nilsrooijmans.com/effortlessly-monitor-close-variants-with-this-google-ads-script/)
  - [Vallaeys close variant gists](https://gist.github.com/siliconvallaeys/356b031b5d6da0857b43c35c1ef1ab5d)
  - [Brainlabs search query mining (n-gram)](https://github.com/Brainlabs-Digital/Google-Ads-Scripts)

### Competitor monitoring — free sources
- **Google Ads Transparency Center**: advertiser/creative/date/region. No spend, targeting, or keywords. **No official API.** Scraping is Google ToS gray area.
- **Meta Ad Library API**: as of 2026, only returns political/social-issue ads in EU. Commercial/brand ads are UI-only.
- **Wayback Machine CDX API**: free, no auth, perfect for landing-page diffs over time.
- **Sitemap diffing**: weekly `/sitemap.xml` fetch.
- **Wappalyzer CLI**: open-source, detects competitor tech stack.
- **Free competitor keyword source**: does not exist at acceptable accuracy without paid tools.

### Industry benchmarks — free sources
- [WordStream/LocaliQ 2025 Google Ads benchmarks](https://www.wordstream.com/blog/2025-google-ads-benchmarks): ~20 industries, US-SMB-skewed.
- Private cross-client aggregation: legally OK if MSA permits internal analytics + aggregation/anonymization.

### MCP servers
- [cohnen/mcp-google-ads](https://github.com/cohnen/mcp-google-ads) — Python, FastMCP, read-only.
- [googleads/google-ads-mcp](https://github.com/googleads/google-ads-mcp) — official Google, experimental, Gemini-targeted, read-only.

### Claude API economics
- Sonnet 4.6 pricing $3/M input, $15/M output. Opus 4.7 $5/M input, $25/M output.
- With prompt caching + Batch API: 50-client weekly+monthly cadence is **$10–20/mo on Sonnet baseline**.
- Opus 4.7 tokenizer ~35% heavier per Finout — budget headroom if escalating.

## 3. Practitioner ground truth

### Reddit and PPC community
- "There has yet to be any sort of fully automated campaign that I have ever run that doesn't need guardrails and regular check-ins." — Michelle Morgan (CXL)
- "You'll see really good performance in the first couple of weeks, then a clear drop-off once Google thinks it's learned enough." — Joe Martinez. The "Performance Cliff."
- Industry survey: AI is saving PPC managers only ~5 hours/week. [Search Engine Land](https://searchengineland.com/survey-ppc-is-getting-harder-and-ai-is-only-saving-5-hours-a-week-471364)
- Real time savings: an agency cut weekly reporting from 4 hours to 30 minutes using Claude + MCP. [Search Engine Land — Claude Skills for PPC](https://searchengineland.com/claude-skills-ppc-scalable-systems-474221)
- Most common AI workflow on r/PPC: pull search-term report → identify high-spend-no-conv terms → apply as exact-match negatives.
- "Read access goes wide… write access is where the boring engineering matters."

### YouTube practitioner channels
- **Aaron Young (Define Digital Academy)** — STAB framework: Spending/Segmentation, Targeting, Ads/LP, Bidding. Match optimization effort to where money is going.
- **John Moran (Solutions 8 / Tier 11)** — Six critical campaigns: General, Brand, Competitor, DSA, Remarketing, Display. Hyper-segmentation + SPACs.
- **Paid Media Pros (Morgan & Martinez)** — Algorithm needs guardrails; learning-phase performance cliff.
- **Isaac Rudansky (AdVenture Media)** — Profit-first framing, not metric-first.

### Existing tools — pricing floor and gaps
- **Optmyzr** $209–249/mo entry — rule engine + 50+ recipes. No conversational layer.
- **Adalysis** ~$99–199/mo — 100+ daily audit checks. Surfaces issues; doesn't act.
- **Opteo** ~$129/mo — clean UI, push-live suggestion engine. Lighter on B2B SaaS specifics.
- **NinjaCat** $900–1400+/mo — enterprise reporting + AI Agents. Overkill for boutique.
- **AgencyAnalytics** $79–239/mo per-client — reporting only; scales painfully.

**White space (no tool nails it):**
1. Conversational write-safe agent layer with MCC + approval queue
2. PMax asset-level diagnostic with creative replacement recommendations
3. B2B SaaS pipeline-aware reporting (SQL/MQL/pipeline, not platform KPIs)
4. Close-variant detection at n-gram level with safe auto-negative push
5. Audit-to-action loops (Adalysis surfaces, doesn't act)

### Audit frameworks
- [Adalysis 100+ check list](https://adalysis.com/how-to-audit-a-google-ads-account-the-ultimate-ppc-audit-checklist-2021/)
- [STAB framework](https://www.optmyzr.com/blog/stab-framework-google-ads-optimization/)
- [Bullseye 2026 AI-era checklist](https://bullseyestrategy.com/blog/ppc-audit-checklist/)
- [PPC Hero 6-tip audit](https://www.ppchero.com/need-to-get-under-the-hood-6-tips-for-performing-an-effective-account-audit/)

## 4. Top 10 painful tasks the tool MUST automate (synthesis)

1. Weekly search-term review with n-gram + close-variant detection
2. Client-facing monthly report assembly
3. PMax search-term + channel report digestion (incl. Search cannibalization)
4. Conversion-tracking and EC4L health checks
5. Budget pacing across MCC
6. Anomaly detection on KPIs, especially post-learning-phase
7. Account structure audit (STAB gap analysis)
8. Asset coverage and PMax creative diagnostic
9. Ad-copy testing pipeline (RSA statistical significance)
10. Search term → negative keyword loop with approval queue

## 5. Things that look easy but are traps

- **Auto-applying negatives from STR**: false positives. One bad n-gram can be shared with high-converting queries. Optmyzr warns: "$8,000 of that spend resulted in $14,500 in profit." Always show profit math, never auto-apply.
- **AI-generated RSAs at scale**: generation is easy; brand voice + compliance is the hard part. Build for review with guardrails, not one-shot creation.
- **Fully autonomous bid management**: every practitioner says no.
- **Cross-channel breadth**: tools that go horizontal-first lose Google-Ads-purist credibility (Madgicx, Adzooma).
- **Feature-count competition with Optmyzr**: losing battle. Differentiate on workflow + B2B opinion.

## 6. B2B SaaS-specific patterns

- **57% of every $1 in B2B SaaS PPC goes to non-converting queries** (GrowthSpree's 150+ account analysis).
- **OCT adoption lifts SQL volume 30–50%** at the same spend.
- **90-day conversion window** is the right B2B default.
- **Negative keyword categories** that are reusable across all B2B SaaS clients: jobs/careers, education ("what is", "tutorial"), free/open-source, competitor employees, login/support.
- **Lifecycle stage events** (HubSpot lifecycle, Salesforce Stage Models) should be configurable as conversion uploads with values matching pipeline $.
- **AI-Max / broad-match expansion is dangerous in B2B SaaS** — Google reps push it; tool must auto-detect and alert.
- **Brand vs non-brand separation** matters more than ecommerce — sales needs to know which leads came from intent-driven non-brand search.

## 7. Research limitations to flag

- X.com/manthanguptaa tweet was not retrievable via WebFetch or nitter; cannot include in grounding.
- Reddit/Search Engine Land direct fetches returned 403 in some agent runs; quoted practitioner statements were retrieved via Google-surfaced snippets and secondary citations (Optmyzr, CXL, PPC.land).
- AdPulse close-variant script blog post returned 403 to WebFetch in agent 2; logic was reconstructed from widely-referenced equivalent open-source scripts (Rooijmans, Vallaeys).
- WordStream benchmarks are SMB and US-skewed; for enterprise / non-US clients, treat as directional only.
