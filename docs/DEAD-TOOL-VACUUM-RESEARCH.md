# LaunchLook — Dead-Tool Vacuum Research

*Research date: May 25, 2026 · Compiled by vacuum-hunt worker · Audience: Rob (founder)*

> Companion read to `COMPETITIVE-INTEL.md`. That doc maps **live competitors**. This doc maps **dead, stripped, or priced-out tools whose audience is still mid-air** — and asks where LaunchLook's existing pipeline can land underneath them in days to weeks of build work, not months.

---

## 1. Executive summary

The vacuums LaunchLook can actually fill are not the famous corpses. Google Optimize's audience was loud but has already been swallowed by VWO, Statsig, GrowthBook, Mida and a dozen no-code lookalikes — and A/B testing is the wrong shape of product for a pre-launch audit anyway. Hotjar (now Contentsquare) is getting expensive but Microsoft Clarity ate that vacuum free-forever. The most useful finding from a week of searches is the **second-tier** graveyard: tools where the audience was always non-technical, the product was always solo-founder-priced, and the replacements are CLI-only OSS projects nobody installs.

**Top 3 vacuums LaunchLook could fill in under two weeks of build, with evidence:**

1. **Plain-English Core Web Vitals findings.** The Web Vitals Chrome extension was officially ended January 13, 2025, merged into Chrome DevTools. Non-technical builders are now staring at "LCP 4.1s — opportunity: reduce unused JavaScript" with no translator. PageSpeed Insights API is free (25,000 calls/day). LaunchLook adds one finding category, one prompt, one PSI call — 2-3 days.
2. **Non-technical site crawl + broken-link audit.** Screaming Frog's "free" tier is 500 *resources* (≈50 real pages) and the UI famously intimidates non-technical buyers; W3C Link Checker is effectively abandoned; replacement tools (linkinator, FreeCrawl, LibreCrawl) all ship as CLIs. LaunchLook already crawls one URL with Playwright. Extend to a 25-50 page crawl + dedicated broken-link findings category = ~1 week.
3. **Validates an existing queued bet: visual regression / "Confidence Check" re-scan.** Percy ($500+/mo), Chromatic ($149/mo), and Applitools ($1K+/mo) priced out solo founders; the OSS replacements (Lost Pixel, Lastest, Sentinel, DojoWatch) require CI knowledge no vibe coder has. LaunchLook already captures desktop + mobile screenshots; bolting on perceptual diff + LLM annotation between two scans is the planned "Send in the Saboteur" feature. The vacuum confirms this should ship before "Watch."

