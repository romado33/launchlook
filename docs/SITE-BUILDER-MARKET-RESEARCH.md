# Site-Builder Market Research — Should LaunchLook Expand Beyond Vibe Coders?

_Updated 2026-05-25 · Audience: Rob · Status: research + recommendation_

---

## 1. Executive Summary

**Recommendation: (d) Don't expand now. Defer site-builder expansion until LaunchLook hits ≥30 paying vibe-coder customers. When that day comes, pilot Webflow only — every other platform is either saturated, structurally wrong, or both.**

Three findings drove this call:

1. **The two biggest markets (WordPress + Shopify) are saturated.** WordPress has free URL-based scanners (Sucuri SiteCheck, wp-scan.org, WPScan) and dozens of paid care plans ($89–$1,000+/mo via WP Buffs, Codeable). Shopify has a deep CRO-audit ecosystem ($680–$2,200/page) targeting the exact surface LaunchLook would scan. Buyers expect humans, walkthroughs, and retainer credit-backs.
2. **Framer — the platform whose pain points _most_ resemble LaunchLook's strengths — is already covered by ≥5 dedicated audit plugins** (Launch Ready, LaunchOps, FrameReview, Preflight, Frame Audit). Most free or freemium. All run inside the editor with click-to-layer UX a URL scan cannot match.
3. **The fix-prompt format is the load-bearing wall.** "Paste this into Lovable" is LaunchLook's wedge. For WordPress that becomes "install plugin X, navigate to Appearance → Customize → ..." — a content + QA tax of 1–2 weeks per platform, with ongoing maintenance every time the platform UI changes (Webflow's Nov 2024 form update broke every existing tutorial overnight).

The one genuine gap worth a future pilot is **Webflow**: designer/freelancer buyer psychology closest to vibe coders, no native pre-launch audit plugin, audit-service pricing floor sits at ~$899 leaving room for a $49–$99 productized scan. That's a Q3/Q4 conversation, not a now conversation. The repo's own discipline ("don't build user-facing automation before 10+ paying customers") applies even harder to second-product expansion.

---

## 2. Pain-Point Matrix

| Pain Point | Platforms | Native / cheap plugin solves it? | LaunchLook pipeline fit | Monetization signal |
|---|---|---|---|---|
| Forms silently break, lose leads | Webflow, Wix, Squarespace | **No** — Webflow Nov '24 update broke email notifs site-wide | **Strong** (Playwright form-submit canary) | **High** — agencies report "missing 2 months of contacts" |
| Missing JSON-LD / structured data | Framer (71%), Wix, Webflow | Framer plugins yes; Webflow/Wix no | **Strong** (HTML pattern-match) | Medium |
| Checkout friction (no guest checkout, hidden shipping, no express pay) | Shopify, WooCommerce | Partial — settings exist, often misconfigured | **Strong** | Very high but **heavily commoditized** |
| Plugin conflict / slow load | WordPress | **Yes** — Wordfence, Query Monitor, host tools | Weak — needs server access | Low |
| Security headers / outdated core | WordPress | **Yes** — Sucuri SiteCheck free, wp-scan.org free | Strong but **redundant** | Low — free incumbent excellent |
| SEO ceiling (slow LCP, no CWV control) | Squarespace, Wix | **No fix** — structural; answer is "migrate" | Weak — output is depressing, not actionable | Low |
| Mobile UX bugs (tap targets, overflow) | All | Framer plugins partial; nobody else URL-side | **Strong** | Medium |
| Broken redirects post-migration | Webflow, Framer | Partial (LaunchOps) | **Strong** | Medium — concrete $ impact |
| Trust-signal gaps (no policy, no reviews, no contact) | Shopify, all SMB | **No native flag** | **Strong** | High — but Shopify CRO firms mine it |
| Accidental noindex / robots blocking | All | No — GSC catches it eventually | **Strong** (trivial HTTP check) | Medium — silent killer |
| **Fix-prompt format doesn't translate** | All non-AI-builder | n/a | **WEAKNESS** — wedge collapses | Critical risk |
| Handoff QA (designer ships, client finds bugs) | Webflow, Framer | Framer yes (5 plugins); Webflow **no** | **Strong** | Medium (freelancers = price-sensitive) |

