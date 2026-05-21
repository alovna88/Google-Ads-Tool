---
name: reddit-ads-campaign-dev-desktop
description: End-to-end Reddit Ads campaign development for B2B SaaS — objective + subreddit research, layered targeting (community / interest / keyword / conversation / custom), campaign structure, ad creative & copy in native voice, Reddit Pixel + Conversions API setup with dedup, bid strategy, scaling framework, and pre-launch QA. Trigger whenever the user mentions Reddit Ads, Promoted Posts, Conversation Placement, Free Form ads, AMA Ads, Reddit Lead Gen, Reddit Pixel, Reddit CAPI, subreddit targeting, Max campaigns, or r/[community] targeting — even if they just say "advertise on Reddit." Optimized for Claude Desktop / Claude.ai (no working-directory or file-write assumptions).
---

# Reddit Ads — Campaign Development

A repeatable workflow for building Reddit Ads campaigns from blank-page to launch-ready. Use it whenever someone asks you to "build a Reddit campaign," "set up Reddit ads," "pick subreddits for [product]," "write a Reddit promoted post," or anything in that orbit.

Reddit is not LinkedIn, Meta, or Google. It has no job-title, seniority, or company-level targeting. The primary lever is **community (subreddit) targeting**, layered with interests, keywords, conversation targeting, and custom audiences. Tone matters more than on any other paid social platform — a creative that wins on LinkedIn will get downvoted into oblivion on Reddit, and downvotes raise your effective CPC across the account because the algorithm reads them as quality signal.

Conversion campaigns on Reddit cost 2–3× more per click than awareness/traffic because the algorithm restricts delivery to higher-intent users. For B2B SaaS the typical sequence is Traffic → Conversion → Retargeting, and the comments section under every promoted post is **part of the ad**: ignoring it raises CPC and damages the brand.

This skill is organized into four phases. Work through them in order, but loop back as needed.

1. **Strategy, community selection & targeting**
2. **Campaign structure**
3. **Ad creative & copy**
4. **Launch checklist & QA**

After launch, the **Scaling Framework** at the bottom governs week-by-week decisions.

## How this skill behaves on Desktop

There is no working directory, no `CLAUDE.md`, no file system. So:

- **All deliverables are inline Markdown** the user can copy-paste into their own docs, briefs, or Ads Manager.
- **Client context is collected in conversation**, not read from a file. If the user hasn't supplied it, ask the four questions in **Inputs to gather** before drafting.
- **No skill chaining.** If the user needs ICP research, competitor monitoring, or a weekly report, that's a separate conversation.

## Inputs to gather

If invoked without enough context, ask these in one shot before drafting anything:

1. **Company + product** — one sentence. What does the user sell?
2. **ICP and ACV** — who's the buyer (role, company size, industry) and what's the annual contract value? (Used to sanity-check budget and bid targets.)
3. **Goal of this campaign** — leads / trials / demos / traffic / brand awareness.
4. **Subreddits the buyer hangs out in** — if they don't know, propose subreddit research as the first deliverable.
5. **Offer / destination** — gated asset, demo page, signup, lead-gen form.
6. **Budget and timeline** — flag if monthly spend is under ~$1,500 for B2B (Reddit needs volume to exit calibration).
7. **Brand voice** — tone, banned phrases, required terms.
8. **Target CAC and primary success metric** — Closed-Won pipeline, SQL volume, MQL volume. Reddit's in-platform CPA is *not* the success metric.

Do not invent business context. If ACV, sales cycle, ICP, or target CAC are missing, stop and ask.

---

## Phase 1 — Strategy, Community Selection & Targeting

### 1.1 Clarify the objective first

The Reddit Ads campaign objective drives optimization, bidding, and available formats. Confirm one before proceeding:

- **Awareness:** Brand Awareness & Reach (CPM bidding)
- **Consideration:** Traffic (CPC); Video Views (CPV)
- **Conversion:** Conversions (requires Reddit Pixel + conversion events); App Installs; Leads (Reddit Lead Generation Ads)
- **Catalog:** Catalog Sales / Dynamic Product Ads (requires product feed)