**The single highest-leverage move:** Ship the Core Web Vitals translator (#1 above) as a new finding category this week. It is 2-3 days of work, fills a vacuum opened January 2025 that none of the AI-audit competitors (PageLens, VibeDoctor, SchemaReports, AuditAI) currently address in plain language, and compounds naturally with the queued security-lite work since both rely on the same "translate jargon → action" wedge.

**Vacuums that looked good but actually got filled or aren't worth chasing:** A/B testing (filled by VWO + Statsig + dozens of no-code lookalikes), Hotjar replacement (Microsoft Clarity is free forever — do not touch), GEO / AI-visibility tracking (Lorelight founder shut his own product down October 31 2025 saying "the problem didn't need solving"), generalist SEO audits (PageSpeed/Ahrefs Free/SEODiff already free), heatmap-style observation (Clarity again).

---

## 2. Vacuum candidates table

| # | Tool | Status | Original use case | Audience stranded | Evidence of orphaned demand | Closest current alternative | Could LaunchLook fill? | Build cost | Demand signal |
|---|------|--------|-------------------|-------------------|-----------------------------|-----------------------------|-----------------------|------------|---------------|
| V1 | **Google Optimize** | Dead — sunset Sept 30, 2023 | Free A/B testing + visual editor with native GA integration | 2-3M sites; mostly solo founders + SMB | ExperimentHQ, RunPivot, Blazeway, Mida, SplitLP all built explicitly to capture refugees; goprecision.co [confirms](https://goprecision.co/blog/google-optimize-alternatives/): "no free alternative has matched Optimize's native integration with Google Analytics"; "many simply stopped running experiments altogether" | VWO ($10K+/yr), Statsig (free for devs), GrowthBook (OSS, dev-bound), Blazeway/SplitLP free tiers | **No.** Different infra (continuous experimentation), wrong audience job (ongoing CRO vs. pre-launch audit) | n/a | Real but filled |
| V2 | **Pingdom free tier** | Dead — killed post-SolarWinds acquisition, no free plan as of 2026; cheapest now $15/mo for 10 monitors | Free site uptime monitoring | Indie devs, solo founders, agency freelancers | [notifier.so guide](https://notifier.so/guides/free-pingdom-alternative/): "Pingdom eliminated their free plan entirely... If you're an indie developer, small business owner, or just someone who wants to know when their website goes down without paying enterprise prices, you need a free Pingdom alternative" | UptimeRobot (now non-commercial only), Better Stack, HetrixTools, Uptime Kuma (self-host) | **Partial — already queued as Watch.** Continuous monitoring is a v2 / subscription play; current LaunchLook is one-time audit | Medium (cron + status pages = 2-4 weeks) | Real, validated by competing entrants |
| V3 | **UptimeRobot free tier** (commercial use) | **Free tier restricted to non-commercial only as of October/November 2024** | Free uptime monitoring with 50 monitors / 5-min checks | Solo SaaS founders, e-commerce micros, anyone with a paid product | [notifier.so](https://notifier.so/guides/uptimerobot-alternative/): "In October 2024, UptimeRobot changed their terms to limit the free plan to non-commercial use only. If you're monitoring a business website, SaaS product, or anything that generates revenue, you technically need a paid plan ($9/month minimum)"; [dev.to migration guide](https://dev.to/velprove/freshping-shut-down-7-best-free-alternatives-for-2026-with-migration-guide-hbf) cites this as a freshly-broken trust event | Notifier.so, Better Stack free, HetrixTools 15 monitors free, Uptime Kuma self-host | **Same as V2** — feeds into queued Watch tier | Medium | Real, fresh, loud |
| V4 | **Freshping (Freshworks)** | Dead — confirmed shutdown June 4, 2026; all data deleted post-shutdown | Free uptime monitoring with status pages | Indie devs who couldn't stomach UptimeRobot's commercial-use change | [DEV.to](https://dev.to/velprove/freshping-shut-down-7-best-free-alternatives-for-2026-with-migration-guide-hbf): "Freshping shut down. No new signups, no renewals, free plan access terminated. June 4, 2026. All ping data permanently deleted" | Same as V2/V3 | **Same as V2** | Medium | Real, very fresh |
| V5 | **Hotjar (legacy free tier)** | Sunset — fully merged into Contentsquare July 2025; alleged stealth caps May 2026 | Heatmaps, session replay, surveys for SMB | UX-curious solo founders & affiliate marketers | [Affiliate Times](https://affiliate-times.com/hotjars-alleged-stealth-price-hike-is-rattling-affiliate-tech-stacks/) reports session caps reduced from 500/day to 200-300; Trends module moved to Scale-only; multiple "stealth price hike" complaints since May 2026 | Microsoft Clarity (free forever, unlimited sessions, no caps); FullSession, Quackback comparisons | **No.** Microsoft Clarity has comprehensively eaten this vacuum and is enterprise-backed | n/a | Filled |
| V6 | **Crazy Egg free trial** | Alive but no free plan; 30-day trial only; $29-249/mo annual-only billing | Heatmaps + simple A/B testing | Small marketing teams | [propicked.com](https://propicked.com/marketing/crazy-egg/pricing): "No free plan. All plans billed annually" | Microsoft Clarity | **No** — Clarity wins | n/a | Filled |
| V7 | **W3C Link Checker** | Effectively abandoned — still up but ancient, slow, no maintenance signal | Free broken-link checker for any URL | Non-technical site owners | Recent broken-link tools (linkinator, linkspector, gone, lost-pixel-related) all ship as **CLIs targeting devs**; no clear non-technical web-based winner [[superuser.com thread](https://superuser.com/questions/38428/application-to-check-broken-links)] | linkinator, Linkspector, Dr. Link Check (paid), DeadLinkChecker (limited) | **Yes — already in pipeline.** Findings library covers broken links; just needs to be surfaced as a dedicated category | Days | Real, quiet |
| V8 | **Xenu's Link Sleuth** | Effectively abandoned — Windows-only, last meaningful update years ago | Free desktop broken-link crawler | Non-technical desktop users | Listed in "abandoned tool" Reddit + StackOverflow threads as the canonical example | Same as V7 | **Yes** — same as V7 | Days | Real, quiet |
| V9 | **Screaming Frog free tier** | Alive but effectively useless — 500 *resources* cap means ~50 real pages; £199/yr to unlock | Free technical SEO crawl | Non-technical site owners who need more than 50 pages | [Medium](https://ytguru.medium.com/we-crawled-a-2-million-url-site-my-macbook-nearly-died-33c9e0c39c6f): "the 500-URL limit on the free version isn't really 500 URLs. It's 500 crawled resources... I tested this on a client's 180-page site. The free version tapped out at page 127"; [searchatlas.com 29-alternatives guide](https://searchatlas.com/blog/screaming-frog-alternatives/) reports users seek alternatives because of "scalability issues, 'outdated' user interface, and a lack of built-in executive-ready visualizations" | FreeCrawl (OSS), LibreCrawl (OSS), Sitebulb (paid, 14-day trial), DeepCrawl (enterprise) | **Yes — small extension.** Expand current single-URL Playwright crawler to ~25-50 pages with rate limiting | 1 week | Real, validated |
| V10 | **Lighthouse standalone DevTools panel** | Being sunset H2 2025 — features merged into Performance panel | Free in-browser perf audit | Devs (target) + some non-tech | Chrome's own [transition post](https://developer.chrome.google.cn/blog/perf-tooling-2024): "the independent Lighthouse panel in DevTools will become redundant, and will be sunset"; PageSpeed Insights API and Lighthouse npm remain alive | PSI website, Lighthouse npm, axe-core, Sentry Performance | **Partial** — LaunchLook can pull PSI API and translate, but Lighthouse itself isn't dead | Days | Mixed |
| V11 | **Web Vitals Chrome extension** | **Dead — officially ended January 13, 2025, merged into Performance panel** | Plain-ish Core Web Vitals readings in-browser | Anyone not comfortable in DevTools | Chrome's [end-of-life post](https://developer.chrome.com/blog/web-vitals-extension-merged): "With the release of Chrome 132 this month, the Web Vitals extension has officially merged with the Performance panel in DevTools... we plan to revoke its CrUX API key in the near future, which will break the field data integration" | Chrome DevTools Performance panel (engineer-grade UI), PageSpeed Insights | **Yes — net-new finding category, easy add.** Call PSI API per URL + one LLM pass per metric (LCP/INP/CLS) → plain-English finding with severity + builder fix prompt | 2-3 days | Real, fresh (Jan 2025) |
| V12 | **Mozilla Observatory / SecurityHeaders.com** | Alive but technical-only — no recent UX investment, no translation layer, jargon-heavy reports | Free security-headers grader | Devs (target); non-technical users locked out | [hackit.cloud](https://hackit.cloud/) explicitly positions against them: "They're great tools — for security engineers. hackit.cloud is built for everyone else"; StayAlive, SecurityBot.dev, FortWatch all building translation layers on top | hackit.cloud ($29/mo), SecurityBot.dev (from $5/mo), StayAlive, FortWatch, native Vercel headers | **Yes — already queued as security-lite.** Checks for HSTS, CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy + plain-English finding + paste-ready fix per builder | Days | Real, fresh (multiple paid lookalikes shipping in 2025-2026) |
| V13 | **Percy / Applitools / Chromatic free + low tiers** | Alive but priced out for solo — Percy $500+/mo, Chromatic $149/mo, Applitools $1K+/mo | Visual regression / screenshot diff between deploys | Indie devs + solo founders | [Lastest README](https://github.com/las-team/lastest) and [DojoWatch README](https://github.com/DojoCodingLabs/dojowatch) both lead with "$0 vs. $500-$1K/mo" framing; multiple OSS replacements (Lost Pixel 4 years old, Lastest, Sentinel, Argos) all explicitly position against this pricing | Microsoft Clarity (no), Lost Pixel (CI-bound), Lastest (CI-bound), DojoWatch (CI-bound) | **Yes — already queued as Confidence Check / Send in the Saboteur re-scan.** Existing pipeline captures desktop + mobile screenshots already; add perceptual diff + LLM annotation against prior scan | 1-2 weeks (vs current "out of pipeline") | Real, validated |
| V14 | **Form-submit verification (no clear dead tool, but no non-technical winner)** | Mixed — MoniForm, FormWatch, FormTracker all exist with 1-free-form tiers, all explicitly subscription-led | Verify a contact form actually sends email | Non-technical site owners post-launch | All three explicitly market "your form silently broke and you lost leads" pain — confirms demand exists; no one-off / pre-launch product owns this finding | MoniForm, FormWatch, FormTracker (all subscriptions); manual self-test | **Yes — net-new finding category.** Playwright fills form with synthetic values → submits → checks for thank-you state + (optionally) email round-trip via mailbox API. Adds one finding category | 1-2 weeks | Real, validated |
| V15 | **BrowserStack Freelancer plan ($19/mo)** | Dead — removed April 25, 2026 per BrowserStack pricing-change history; "Free" plan now $25/year, "Unlimited" $39/year | Single-user cross-browser real-device testing | Solo freelancers and small agencies | [PulseSignal price tracking](https://getpulsesignal.com/changes/browserstack): "Freelancer Plan $19/month — Removed; Automate (Chrome Desktop) basic parallel $59/month — Removed... New plan: Free $25/year" | LambdaTest (now TestMu AI) free with limits, Autonoma free web-only, Selenium self-host | **Partial — out-of-band fit.** Real-device farm is heavy infra. LaunchLook can offer "tested on N viewports + N user-agents" via Playwright as a lighter wedge | Days for Playwright UA sweep; weeks for real devices | Real but narrow |
| V16 | **Lorelight (GEO / AI-visibility tracking)** | Dead — founder shut down October 31, 2025 with detailed post-mortem | Track brand mentions in ChatGPT/Claude/Perplexity | SMB marketers chasing AI search visibility | [Founder's own post-mortem](https://growwithless.com/shutting-down-lorelight/): "customers were churning because the product didn't change what they needed to do. The fundamentals remain the same. You don't need a specialized tool"; [Search Engine Land](https://searchengineland.com/geo-startup-lorelight-shuts-down-464208) corroborates | SchemaReports, AuditAI (both still alive but pivoting) | **No.** Lorelight's founder concluded the entire category was a hype cycle. Hordus.ai is repeating the mistake at the enterprise tier. Skip | n/a | Anti-signal |
| V17 | **Lighthouse CI free hosting** | Alive but stripped over time; Lighthouse 13 (Oct 2025) breaks old API consumers | Free CI for perf budgets | Devs running their own CI | Chrome's [Lighthouse 13 announcement](https://developer.chrome.google.cn/blog/moving-lighthouse-to-insights): "some breaking changes for Lighthouse users, especially the API users that may be used to certain audit names or result formats" | PSI API direct, GitHub Actions custom, paid services | **No** — wrong audience (CI users, not vibe coders) | n/a | Wrong audience |
| V18 | **Tota11y / older WAVE Firefox toolbar** | Tota11y abandoned (jdan/tota11y, low recent commits); WAVE Firefox toolbar no longer maintained per WebAIM | Free in-browser accessibility audits | Non-technical users wanting a quick check | [WebAIM blog](https://webaim.org/blog/wave-updates/): "we have decided to no longer update the WAVE Firefox toolbar... we recommend users migrate to the Chrome extension"; tota11y last meaningful release pre-2022 | WAVE Chrome extension (alive), axe DevTools (alive), Stark Figma plugin | **Yes — already implicit in pipeline.** axe-core could plug into existing Playwright capture; produce 3-5 accessibility findings per audit | 1 week | Real, quiet |
| V19 | **Free SEO tools generally (Moz/Ahrefs/SEMrush graveyard)** | Mixed — Moz Free Tools degraded over time; Ahrefs Free re-launched 2024 (5K credits/mo, verified ownership); SEMrush still gated | Free keyword + site audits | Marketers and SMB SEOs | [SEODiff](https://seodiff.io/) and [FreePageRank](https://freepagerank.com) both built free hooks explicitly because "Moz wants signup, Ahrefs caps you, Semrush wants email" | Ahrefs Free, SEODiff, FreePageRank, Launly | **No / partial.** SEO is too crowded a wedge for LaunchLook to chase head-on — see COMPETITIVE-INTEL §4.1 on entrenchment | n/a | Real but crowded |
| V20 | **DownNotifier / IsItDownRightNow consumer side** | Alive, but consumer-facing only (third-party outage status, not your own site) | Tell users if popular services are down | End users, not founders | DownNotifier.com still offers $14.95/yr 10-site monitoring; not a vacuum | Better Stack, UptimeRobot for self-monitoring | **No** — different product | n/a | Not vacuum |

---

## 3. Composite-score leaderboard

Scoring axes (1-5 each, higher = better for LaunchLook):
- **Demand**: How loud, recent, and specific is the orphan signal?
- **Build**: How quickly can LaunchLook's pipeline absorb it? (5 = days; 1 = months of new infra)
- **Fit**: Does this naturally serve vibe-coding pre-launch founders without pulling focus?

| Rank | Candidate (vacuum #) | Demand | Build | Fit | Composite | Status vs roadmap |
|------|---------------------|--------|-------|-----|-----------|-------------------|
| 1 | **Plain-English broken-link audit (V7+V8)** | 3 | 5 | 5 | **13** | In pipeline — surface as a dedicated finding |
| 2 | **Plain-English security-headers audit (V12)** | 3 | 5 | 5 | **13** | **Already queued (security-lite)** — validates |
| 3 | **Non-technical pre-launch crawl (V9)** | 4 | 4 | 5 | **13** | Net-new small extension (25-50 page crawl) |
| 4 | **Re-scan + visual regression (V13)** | 4 | 4 | 5 | **13** | **Already queued (Confidence Check / Saboteur)** — validates |
| 5 | **Core Web Vitals plain-English finding (V11)** | 3 | 5 | 4 | **12** | Net-new, 2-3 days, easy add |
| 6 | **Form-submit smoke test (V14)** | 3 | 4 | 4 | **11** | Net-new, 1-2 weeks, persona-rich |
| 7 | **Accessibility findings via axe-core (V18)** | 3 | 4 | 4 | **11** | Net-new, fits existing pipeline |
| 8 | **Indie commercial uptime monitoring (V2+V3+V4)** | 5 | 2 | 3 | **10** | **Already queued (Watch subscription)** — validates the future tier |
| 9 | **Cross-browser / user-agent sweep (V15)** | 3 | 3 | 3 | **9** | Net-new, narrow appeal |
| 10 | **A/B testing replacement (V1)** | 4 | 1 | 1 | **6** | Skip — wrong product shape |

---

## 4. Top-5 deep dives

### Deep dive 1 — Plain-English Core Web Vitals findings (V11 · composite 12)

**What it left behind.** Chrome killed the Web Vitals extension on January 13, 2025, merging its features into the DevTools Performance panel. Non-technical builders who used to glance at the extension popup for "LCP, INP, CLS" now have to learn DevTools, or read raw PageSpeed Insights output (which speaks engineer: "Largest Contentful Paint element… Eliminate render-blocking resources… 4 KiB savings on unused JavaScript"). PageSpeed Insights itself is alive — the API offers 25,000 free calls/day — but no AI-audit competitor (PageLens, VibeDoctor, SchemaReports, Vibe Code QA) currently translates PSI output into vibe-coder plain English with a builder-specific fix prompt.

**LaunchLook implementation.** Add one PSI API call in `scripts/ai_audit/pipeline.py` (mobile + desktop strategies) after the screenshot pass. Pass the three Core Web Vitals + opportunities into a new `core_web_vitals.txt` prompt that emits a single finding per failing metric, severity-mapped (LCP > 4s = High; INP > 500ms = Medium; CLS > 0.25 = High). Reuse `system.txt`'s fix-prompt-by-builder section so Lovable users get "Add `loading='lazy'` to your hero image" and v0 users get "Use `next/image` with priority on your above-the-fold component."

**Pricing / positioning.** Bundle into Starter ($19) at one Core Web Vitals finding max; Full ($49) at three findings max; Pro ($99) full breakdown + per-page comparison. Adds a Lighthouse-translator angle the competitive set doesn't have. **Why now:** the orphan signal is fresh (Jan 2025) and CrUX API key revocation makes the extension fully broken — anyone who limps along on the old extension will have it die mid-2026.

### Deep dive 2 — Re-scan with visual regression / "Send in the Saboteur" (V13 · composite 13)

**What it left behind.** Percy starts at $500/mo, Chromatic $149/mo, Applitools $1K-2K/mo — pricing built for product teams, not solo vibe coders. OSS alternatives (Lost Pixel, Lastest, Sentinel, DojoWatch, Argos) all ship as CLIs that require Storybook, Playwright config files, or GitHub Actions — exactly the kind of YAML that no-code Lovable/Base44 builders never touch. The audience that needs "did anything break after I told the AI to redesign my hero?" has no productized answer.

**LaunchLook implementation.** Already queued as Confidence Check / Send in the Saboteur per `03-build-queue.md` anti-queue carve-outs. Concrete spec: persist the screenshot set + parsed-HTML snapshot from the original audit to `output/customers/{slug}/baseline/`. On re-scan request, run `scripts/ai_audit/pipeline.py` against the live URL, then `pixelmatch` or `sharp`-based perceptual diff per viewport. Send diffs > 5% pixel-change above a content mask to the LLM as a "regression candidate" finding ("Your pricing page hero shifted 47% — most likely cause: AI builder changed the grid template").

**Pricing / positioning.** $19 add-on to any prior audit; $9 if purchased within 14 days of original. Positions as "Send in the Saboteur" — a Tester from the queued cast that comes back to confirm the AI builder didn't break anything in the last week. **Why now:** every competitor with a re-scan feature (PageLens Weekly Monitor, SchemaReports Pro, VibeDoctor PR integration) is subscription-only; LaunchLook can own the one-off re-scan price point first.

### Deep dive 3 — Plain-English security-headers + secret-scan audit (V12 · composite 13)

**What it left behind.** Mozilla Observatory and SecurityHeaders.com still run, but their reports read like firewall rules ("Add `frame-ancestors 'none'` to Content-Security-Policy"). The vacuum has spawned a wave of paid translators in 2025-2026: hackit.cloud ($29/mo), SecurityBot.dev (from $5/mo), StayAlive ($5-15/mo, bundles uptime + SSL + broken links), FortWatch ($29-99+/mo with AI explanations). Every one explicitly markets against "the leading security tools wanted €300+/month."

**LaunchLook implementation.** Already queued as security-lite per `03-build-queue.md`. Concrete spec: `scripts/ai_audit/security_lite.py` runs five checks per audit: (1) HSTS, (2) CSP presence, (3) X-Frame-Options, (4) X-Content-Type-Options, (5) Referrer-Policy. A sixth check looks for exposed `.env` / `.git` / `/admin` / `firebase` keys in the HTML extract. Each finding includes a builder-specific fix ("Add to your Vercel `vercel.json`: …" / "In Lovable, ask the AI: 'Add a Content-Security-Policy header that allows self plus inline scripts'").

**Pricing / positioning.** Already inside Pro tier ($99); included free in Starter as 1 finding max to position against hackit.cloud's "$29/mo for 1 site" model. Note: do not market against Snyk or Detectify on depth — position as "the security report your non-technical co-founder can read." **Why now:** the lookalike count (hackit, StayAlive, SecurityBot, FortWatch) all shipped 2024-2026 — the buyer pattern is validated. LaunchLook's lever is the founder-curated wrapper, not the depth.

### Deep dive 4 — Non-technical site crawl + broken-link audit (V7+V8+V9 · composite 13)

**What it left behind.** Three orphan signals stack here: W3C Link Checker is effectively unmaintained, Xenu's Link Sleuth is Windows-only and abandoned, and Screaming Frog's "free" tier crawls only ~50 real pages (the 500-resource cap collapses on any site with normal image/JS loading) before the £199/yr paywall. Non-technical alternatives are all CLIs targeting devs (linkinator, linkspector, lychee, gone). The buyer who can't open a terminal has no productized cross-page audit.

**LaunchLook implementation.** Extend `scripts/ai_audit/html_extract.py` from single-URL to BFS-crawl-with-cap (default 25 pages Starter / 50 Full / 100 Pro). Reuse Playwright's existing context. Add a `broken_links` finding category to `06-findings-library.md` keyed off `_PRESCREEN_BROKEN_LINKS` already implied in the regex prescreener; surface as a dedicated severity-Medium finding per dead link. Add a `crawl_summary` finding ("We checked 27 pages of your app and found 4 broken links, 2 missing meta titles, and 1 page with duplicate H1 tags") — sticky and shareable in screenshots.

**Pricing / positioning.** No price change; the depth bump is part of the tier ladder rationale. Internal page count maps cleanly to tier. **Why now:** PageLens AI is already capped at 25 pages on its $29 Launch Pack — matching their ceiling at $19 Starter is a quick wedge. Also blunts the "$49 Olly Roast vs $49 LaunchLook" comparison since Olly only reviews a single landing page.

### Deep dive 5 — Form-submit smoke test (V14 · composite 11)

**What it left behind.** Nobody died here — MoniForm, FormWatch, FormTracker are all alive with free 1-form tiers. But the model is exclusively subscription monitoring, not one-off pre-launch verification. "Did my contact form actually send the email when I launched yesterday?" is a real founder pain (every form-monitor landing page leads with it) and there's no one-off non-technical answer in market.

**LaunchLook implementation.** Add `scripts/ai_audit/form_check.py`: Playwright detects forms on the homepage + contact page + signup page, fills with synthetic safe values ("testname@launchlook.audit"), submits, captures the post-submit DOM. Detects three failure modes: (1) submit button doesn't trigger network call; (2) network call returns 4xx/5xx; (3) page shows generic error or no acknowledgment. Optional email round-trip via a disposable mailbox API in the Pro tier. Single new finding category ("Your signup form submitted but didn't acknowledge — users will assume it broke and bounce") with builder-specific fix prompts.

**Pricing / positioning.** Bundled in all tiers. Adds a persona to the queued "Testers" cast: "The Stranger Who Tried to Sign Up." **Why now:** form-monitoring is a $5-10/mo subscription category — LaunchLook captures the same value at launch as a one-time finding without committing to ongoing monitoring infrastructure. Costs ~1 LLM call extra per audit; near-zero marginal LLM cost.

---

## 5. Cross-check vs. existing build queue

| Top-5 candidate | Already queued? | What this means |
|-----------------|-----------------|-----------------|
| **Plain-English security-headers** | **Yes** — `03-build-queue.md` security-lite | **Validates an existing bet.** Multiple paid lookalikes (hackit.cloud, SecurityBot.dev, StayAlive, FortWatch) confirm the buyer + price point exists. Ship it. |
| **Re-scan / visual regression (Saboteur)** | **Yes** — anti-queue carve-out + `01-product-spec.md` "Follow-up re-scan" | **Validates an existing bet.** Percy/Chromatic/Applitools are explicitly priced out of solo, OSS replacements are CLI-bound. Ship before Watch subscription. |
| **Indie commercial uptime monitoring** | **Yes** — "Watch" subscription tier per `02-strategy-and-context.md` | **Validates the future bet.** Freshping just died (June 2026), UptimeRobot free went non-commercial-only (Oct 2024), Pingdom has no free tier — the demand is loud. But Watch is correctly deferred per `COMPETITIVE-INTEL §4.3`: ship after 100 paying one-off customers ask. |
| **Plain-English Core Web Vitals** | **Net-new** | **Add to roadmap.** 2-3 day build. Fills a January 2025 orphan. Compounds with security-lite (both "translator" plays). |
| **Non-technical 25-50 page crawl + broken-link finding category** | **Partially in pipeline** (single-URL today; broken-link patterns implied in prescreener) | **Net-new small extension.** ~1 week to expand crawler depth + surface findings explicitly. Improves Starter/Full/Pro feature ladder. |
| **Form-submit smoke test** | **Net-new** | **Add to roadmap.** 1-2 week build. Persona-rich; adds a Tester to the cast. |
| **Accessibility findings via axe-core** | **Net-new** | **Add to roadmap.** ~1 week. Touches a quietly-orphaned audience (Firefox WAVE toolbar abandoned, tota11y dormant). |
| **Cross-browser / user-agent sweep** | Out of scope | **Good idea, wrong time.** BrowserStack pricing change is real but the buyer-job (cross-browser real-device parity) is a different product. Defer. |

---

## 6. The "don't bother" list

| Vacuum | Why skip | Evidence |
|--------|----------|----------|
| **Google Optimize replacement** | A/B testing is the wrong product shape (continuous, not pre-launch). Vacuum is already filled by Statsig + GrowthBook + VWO + Mida + Blazeway + ExperimentHQ + SplitLP + RunPivot + Humblytics + Segmently. Multi-week lookalikes already shipped. | `goprecision.co/blog/google-optimize-alternatives/` lists 10+ filled alternatives; medium.com/@andrew-chornyy lists 6 free ones in 2025 alone |
| **Hotjar replacement** | Microsoft Clarity is free forever with unlimited heatmaps, session replays, and rage-click detection. Microsoft-backed. Do not invite a "but Clarity is free" objection. | `uxheat.com/blog/crazy-egg-vs-clarity` — Clarity = $0 unlimited; full-feature alternative |
| **Crazy Egg replacement** | Same as Hotjar — Clarity wins | Same source |
| **Lorelight-style GEO / AI-visibility tracking** | The founder of the prior winner publicly shut it down October 31 2025 saying the problem doesn't need solving as a standalone product. SearchEngineLand corroborates. | `growwithless.com/shutting-down-lorelight/`; `searchengineland.com/geo-startup-lorelight-shuts-down-464208` |
| **Generic free SEO audit** (Ahrefs/Moz/SEMrush graveyard angle) | PageSpeed + Ahrefs Free + SEODiff + FreePageRank already fill the free-SEO-audit space. SchemaReports + AuditAI cover the AI-search audit niche. LaunchLook on SEO is a focus dilution. | `seodiff.io`, `freepagerank.com` both already free with no signup; competitive-intel doc §4.1 marks SEO as crowded |
| **Lighthouse CI replacement** | Wrong audience. CI users are devs; LaunchLook is for non-technical vibe coders pre-launch | Chrome's own transition post; LaunchLook can use PSI but not compete with Lighthouse CI |
| **Free Pingdom-equivalent right now** | Continuous monitoring is a v2 / subscription product. Better Stack + HetrixTools + Uptime Kuma already fill it. LaunchLook's one-time positioning shouldn't fork into ongoing monitoring until Watch tier | See deep dive 2 cross-check |
| **W3C-style site validator** | Site validation as a standalone product (HTML conformance, etc) has no buyer in 2026 — modern frameworks emit valid HTML by construction and AI builders sidestep this | No live competitor in this category for non-tech buyers; absence of demand signal |

---

## 7. Appendix — sources and notable threads

### Primary "vacuum" announcements
- Google Optimize sunset (Sept 30, 2023): `blazeway.app/vs/google-optimize/`, `experimenthq.io/blog/why-google-optimize-discontinued`, `runpivot.com/compare/runpivot-compare-google-optimize`
- Web Vitals Chrome extension end-of-life (Jan 13, 2025): `developer.chrome.com/blog/web-vitals-extension-merged`
- Lighthouse DevTools panel sunset (H2 2025): `developer.chrome.google.cn/blog/perf-tooling-2024`, `developer.chrome.google.cn/blog/moving-lighthouse-to-insights`
- Hotjar merged into Contentsquare (July 2025): `saaspricepulse.com/tools/hotjar`, `fullsession.io/blog/hotjar-free-plan/`, `quackback.io/blog/hotjar-pricing`
- Hotjar alleged stealth price hikes (May 2026): `affiliate-times.com/hotjars-alleged-stealth-price-hike-is-rattling-affiliate-tech-stacks/`
- UptimeRobot free tier restricted to non-commercial (Oct/Nov 2024): `notifier.so/guides/uptimerobot-alternative/`, `dev.to/velprove/freshping-shut-down-7-best-free-alternatives-for-2026-with-migration-guide-hbf`
- Freshping shutdown (June 4, 2026): `dev.to/velprove/freshping-shut-down-...`
- Pingdom no free tier post-SolarWinds: `notifier.so/guides/free-pingdom-alternative/`, `hyperping.com/blog/best-pingdom-alternatives`
- BrowserStack pricing restructure (April 2026): `getpulsesignal.com/changes/browserstack`
- Lorelight shutdown (Oct 31, 2025): `growwithless.com/shutting-down-lorelight/`, `searchengineland.com/geo-startup-lorelight-shuts-down-464208`, `ppc.land/lorelight-founder-shuts-down-ai-visibility-tracking-tool/`
- WAVE Firefox toolbar abandonment: `webaim.org/blog/wave-updates/`

### Replacement / orphan-capture lookalikes (validate the vacuum exists)
- Optimize refugees: Blazeway, ExperimentHQ, RunPivot, SplitLP, Mida, Segmently, Statsig, GrowthBook, Humblytics
- Uptime: Better Stack, Notifier.so, HetrixTools, Uptime Kuma, Hyperping, StayAlive, SecurityBot.dev
- Security headers + non-tech translator: hackit.cloud, SecurityBot.dev, StayAlive, FortWatch
- Screaming Frog: FreeCrawl, LibreCrawl, Sitebulb, DeepCrawl
- Web Vitals: PageSpeed Insights API (free 25K calls/day), `developers.google.com/speed/docs/insights/release_notes`
- Visual regression OSS: Lost Pixel, Lastest, Sentinel, DojoWatch, Argos
- Form monitoring: MoniForm, FormWatch, FormTracker
- AI-audit competitor landscape (cross-reference): see `COMPETITIVE-INTEL.md` §2

### Quotes worth keeping
- Lorelight founder (post-mortem): *"customers were churning because the product didn't change what they needed to do… You don't need a specialized tool for [this]"* — this is the anti-pattern to watch for; check every queued LaunchLook feature against "does this change buyer behavior or just measure it?"
- ExperimentHQ on Optimize: *"Estimates suggest 2-3 million websites used Google Optimize. Overnight, they lost their testing capability."*
- Medium on Screaming Frog: *"the 500-URL limit on the free version isn't really 500 URLs. It's 500 crawled resources… tapped out at page 127"*
- hackit.cloud landing page: *"They're great tools — for security engineers. hackit.cloud is built for everyone else."* — verbatim the wedge LaunchLook should claim.
- Affiliate Times on Hotjar: *"alleged stealth price hike is rattling affiliate tech stacks"* — the buyer pain is real, but Clarity already won; do not chase.

---

*Companion docs: `COMPETITIVE-INTEL.md`, `SITE-BUILDER-MARKET-RESEARCH.md`, `03-build-queue.md`, `02-strategy-and-context.md`. The site-builder vacuum was researched separately and recommended against. This doc focuses on the **AI/vibe-coder** segment LaunchLook already serves.*