**Reading:** Strong fit + no incumbent = forms-broken (row 1), trust-signal gaps (row 9), noindex (row 10), handoff QA (row 12). Of those, **Webflow** appears in three. Shopify's row 9 is buried under a dense human-audit market.

---

## 3. Per-Platform Deep Dive

### WordPress — 274K subreddit, ~470M sites (~43% of all websites)
**Top pains** (24x7wpsupport, sheafmediagroup, dev.to playbooks): plugin conflicts, slow load, SMTP/email delivery, SSL migration loops, WooCommerce checkout, malware, DB corruption.

**Why LaunchLook doesn't fit:**
- Most pain needs **server access** (PHP version, `wp-config.php`, `.htaccess`, plugin list, DB queries). URL scan sees symptoms, not causes.
- Free incumbents dominate: [Sucuri SiteCheck](https://sitecheck.sucuri.net/), [wp-scan.org](https://wp-scan.org/malware-check) (22 checks, A+ → F, no signup), [WPScan](https://wpscan.com/scan/).
- Paid incumbents entrenched: WP Buffs $89–$359/mo, Codeable $140–$1,000+/mo retainers and $599–$1,500 one-time audits (all include human walkthrough).
- Fix prompts need full rewrite per theme/builder (Divi, Elementor, Gutenberg, Bricks, Oxygen — thousands of combinations).

**Verdict: Avoid.** Wrong shape, wrong buyer, dominant incumbents.

### Shopify — 306K subreddit, ~48M stores
**Top pains** (forgecro, jasonstokes, buildgrowscale 2026 checklists): forced account creation (~34% of cart abandonment per Maropost 2026), no guest checkout, missing express payments, hidden shipping, vague delivery, weak reviews, mobile UX gap, abandoned-cart flows.

**Pipeline _technically_ fits 1:1** — but the market is **the most saturated on the list**:
- Blackbelt Commerce: $997 flat (credit-back) · Stargazer Studio: $899 · cro.media: $1,499 · 100xelevate: $1,599/page · Zinn Hub: $680 — all human-delivered, all with walkthrough calls.
- A $30K+/month store owner expects "human expert," not "AI scan + PDF." LaunchLook would either undercut to $49 (looks unserious for a revenue-critical store) or compete at $999+ (where humans win).
- Shopify-specific fixes need merchant-admin vocabulary ("Settings → Checkout → enable guest checkout"), not AI-builder prompts.

**Verdict: Avoid for now.** Tempting overlap, but the moat is human relationships + retainer credit-back.

### Webflow — 34K subreddit, ~12M sites
**Top pains** (Webflow community forum, Discourse, agency blogs):

1. **Form submissions silently failing post Nov 2024 update.** Agency running 250–300 sites reports forms stuck on Pixel 7/8, missing labels in email notifications, broken `Send To` validation ([Form Issues - LOTS OF THEM!](https://community.webflow.com/ask-answer/post/form-issues---lots-of-them-jwCVuuYwfrl4F8A)).
2. **Email notifications not delivering.** _"It seems that have been missing contacts and newsletter subscriptions for 2 months :( No warning ever received."_ ([Discourse thread](https://discourse.webflow.com/t/form-submission-stopped-working-with-no-apprent-reason/308987))
3. **No native pre-launch audit tool.** Webflow University publishes a 20+ item manual checklist; third-party agencies sell $899–$4,800 audits. Nothing $49–$99 productized.
4. CLS / SPA hydration hurting Core Web Vitals.
5. Client handoff QA is freelancer pain — designer ships, client emails next week with a bug list.

**LaunchLook pipeline fit: strong.** Form-submit verification, broken-CTA, mobile screenshot diff, schema/meta checks, link crawl — all map without modification. Fix-prompt rework is the lightest of any non-AI platform: Webflow users edit visually, so instructions translate as _"In Designer → select Form → Settings tab → ..."_

**Verdict: only platform genuinely worth a pilot. Save for Phase 2.**

### Squarespace — 18K subreddit, ~23M sites
**Top pains** (howtohosting.guide 2,316-review analysis, webvise): support response delays (24+ hrs, no phone), Google-Domains transition friction, **SEO ceiling — PageSpeed 45–65 mobile is typical and structural** (third-party scripts bundled, no caching control), no Core Web Vitals control, limited structured data, no autosave, grid limits.

**Why it doesn't fit:** most pain is structural to the platform — the answer is "migrate," not "audit." LaunchLook reporting _"your PageSpeed is 52"_ tells the owner nothing they can act on inside Squarespace.

**Verdict: Avoid.**

### Wix — 15K subreddit, ~29M sites
**Top pains** (we-optimizz, insidea, VisualSitemaps): dynamic-page URL prefixes locked (`/product/`, `/post/`), accidental noindex misconfigs, 5-markup-per-page schema cap, weak internal linking, mobile content hiding.

**Notable context:** Wix stock down ~50% YTD, ~1,000 layoffs (20% of workforce) announced May 2026. **Wix owns Base44**, which is on LaunchLook's existing vibe-coder target list. Wix is now competing with itself.

**Why it doesn't fit:** Pipeline could detect most issues, but Wix's buyer profile is "I bought Wix to not think about SEO" — least audit-tolerant audience. Platform instability adds risk.

**Verdict: Avoid.** Possibly revisit if Wix consolidates around Base44 as the AI play.

### Framer — small but active community (~tens of thousands of designers)
**Top pains** (97-site SEO audit by letaiworkforme): thin content (95% of sites), broken H1 (92%), weak internal linking (94%), Lighthouse perf <90 (92%), missing alt text (89%), missing JSON-LD (71%), CLS from font/animation hydration, favicon caching, no granular `robots.txt`.

**Pipeline fit is structurally perfect** — and **commercially blocked.** The Framer Marketplace already has ≥5 dedicated audit plugins:
- **[Launch Ready](http://framer.com/marketplace/plugins/launch-ready/)** (free) — alt text, favicon, OG image, nested links, mobile overflow, A–D grade
- **[LaunchOps](https://www.framer.com/marketplace/plugins/launchops/)** — broken links, redirects, localization, CMS, accessibility, JSON-LD checks
- **[FrameReview](https://www.framer.com/marketplace/plugins/framereview/)** — first 5 audits free, marketplace + SEO + a11y + perf
- **[Preflight](https://www.framer.com/marketplace/plugins/preflight/)** — free + Pro with PageSpeed + AI auto-fix via Claude/MCP
- **[Frame Audit](https://framer.com/marketplace/plugins/frame-audit/)** — PageSpeed + a11y + responsiveness

These plugins beat LaunchLook on **jump-to-layer UX** — click a finding, the plugin selects the broken layer in canvas. URL-only audit can't match that. The platform whose pain most resembles LaunchLook's strengths is the most saturated by native tooling.

**Verdict: Avoid.**

### Carrd / Ghost
- **Carrd** is intentionally single-page; no real audit market.
- **Ghost** pains (Amazon card bugs, `cards.min.js` race condition, admin lockouts on staff device verification) but the audience is technical bloggers/self-hosters — wrong buyer for LaunchLook.

**Verdict: Skip.**

---

## 4. Strategic Analysis

### 4.1 Overlap map — what translates cleanly?

| Capability | Vibe Coders | WP | Shopify | Webflow | Squarespace | Wix | Framer |
|---|---|---|---|---|---|---|---|
| URL audit + screenshot | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Broken-CTA, mobile bugs, copy, a11y, regression | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Trust-gap detection | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | partial |
| Security-lite (headers, exposed routes) | ✅ | ⚠️ saturated | ✅ | ✅ | partial | partial | ✅ |
| **AI-builder fix prompts (current format)** | ✅ | ❌ rewrite | ❌ rewrite | ❌ rewrite | ❌ rewrite | ❌ rewrite | ❌ rewrite |

**Read:** detection translates everywhere; **fix-prompt generation collapses everywhere outside the AI-builder world.** That single row is the entire strategic problem.

### 4.2 The fix-prompt problem

LaunchLook's wedge isn't "we find 25 issues" — it's "here are 25 paste-ready prompts for the AI you already use." That output costs ~30s of model time per finding, is high-trust because the format matches what vibe coders do all day, and has **near-zero per-platform content cost** (Lovable, Bolt, Cursor, v0, Replit, Base44 all consume natural-language prompts identically).

A WordPress/Shopify/Webflow version requires platform-specific UI vocabulary, plugin-aware fix paths (Elementor vs Gutenberg vs Divi for WP alone), QA review per fix, and ongoing maintenance every time the platform UI changes. **Estimate: ~1–2 weeks engineering + content per platform, plus permanent maintenance debt.** Webflow's Nov 2024 form-system update is a live example of why this matters — any prior tutorial broke overnight.

**Conclusion: per-platform fix prompts are technically feasible but commercially expensive.** If expansion happens, start with **one** platform (Webflow is the lightest lift) and treat it as a separate content surface.

### 4.3 Buyer-psychology overlap

| Trait | Vibe Coder | Webflow/Framer Designer | WP/Shopify Owner |
|---|---|---|---|
| "Scared to launch" | high | high | medium |
| QA process exists | no | partial | yes (agency/VA) |
| Price tolerance | $19–$99 | $49–$499 | $99–$2,000+ |
| Expects human contact | no | sometimes | **yes — almost always** |
| Time-to-decision | minutes | hours | days, via referral |

**Webflow/Framer designers are the closest psychological match.** WP/Shopify owners are a different buyer entirely — they expect agency-tier service.

### 4.4 Competitive landscape (published prices, May 2026)

| Service | Platform | Price | Format |
|---|---|---|---|
| Sucuri SiteCheck, wp-scan.org, WPScan | WordPress | **Free** | URL scanner |
| WP Buffs care plans | WordPress | $89 / $179 / $239 / $359 per month | Retainer |
| Codeable maintenance | WordPress | $140 / $590 / $1,000+/mo | Retainer |
| Codeable audit | WordPress | $599 / $999 / $1,500+ one-time | Human + walkthrough |
| Blackbelt Commerce | Shopify | $997 (credit-back to retainer) | Human, 7d, 60min call |
| Stargazer Studio | Shopify | $899 one-time | Human, 5d, no store access |
| cro.media | Shopify | $1,499 + free implementation | Human team |
| 100xelevate | Shopify | $1,599 / $2,200 per page | Human, bundled |
| Beetlebeetle "free audit" | Webflow | $0 | Human, 72h, 3–4 tips (lead-gen) |
| FloPros monthly audit | Webflow | $4,800 one-time | Monthly delivery |
| DH Insights retainer | Webflow | $3,760 / $8,000 per month | Hours bank |
| Launch Ready / Preflight / etc. | Framer | Free | In-editor plugin |

**Gap LaunchLook could fill:** $19–$99 productized, no-call, AI-driven, URL-only scan. That gap is **genuine for Webflow** (no $49 option exists). It's **already filled or commoditized** for WordPress (free incumbents) and Shopify (sub-$1k human market). For Framer, plugins own the niche.

### 4.5 Single app vs split — recommendation: **(d) Don't expand now, with reserved Phase 2 = Webflow only**

| Criterion | (a) Single app, fork per platform | (b) Two surfaces, one brand | (c) Separate product | **(d) Don't expand** |
|---|---|---|---|---|
| Cost of build | 4–8 weeks | 4–8 weeks + brand surface | 6–10 weeks + brand work | **$0** |
| Time-to-revenue | 8–12 weeks | 8–12 weeks | 12+ weeks | n/a |
| Risk to vibe-coder positioning | **high** (dilutes wedge) | medium | low | none |
| Engineering distraction pre-PMF | high | high | high | none |
| Market size if it works | huge | huge | huge | bounded |
| **Probability it works** | **low** (saturated) | low–medium | medium | n/a |

The repo's stated discipline — *"Don't let Cursor build user-facing automation before you have 10+ paying customers"* — applies even harder to a second product. LaunchLook hasn't proven the vibe-coder thesis yet (free 3-finding hook is queued, not shipped). Expanding before PMF would split focus, dilute "for AI builders," and pour engineering into the **lowest-probability-of-payoff segment of the matrix**.

Honest framing: site-builder users have real pain, but most of it is either already solved by incumbents or shaped wrong for LaunchLook's URL-only / AI-fix-prompt model. The single exception is Webflow, and that exception isn't urgent.

### 4.6 If you expand to Webflow later — top 5 MVP features

In order of leverage per engineering hour, biased toward what the existing pipeline can do today:

1. **Webflow form-submit canary** _(≤1 week)_ — Playwright submits dummy data to every form, verifies confirmation page + email delivery to a LaunchLook-owned mailbox. Directly attacks the #1 forum complaint. Zero AI; just Playwright + mailbox.
2. **noindex / robots / sitemap sanity check** _(≤2 days)_ — already in pipeline; surface as a Webflow-flavored finding. Catches "accidentally hid your whole site from Google."
3. **Webflow-flavored fix-prompt fork** _(~1 week)_ — same finding library, output rewritten as Designer-panel instructions. Cheapest fix-prompt fork of any non-AI platform.
4. **JSON-LD / schema gap report** _(≤2 days)_ — HTML parse for `application/ld+json`, flag missing per content type. Webflow's site-wide custom-code-head model means schema is often forgotten on CMS pages.
5. **Client-handoff "ship report" PDF variant** _(≤3 days)_ — same engine, branded for freelancer-to-client delivery, including a before/after snapshot pair. Reframes the product for the Webflow freelancer's actual moment of pain (sending a deliverable).

**Total Phase 2 effort:** ~3–4 calendar weeks to a credible Webflow MVP. **Defer until vibe-coder PMF is in hand.**

---

## 5. Recommendation + MVP Scope

**Immediate (next 90 days): do not expand.** Continue shipping the vibe-coder build queue (free 3-finding hook, security-lite, re-scan, Watch subscription). Validate the wedge with ≥30 paying customers.

**Phase 2 trigger (~3–6 months out):** when LaunchLook clears 30 paying customers AND has a repeatable acquisition channel, run a **Webflow pilot** as a separate landing page under the same brand — option (b) framing: "LaunchLook for Webflow." Do not pursue WordPress, Shopify, Squarespace, Wix, or Framer at any point absent strong new evidence.

**Webflow pilot MVP:** five features above, ~3–4 calendar weeks. Soft-launch on r/webflow + Webflow Discord + designer Twitter. Price experiment: $29 / $79 / $149 — landing just under the freelance-audit floor at $899.

**Hard-stop conditions for the pilot:**
- If Webflow ships a first-party pre-launch audit in their next 2 quarters → abandon.
- If a Framer-style plugin marketplace audit competitor emerges → abandon.
- If the first 20 Webflow buyers ask for a walkthrough call → buyer expects "human"; the productized model breaks.

---

## 6. Appendix — Notable Threads / Quotes / Evidence

### Webflow forms (highest-confidence pain)
- [community.webflow.com — "Form Issues - LOTS OF THEM!"](https://community.webflow.com/ask-answer/post/form-issues---lots-of-them-jwCVuuYwfrl4F8A) — agency managing 250–300 sites, unresolved post-Nov 2024 form bugs. _"I'm having real trust issues with Webflow Forms."_
- [Discourse — "Form submission stopped working"](https://discourse.webflow.com/t/form-submission-stopped-working-with-no-apprent-reason/308987) — _"missing contacts and newsletter subscriptions for 2 months :( No warning ever received."_
- [homade.co — Missing form labels guide](https://www.homade.co/post/how-to-fix-missing-form-labels-in-webflow) — third-party walkthrough for the Nov '24 fix.

### Framer audit market is already saturated
- [Launch Ready](http://framer.com/marketplace/plugins/launch-ready/) (free), [LaunchOps](https://www.framer.com/marketplace/plugins/launchops/), [FrameReview](https://www.framer.com/marketplace/plugins/framereview/) (first 5 free), [Preflight](https://www.framer.com/marketplace/plugins/preflight/) (free + AI via Claude/MCP), [Frame Audit](https://framer.com/marketplace/plugins/frame-audit/).

### Framer SEO baseline (97-site audit)
- [letaiworkforme — Framer SEO Problems](https://letaiworkforme.com/blog/framer-seo-problems): 95% thin content, 92% broken H1, 94% weak internal linking, 71% no JSON-LD.

### WordPress free incumbents (key reason to avoid)
- [Sucuri SiteCheck](https://sitecheck.sucuri.net/), [wp-scan.org](https://wp-scan.org/malware-check) (22 checks, A+ → F, no signup), [WPScan](https://wpscan.com/scan/).

### WordPress paid incumbents
- [WP Buffs plans](https://wpbuffs.com/plans/) — $89/$179/$239/$359 per month.
- [Codeable WordPress audit](https://www.codeable.io/packages/wordpress-audit/) — $599/$999/$1,500+ with walkthrough call.
- [Codeable 2026 maintenance pricing](https://www.codeable.io/blog/wordpress-maintenance-pricing/).

### Shopify CRO audit market
- [Blackbelt Commerce](https://www.blackbeltcommerce.com/shopify-conversion-audit/) ($997 flat, credit-back), [Stargazer Studio](https://stargazerstudio.net/shopify-cro-audit) ($899), [cro.media](https://cro.media/shopify-cro-audit/) ($1,499). Public 2026 checklists: [forgecro](https://forgecro.com/shopify-cro-audit-checklist/), [jasonstokes](https://jasonstokes.com/blog/shopify-store-audit-checklist-2026), [buildgrowscale](https://buildgrowscale.com/shopify-conversion-rate-optimization-guide).

### Squarespace ceiling complaints
- [webvise — Squarespace problems](https://webvise.io/blog/squarespace-website-problems) — PageSpeed 45–65 mobile is typical and structural.
- [howtohosting.guide — 2,316-review analysis](https://howtohosting.guide/squarespace-customer-review/) — support delays + Google-Domains transition top the list.

### Wix instability + Base44 ownership (relevant cross-link)
- [coincentral — Wix stock drops 50%, 1,000 layoffs](https://coincentral.com/wix-stock-drops-50-as-1000-job-cuts-signal-deeper-trouble-after-earnings/) — May 2026. Base44 ARR $150M; on LaunchLook's existing target list.

### Market size (Sep 2025 / 2026)
- [Subreddit counts](https://www.websitebuilderexpert.com/news/subreddits-for-businesses/): r/Wordpress 274K, r/shopify 306K, r/squarespace 18K, r/wix 15K. r/Webflow ~34K via [gummysearch](https://gummysearch.com/r/webflow/).
- [Platform market share 2026](https://tsidigitalsolution.com/website-platform-market-share-in-2026/): WordPress 472M sites, Shopify 48M, Wix 29M, Squarespace 23M, Webflow 12M.

### Webflow audit pricing range
- [FloPros](https://www.flopros.com/signup/power-up/monthly-audit-bundle) $4,800 one-time · [beetlebeetle](https://www.beetlebeetle.com/post/webflow-pricing-free-vs-paid-plans) free human audit (lead-gen) · [DH Insights](https://www.digihotshot.com/dh-insights/webflow-maintenance-guide) $3,760–$8,000/mo retainers.

### Items flagged "anecdotal — Rob to validate"
- "Webflow has no native pre-launch audit plugin equivalent to Framer's" — based on absence in search results, not on positive proof.
- "Webflow/Framer designers are price-tolerant up to $499" — directional inference from agency pricing, not a primary buyer survey.
- The "first 20 buyers ask for a walkthrough call" hard-stop is a heuristic, not a measured threshold.

---

_End of report. Decision-relevant content is sections 1, 4.5, 5._