Map the user's business goal to the right objective. "Demo bookings" → Conversions with pixel firing on `/demo-confirmation`. "Trial signups" → Conversions with signup-complete event. "Eyes on our launch" → Brand Awareness & Reach. Don't assume.

**Profit framing reminder.** Optimization metric should always reconcile to CAC, LTV:CAC, or pipeline $. Reddit's in-platform CPA is not the success metric — Closed-Won attribution is.

### 1.2 Subreddit research — the most important step

Reddit doesn't sell access to "VPs of Engineering at 500-person SaaS companies." It sells access to communities where those people argue about tooling. Community selection is the single biggest performance driver on Reddit, ahead of creative and bidding.

**Research process (do this before opening Ads Manager):**

1. **Start with the buyer's vocabulary.** What problem do they search for? What competitor do they complain about? Search those terms in Reddit's native search; record every relevant community in the top organic results.
2. **Triangulate via competitors.** Search "[competitor name]" and "[competitor] alternative" — note which subs surface.
3. **Lurk before targeting.** Read the top 20 posts of the last 30 days in each candidate sub. Confirm (a) audience matches ICP, (b) the sub allows promotional content (some ban it outright), (c) the tone is something the ad creative can match.
4. **Check size and activity.** Subreddits need **5,000+ subscribers** to be eligible for targeting. Smaller, high-intent communities (10k–200k members) often beat the giants for B2B. Look for daily posting cadence and a healthy comment-to-post ratio.
5. **Build a shortlist of 5–15 subreddits per ad group.** Don't stuff 50 subs into one ad group — you lose visibility into which one is working.

**B2B SaaS reference communities (verify each is still active and on-topic before targeting):**

- Developer / DevOps: r/devops, r/sysadmin, r/kubernetes, r/programming, r/aws, r/AZURE, r/googlecloud, r/SRE, r/PlatformEngineering, r/docker, r/terraform
- Engineering leadership: r/ExperiencedDevs, r/cscareerquestions (with care), r/EngineeringManagers
- Security: r/cybersecurity, r/netsec, r/AskNetsec
- Data: r/dataengineering, r/MachineLearning, r/datascience
- Business / founder: r/startups, r/Entrepreneur, r/SaaS, r/B2BMarketing, r/marketing, r/sales, r/RevOps
- FinOps / Finance ops: r/FinOps, r/financialindependence (consumer angle only)

These are starting points, not a final list. Always validate by lurking.

### 1.3 Targeting layers (Reddit Ads Manager fields)

In order of typical importance for B2B:

- **Communities (subreddits)** — primary lever. OR logic within the field.
- **Keywords** — recently-discussed words and phrases in posts and comments. Reddit reports ~30% higher CTR vs community or interest targeting. Best for competitor and category capture (e.g. "kubernetes cost", "karpenter", "spot instances").
- **Conversation targeting** *(Reddit's newest layer)* — analyzes sentiment and context of discussions. Reach users in positive conversations about a topic, or users expressing frustration with a named competitor. Use after community targeting is validated.
- **Interests** — broader Reddit-defined categories (e.g. "Technology & Programming"). Use as a fallback to widen reach when community targeting under-delivers.
- **Custom audiences** — uploaded customer lists (matched anonymously), website visitors via Reddit Pixel, engagement audiences from prior ads. **Always upload a customer-exclusion audience.**
- **Lookalike audiences** — built from a custom-audience seed. **Minimum seed: 1,000 users.**
- **Demographics** — location (country, region, US DMA), gender. No age, no job title, no company.
- **Devices** — iOS, Android, Desktop. B2B campaigns typically see better lead quality from Desktop.
- **Placements** — Feed, Conversation Placement, or both. Conversation Placement (ads inside comment threads) often outperforms Feed for B2B because users are mid-research; running both lowers blended CPM.
- **Time of Day / Day Parting** — useful for B2B (working hours, weekdays).

**Targeting hygiene rules:**

- Keep each ad group on **one targeting method** (community OR interest OR keyword OR custom audience OR conversation). Mixing them destroys attribution.
- Use **Brand Safety** controls to exclude communities you don't want to appear in and to block sensitive keywords.
- Exclude existing customers via custom-audience upload (always).
- Toggle "Automated targeting" **OFF** for first launch. Re-enable only if delivery is healthy after week 2.

### 1.3a Targeting architecture — the 5-ad-group pattern

For a typical B2B conversion campaign, structure the ad groups as five layers with distinct intent and distinct bids:

```
Ad Group 1: "Core Communities"     — 5–8 highest-intent subreddits           (highest bid after retargeting)
Ad Group 2: "Adjacent Communities" — 10–15 related subreddits                (mid bid)
Ad Group 3: "Keyword Capture"      — 15–25 high-intent keywords              (mid-high bid; often best ROI)
Ad Group 4: "Conversation"         — competitor frustration / category sentiment (mid bid; new layer)
Ad Group 5: "Retargeting"          — pixel audiences, site visitors          (highest bid)

Optional once validated:
Ad Group 6: "Interest Expansion"   — 2–3 broad interest categories           (lowest bid)
Ad Group 7: "Lookalike"            — built from converters seed              (mid bid)
```

Set different bid levels per ad group so you can read which layer is actually moving the needle. Never collapse two layers into one ad group.

**Output for this phase:** an audience brief, one block per ad group, delivered inline:

```
Audience name:     [e.g., "DevOps practitioners researching K8s cost"]
Targeting type:    [Communities / Interests / Keywords / Custom / Lookalike / Conversation]
Targeting values:  [list]
Location:          [countries]
Devices:           [if filtered]
Placement:         [Feed / Conversation / Both]
Exclusions:        [customers, competitors, sensitive keywords]
Estimated reach:   [from Ads Manager forecast — user supplies after they check]
```

### 1.4 Budget & bidding

Reddit's $5/day platform minimum is not a viable B2B testing budget. Defaults:

- **Daily budget per ad group:** $25–$50 minimum to give the algorithm enough impressions to optimize. $50–$100 once a campaign is winning and you're scaling.
- **Total monthly minimum for a real B2B test:** ~$1,500. Flag if the user's stated budget is below this.

**Bid strategies:**

| Strategy | How it works | When to use |
|---|---|---|
| **Lowest Cost / Maximum Delivery** | Reddit optimizes for max conversions within budget | Default starting point for weeks 1–2. Lets the algorithm discover baseline CPA. |
| **Cost Cap / Target CPA** | Set target average CPA; Reddit optimizes around it | After 50+ conversion events. Set 10–20% above your observed CPA. |
| **Manual CPC** | Hard CPC cap, full control | Small budgets, or testing new subreddit targets the algorithm has no signal on. |

**Pricing model selection** follows the objective: CPM (awareness), CPC (traffic), CPV (video views), CPA / oCPC (conversions with calibrated pixel). Wrong model → auction optimizes for the wrong metric.

**Schedule:** Run continuously. Reddit recommends maintaining stable campaigns for **14 days** following creation or major edits for proper model calibration. Avoid changes inside the learning window.

**Max campaigns (AI-powered, available 2026):** Reddit's Max campaigns auto-optimize targeting, bidding, and placements. Reddit's internal data shows lower CPA and more conversions vs manual at equivalent budget. Consider Max for: advertisers new to Reddit, broad conversion objectives, or scaling beyond manual optimization limits. **Do not** use Max as the first campaign — you need manual data first to set expectations and validate the pixel.

---

## Phase 2 — Campaign Structure

### 2.1 Naming convention

Use this format unless the user has their own:

```
[Objective]_[Funnel Stage]_[Targeting type + value]_[Geo]_[Format]_[Date]

Examples:
Conv_MOFU_Communities-DevOps_US_PromotedPost_2026-05
Traffic_TOFU_Keyword-K8sCost_US-CA-UK_Video_2026-05
```

For ad-level names, append the creative variant:

```
Conv_MOFU_Communities-DevOps_US_PromotedPost_2026-05_HeadlineA_Screenshot
```

### 2.2 Account hierarchy

Reddit structure: **Account → Campaign → Ad Group → Ad**.

- **Campaign** = one objective + one budget umbrella. Aligns to a coherent initiative (e.g. "Q2 2026 K8s Cost Report launch").
- **Ad Group** = one targeting method (one subreddit cluster, OR one keyword set, OR one custom audience, OR conversation). Never mix targeting methods inside an ad group.
- **Ad** = one creative variant. Run 3–5 ads per ad group for testing.

Reddit's Ads Manager is less flexible than LinkedIn or Meta — keep the structure simple and clean.

### 2.3 A/B testing setup

Reddit doesn't have native split testing. Structure tests manually:

- **One variable per test** (headline OR image OR community OR offer — never multiple at once).
- Duplicate the ad group, change only the test variable, run in parallel with equal budgets.
- Minimum test duration: **14 days** to clear the algorithm's calibration window. Minimum volume: **500 clicks per variant** before declaring a winner.
- Don't judge an ad before ~5K impressions or 100 clicks per variant — Reddit's auction has high short-term variance.

### 2.4 Tracking — Pixel + CAPI, always both

Before any campaign goes live, both client-side and server-side tracking must be in place. Combining Pixel + CAPI reduces CPA materially (Reddit's reported figures: ~25% lower CPA, ~35% more unique converters) because CAPI catches the 30–40% of events the pixel misses to ad-blockers and privacy settings.

**Reddit Pixel (client-side).** Wrap the snippet below in a script tag in the page head, site-wide. Verify with the Reddit Pixel Helper Chrome extension before launch.

```javascript
// Base pixel — wrap in a script tag in the page head
!function(w,d){if(!w.rdt){var p=w.rdt=function(){p.sendEvent?
p.sendEvent.apply(p,arguments):p.callQueue.push(arguments)};
p.callQueue=[];var t=d.createElement("script");
t.src="https://www.redditstatic.com/ads/pixel.js";t.async=!0;
var s=d.getElementsByTagName("script")[0];
s.parentNode.insertBefore(t,s)}}(window,document);

rdt('init','YOUR_PIXEL_ID', {
  optOut: false,
  useDecimalCurrencyValues: true
});
rdt('track', 'PageVisit');
```

**Standard events to instrument** (map to your CTA destinations — do not invent events):

```javascript
rdt('track', 'PageVisit');
rdt('track', 'ViewContent');
rdt('track', 'Search');
rdt('track', 'AddToCart');
rdt('track', 'Lead');
rdt('track', 'SignUp');
rdt('track', 'Purchase', {
  value: 99.99,
  currency: 'USD',
  transactionId: 'ORDER-123',
  conversionId: 'conv_abc123'   // SAME id sent via CAPI for dedup
});
rdt('track', 'Custom');
```

**Reddit Conversions API (server-side).** Required as a redundant layer for any Conversion objective.

```python
import requests, hashlib, time

def send_reddit_conversion(pixel_id, access_token, event):
    """POST a conversion event to Reddit's CAPI. Hash PII per Reddit spec."""
    url = f"https://ads-api.reddit.com/api/v2.0/conversions/events/{pixel_id}"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    email_hash = (
        hashlib.sha256(event["email"].lower().strip().encode()).hexdigest()
        if event.get("email") else None
    )
    payload = {"events": [{
        "event_at": int(time.time()),
        "event_type": {"tracking_type": event.get("event_type", "Purchase")},
        "user": {
            "email": email_hash,
            "external_id": event.get("external_id"),
            "ip_address": event.get("ip"),
            "user_agent": event.get("user_agent"),
        },
        "event_metadata": {
            "item_count": event.get("item_count", 1),
            "value_decimal": event.get("value"),
            "currency": event.get("currency", "USD"),
            "conversion_id": event.get("conversion_id"),  # MUST match pixel id for dedup
        },
    }]}
    return requests.post(url, json=payload, headers=headers).json()
```

**Deduplication.** Pass the same `conversion_id` in both the pixel call and the CAPI call. Reddit uses it to dedupe; without it you double-count.

**UTMs.** Every destination URL gets:

```
?utm_source=reddit
 &utm_medium=paid-social
 &utm_campaign=[campaign-name]
 &utm_content=[ad-variant]
 &utm_term=[subreddit-or-audience]
```

**Conversion window.** Reddit's default is **7-day click + 1-day view** for most objectives; the platform also supports **7-day click + 7-day view**, which is the better default for B2B (most Reddit-driven purchases happen within 10 days of exposure). For long B2B sales cycles, in-platform CPA still won't capture full-funnel impact — supplement with post-conversion "How did you hear about us?" survey + capture Reddit's `rdt_cid` into the CRM, then reconcile against Closed-Won later.

**One Reddit Pixel per ad account.** Multiple sites → segment via URL parameters or event metadata, not separate pixels.

---

## Phase 3 — Ad Creative & Copy

### 3.1 Reddit's iron rule: native voice or die

Reddit punishes corporate language faster than any other platform. The comments section is part of the ad — a downvoted, mocked thread tanks performance and signals to Reddit's algorithm that your creative is low quality, which raises your CPC across the account.

The test before writing any Reddit ad: **if this exact copy could run unchanged on LinkedIn or Meta, it's not ready for Reddit.**

What works:

- Problem-first openings written in the subreddit's vernacular
- Specific, verifiable claims (numbers, screenshots, named tools)
- Conversational tone, sentence length matching organic posts
- TL;DR at the top of longer ads (Free Form format)
- Transparent positioning ("Yes, this is an ad. Here's why we built this thing.")
- First-person, slightly informal, occasionally self-deprecating

What kills the ad:

- "Revolutionize / disrupt / unleash / leverage / transform / next-generation" and similar buzzwords (cross-check against the brand voice the user supplied)
- Stock photography, especially handshake/team/laptop clichés
- Hard sells before trust ("Book your demo today!" on cold audiences)
- Mismatch between subreddit tone (r/sysadmin is dry; r/startups is hopeful) and creative tone
- "BUY NOW", "LIMITED TIME", "DON'T MISS OUT" energy
- Sender account with low/zero karma — Redditors notice and distrust

### 3.2 Format selection & specs

| Format | Best for | Key specs |
|---|---|---|
| **Promoted Post — Image** | TOFU/MOFU, workhorse | 1:1 (1080×1080) or 4:5 (1080×1350) preferred; also 4:3, 16:9. JPG/PNG/GIF (GIF → still thumbnail). Max 3 MB. |
| **Promoted Post — Video** | Demos, walkthroughs | 1:1, 4:5, 4:3, 16:9. MP4/MOV, ≤30 FPS. Max 1 GB (≤512 MB recommended). 5–30 s ideal; up to 15 min allowed. Autoplay muted — front-load message in first 3 s. Captions required. |
| **Carousel** | Multi-feature / sequential narrative | 2–6 cards at 1200×1200. JPG/PNG/GIF. Max 20 MB/card (3 MB recommended). 50-char caption per card. Each card must stand alone — users don't always swipe. |
| **Text Ad** | Native-feeling discussion-style promotion | Headline ≤300 chars (keep under 100). Body up to 40,000 chars (rich text). Blends into organic. |
| **Free Form Ad** | MOFU/BOFU thought leadership, technical subs | Long-form native rich text + images. Best Reddit-only format. Lead with TL;DR. |
| **Conversation Placement** | Layered with other formats — not standalone | Ad appears inside comment threads. Headline **≤100 chars mobile / ≤250 chars desktop**. Thumbnail 400×300 px, ≤500 KB. Combine with Feed for lower blended CPM. |
| **Reddit Lead Gen Ad** | Conversions where LP friction kills CVR | Native form, pre-filled where possible. Lower lead quality than landing-page traffic — add 1–2 qualifying questions. |
| **AMA Ads / Reminder Ads** | Event-driven, beta launches | Use only when you have a real AMA or scheduled event. |
| **Dynamic Product Ads (DPA)** | Catalog / e-comm | Auto-generated from product feed. Reddit's tests show meaningfully higher ROAS vs standard conversion campaigns. |
| **Takeover (Managed / Premium)** | Large brands, major launches | Reddit / Front Page / Category takeover. 24-hour position. Banner 300×250 or 300×600 px, JPG/PNG, ≤150 KB. Requires managed-service sales contact. |

**Headline character limits across placements** — always design for the strictest:

- **Feed:** 300 chars hard cap, keep under 150 for full visibility, **under 100 for mobile**
- **Conversation placement:** 100 chars mobile / 250 chars desktop
- **If running both placements (recommended for B2B):** keep headline ≤100 chars

For B2B SaaS specifically, the highest-leverage starting combo is **Promoted Post (image with product screenshot or data viz) + Free Form Ads in technical subreddits**.

### 3.3 Copy structure

Every Promoted Post has three components:

**1. Headline** (visible everywhere) — Lead with the reader's problem, not the product. Mirror how organic posts in the target sub are titled. Respect the strictest character cap in §3.2.

**2. Body / Description** — Conversational, specific, evidence-backed. Match the technical density of the target subreddit. Cite numbers, name competitors honestly, link to a gated asset or specific landing page.

**3. CTA button.** Pick from Reddit's predefined list and choose the one that matches the offer **literally** — "Learn More" underperforms specific CTAs:

```
Learn More · Sign Up · Download · Shop Now · Get Quote · Apply Now ·
Install Now · Contact Us · Subscribe · Watch More · Get Showtimes ·
View More · Visit Site · Order Now · Get Offer · Book Now
```

### 3.4 Copy patterns that work on Reddit

**Pattern — Specific pain → Specific fix → Optional ask**
```
Headline: "Tired of OOM-killed pods at 3am? We built a tool that re-rightsizes before the page goes off."
Body:     [2–3 lines of specifics; link to the gated asset or product]
CTA:      Download / Learn More
```

**Pattern — Counterintuitive data + invitation to discuss**
```
Headline: "We analyzed 200 K8s clusters. 67% are over-provisioned by 2x+. Here's the breakdown."
Body:     [Report summary; TL;DR with key stat]
CTA:      Download / View More
```

**Pattern — Honest acknowledgment + value upfront**
```
Headline: "Yes, this is a Cast AI ad. Free K8s cost report (no email required) below."
Body:     [What's in it for the reader]
CTA:      View / Learn More
```

**Headline frameworks that travel across categories:**

```
"I built [thing] because [authentic reason]. Here's what I learned."
"[Specific number] [thing] that actually [desirable outcome]."
"We asked [community-relevant group] about [topic]. The results surprised us."
"[Product] for people who [relatable pain point]."
"Honest take: [category] is broken. Here's our attempt to fix it."
```

Cross-check every variant against the brand-voice constraints the user supplied (banned phrases, required terms) before shipping.

### 3.5 Visual brief

For every ad the creative brief specifies:

- **Aspect ratio:** 1:1 (1080×1080) or 4:5 (1080×1350) for image; 4:5 vertical or 16:9 for video.
- **Visual style:** Screenshots, data visualizations, product UI — not stock photography. Reddit users react badly to glossy marketing visuals.
- **Text on image:** Sparingly. The headline is already text. If there must be text on the visual, make it look like a callout, not a billboard.
- **Brand:** Logo present but de-emphasized. Reddit prefers the message over the brand.
- **Thumbnail (where used):** 400×300 px, 4:3, ≤500 KB.

### 3.6 Variant generation

When asked to "draft the ads," produce **3–5 variants per ad group**, varying ONE element across them so the test is clean. Default split:

- 2 headline variants (different angle: pain vs. data vs. transparency)
- 2 body variants (different proof angle)
- 1 creative concept variant (screenshot vs. data visualization vs. unpolished sketch)

Label each variant clearly so they map to the naming convention in §2.1.

---

## Phase 4 — Launch Checklist & QA

Walk this checklist with the user before going live. Skipping it is the #1 way to burn budget on Reddit, where CPCs in competitive B2B niches can hit $4+.

### 4.1 Tracking & measurement

- [ ] Reddit Pixel installed sitewide; verified firing via Reddit Pixel Helper
- [ ] Reddit Conversions API (CAPI) configured server-side as redundancy
- [ ] Same `conversion_id` passed by pixel and CAPI for deduplication
- [ ] Conversion events defined and tested for every CTA destination (PageVisit, Lead, SignUp, Purchase, or Custom)
- [ ] UTMs present on every destination URL, aligned to naming convention
- [ ] If using Lead Gen Ads: CRM integration tested (Zapier / native / API); test lead submitted and routed correctly
- [ ] Conversion window set (7-day click + 7-day view recommended for B2B)
- [ ] Reddit's `rdt_cid` captured into CRM for Closed-Won attribution

### 4.2 Targeting

- [ ] Each ad group uses ONE targeting method
- [ ] Subreddit shortlists validated (lurked the top 20 organic posts; promo-content allowed; ≥5,000 subscribers)
- [ ] Brand Safety community + keyword exclusions applied
- [ ] Custom audience uploaded for **customer exclusion** (always)
- [ ] "Automated targeting" toggled OFF for first launch
- [ ] Location matches intent (don't accept default if the offer is regional)
- [ ] Placement: Feed + Conversation Placement enabled for B2B unless there's a reason to split
- [ ] Retargeting ad group seeded with pixel audience (will become useful from week 2)

### 4.3 Budget & bidding

- [ ] Daily ad group budget ≥ $25 (test) or ≥ $50 (scaling)
- [ ] Monthly budget ≥ ~$1,500 for a real B2B test (flag otherwise)
- [ ] Bid strategy matches objective and conversion-data maturity (Lowest Cost to start; Cost Cap / Target CPA after 50+ events)
- [ ] Pricing model matches objective (CPM/CPC/CPV/CPA)
- [ ] Campaign end date set or explicitly left open
- [ ] Account billing method confirmed active

### 4.4 Creative & copy

- [ ] Every ad has headline, body, CTA filled in
- [ ] Headlines respect the strictest placement cap (≤100 chars if running Conversation Placement)
- [ ] Spell-check, brand/product capitalization verified
- [ ] **Native-voice check:** read the top 20 organic posts of the target sub; does the ad read like one of them?
- [ ] **Buzzword scrub:** no "revolutionize / disrupt / unleash / leverage / transform / next-generation"; reconciled against the brand voice the user supplied
- [ ] Landing page matches ad promise (same offer, same language)
- [ ] Landing page loads under 3 seconds on mobile and desktop
- [ ] Images at correct aspect ratio (no awkward crops in both Feed and Conversation previews)
- [ ] Video has captions and front-loaded message
- [ ] Sender account associated with the ad has reasonable karma

### 4.5 Approvals (draft, don't apply)

- [ ] Internal stakeholder sign-off on creative + copy (marketing lead, brand, legal if regulated)
- [ ] Client sign-off (written) on creative, targeting, and budget
- [ ] Budget approved
- [ ] Skill output is a **draft** delivered inline as Markdown. The human applies it in Reddit Ads Manager. **The skill never pushes live.**

### 4.6 Comment monitoring plan — Reddit-specific, do not skip

The thread under your ad is public, indexable, and influences how every subsequent viewer interprets the ad. Plan moderation **before launch**:

- **Day 1–3:** Check comments every 4–6 hours during target audience working hours. Respond to genuine questions; do not engage trolls.
- **Brand voice in replies:** same conversational tone as the ad. No corporate replies. Honest answers to criticism beat defensive PR.
- **Escalation policy:** decide in advance which categories of criticism require a product/exec response vs. a marketing reply vs. ignore.
- **Hiding vs. responding:** Reddit lets you hide hostile comments under your ads. Use sparingly — hiding obvious bad-faith is fine; hiding legitimate criticism reads as cowardly and Redditors notice.

### 4.7 Post-launch monitoring plan

- **Day 1–3:** Delivery, frequency, upvote/downvote ratio, comment quality. Pause anything getting brigaded.
- **Day 7:** First optimization check — pause clear underperformers (CPC over 2× benchmark, CTR under 0.3% on Feed). Don't make material changes inside the 14-day learning window unless an ad is actively damaging the brand.
- **Day 14:** Full performance review against KPIs. First valid optimization point per Reddit's calibration window.
- **Day 30:** Decide refresh, scale, or kill. Refresh creative every 10–14 days regardless — Reddit fatigue is faster than Meta or LinkedIn because users visit the same communities daily.

---

## Scaling Framework

Once the campaign is live, governance moves to this three-phase loop.

```
Phase 1 — Validate (Week 1–2)
├── 3–5 ad groups, 3–5 creatives each
├── Lowest Cost bidding
├── $50–$100/day total
├── No changes inside the 14-day learning window
└── Goal: identify ≥2 ad groups with in-platform CPA < target

Phase 2 — Optimize (Week 3–4)
├── Pause underperforming ad groups and ads
├── Add 2–3 new creative variations on winners
├── Switch top performers to Cost Cap / Target CPA (set 10–20% above observed CPA)
├── Scale budget by ≤20% per step on winners
└── Goal: consistent CPA at scale; first reconciliation against Closed-Won

Phase 3 — Scale (Month 2+)
├── Expand into interest + keyword targeting
├── Launch lookalike audiences from the converters seed (≥1,000)
├── Add conversation targeting (competitor frustration, category sentiment)
├── Test Max campaigns for incremental reach (do not replace manual yet)
└── Goal: 3× budget while keeping CAC within 20% of target
```

**Reference benchmarks (Reddit, across industries — verify against the client's own data before relying):**

- CTR: 0.3%–1.5% (varies heavily by subreddit and creative)
- CPC: $0.20–$4.00
- CPM: $0.50–$15.00 (as low as $0.20 in niche subreddits)
- CVR: 1%–5% for considered purchases

Benchmarks are sanity checks, not targets. Targets come from the user's stated CAC / pipeline goal.

---

## When the user gives you a vague brief

If they say "build me a Reddit campaign for our new product," don't draft — interview first using the questions in **Inputs to gather**. Once you have answers, produce a one-page campaign brief covering Phases 1–3, then walk the launch checklist.

---

## Output formats (inline Markdown)

**Campaign brief** — when the user asks for a plan, deliver inline in this structure (the user copy-pastes it into their own docs):

```
# [Campaign Name]

## Objective
[One line — and the in-platform optimization metric it implies]

## Subreddit shortlist
[5–15 subs with rationale; flag any with promo-content bans or under 5K subscribers]

## Audiences / Ad Groups
[One block per ad group, one targeting method each, per §1.3 format]

## Structure
- Campaign: [name + objective]
- Ad Groups: [list with targeting + format + bid level]
- Ads per ad group: [count + what varies]

## Budget & Bidding
[Daily budget per ad group, total budget, bid strategy, pricing model, duration]

## Creative Brief
[Ad variants per ad group with headline / body / CTA / visual direction]

## Tracking
[Pixel status, CAPI status, conversion events, UTM template, conversion window]

## Launch Checklist
[Inline reference to §4]

## Comment Monitoring Plan
[Cadence + escalation policy]

## Success Metrics
[Primary KPI in CAC / pipeline $ terms; secondary KPIs in Reddit-platform terms]

## Top 3 actions for this week
1. [Most important next step]
2. [Second]
3. [Third]
```

**Ad copy deliverable** — when the user asks just for the ads, deliver as a Markdown table:

| Variant | Headline | Body | CTA | Visual direction | Subreddit fit notes |
|---|---|---|---|---|---|
| A | … | … | … | … | … |

**Targeting + structure table** — when the user is ready to push to Ads Manager, deliver as a Markdown table they can paste into a spreadsheet:

| campaign_name | ad_group_name | targeting_type | targeting_values | location | devices | placement | exclusions | daily_budget_usd | bid_strategy | pricing_model |
|---|---|---|---|---|---|---|---|---|---|---|

---

## Things to avoid

- Stuffing 50+ subreddits into one ad group — kills attribution to specific communities.
- Mixing community + interest + keyword targeting in a single ad group — same problem.
- Recycling LinkedIn/Meta creative verbatim — Reddit users will downvote on sight, and the downvotes raise your effective CPC.
- Launching without **both** the Reddit Pixel and CAPI — you'll be running blind on 30–40% of conversions.
- Forgetting the `conversion_id` dedup key between Pixel and CAPI — you'll double-count.
- Judging an ad's performance before 14 days or 500 clicks per variant — Reddit's auction has high short-term variance.
- Ignoring the comment section — silent criticism becomes visible criticism fast.
- Hard-selling on cold audiences — Reddit users are researchers, not buyers. Lead with value.
- Targeting r/all or only the biggest subs — niche, high-intent subs (10k–200k members) consistently outperform giants for B2B.
- Setting daily budgets under $25 — Reddit's algorithm needs volume to optimize delivery, and tiny budgets often underspend or fail to exit calibration.
- Forgetting to exclude existing customers — wastes budget and erodes goodwill in communities.
- Launching Max campaigns as the first campaign — you need manual data first to set realistic CPA expectations.
- Reporting Reddit's in-platform CPA as the success metric — the real metric is CAC against the user's stated target.
