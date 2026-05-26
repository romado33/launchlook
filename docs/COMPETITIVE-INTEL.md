# LaunchLook Competitive Intelligence Report

*Research date: May 25, 2026 • Compiled by competitive intel worker • Audience: Rob (founder)*

---

## 1. Executive Summary

LaunchLook is entering a market that **looks like a beach but is in fact a coral reef** — crowded with niche tools that all converged on the same idea in 2024-2026: scan a vibe-coded site, output AI-readable findings, charge a one-time fee. The single most important finding in this report: **PageLens AI** ([pagelensai.com](https://www.pagelensai.com)) is a near-twin of LaunchLook — same buyer, same workflow (URL in → markdown out → paste into Claude/Cursor), pricing that undercuts LaunchLook ($1 / $15 / $29 vs $19 / $49 / $99), with an MCP server already shipped. **VibeDoctor** (vibedoctor.io, ~129 checks, $0/$15/$49/$129) and **SchemaReports** (identical $19/$49/$99 ladder for AI-search audits) are the next two closest threats.

The market's "table stakes" have stabilized: a free or near-free hook, markdown/Cursor-ready fix prompts, security headers + secret scanning, and a 30–60 second turnaround. **Head-on competition with PageSpeed Insights / Lighthouse / Microsoft Clarity is suicidal** — they are free, Google-/Microsoft-backed, and have ~100% awareness among technical users. Head-on with PageLens AI is also painful: same wedge, lower price, more checks already shipped.

LaunchLook's defensible angle is **the human in the loop** ("founder-curated" spot-check) plus the **persona-tagged "Testers" cast** — emotionally distinctive in a market drowning in lookalike "vibe-X" SAST wrappers. The 2-3 most leveraged moves are: (1) lean harder into curation as anti-AI-slop positioning, (2) ship the free 3-finding hook *immediately* because it is now the genre's price of admission, (3) raise the Pro tier ceiling and add a $199-$299 "human roast + AI audit" hybrid that flanks Dan Kulkov ($99 video roast, 300+ sold) and Olly Meakings ($350, 850+ sold). The $19/$49/$99 ladder is **directionally correct but mispriced at the Starter tier** — $19 for 5 findings is more expensive per finding than every competitor; $1-$5 free-trial-with-upsell is the proven hook.

The biggest surprise: the "vibe coding audit" niche has gone from empty in late 2024 to ~12 tracked entrants by May 2026, with three Product Hunt launches in the last 90 days alone. **The land grab window closes in Q3/Q4 2026.** Whoever owns the SEO terms "vibe coding security," "AI app audit," and "is my Lovable app safe" by year-end will compound. Rob should treat distribution (content + communities) as a higher priority than feature parity.

---

## 2. Competitive Map

### Tier 1 — Direct competitors (AI / vibe-coder audit)

| Name + URL | Pitch | Pricing | Estimated traction | Worked | Failed | Buyer | Entrenchment | LaunchLook's wedge |
|---|---|---|---|---|---|---|---|---|
| **PageLens AI** ([pagelensai.com](https://www.pagelensai.com)) | "AI-ready website audit, $1 to start, markdown export for Cursor/Claude." | $1 Launch Scan (3 pages) / $15 Full Scan (25 pages) / $29 Launch Pack (15 pages, desktop+mobile, re-scan) / $5/mo Weekly Monitor | No public reviews on Wavel (0/5, 0 reviews). Active blog, shipped MCP server, "dogfood loop" content. No public traction numbers — **flagged for Rob to validate via SimilarWeb / X mentions** | Free instant check hook; markdown export for AI agents; MCP integration; "persona reviews" already shipped; vibe-coder positioning explicit | New, rule library "still expanding" per third-party review; no autofix; 25-page cap | Vibe coders shipping with Lovable/Bolt/Cursor — **identical to LaunchLook** | **Vulnerable** — closest twin but probably still small (zero reviews, recent launch). Window is open but narrowing. | Founder-curated human spot-check; persona-tagged "Testers" narrative; Loom walkthrough at Pro tier |
| **VibeDoctor** ([vibedoctor.io](https://vibedoctor.io)) | "Production readiness platform for AI-coded apps. 129+ checks in 30s." | Free (3 scans/day) / Watch / Guard / Shield — entry **$15/mo** per PR-release; team plans up to 25 seats | Public PR launch May 6, 2026 (PRLog); ships from Patna, India; testimonials on pricing page (low-volume but real). Listed on multiple aggregator sites. Solo founder origin story. | "AI-specific" checks (hallucinated imports, god files, empty tests); free continuous scanning; GitHub PR integration; rich visual "Vibe X-Ray" | Subscription-only — no one-off purchase path; brand "VibeDoctor" is generic and crowded by 8+ "vibe*" tools; India support time zone | Indie hackers + small teams shipping with Cursor/Copilot/Bolt | **Vulnerable but rising** — most product-developed of the direct cohort. The 129-checks-in-30s claim is hard to match. | LaunchLook is one-time payment (no commitment); founder-curated narrative; persona tags; English-speaking founder time zone |
| **ZeriFlow** ([zeriflow.com](https://zeriflow.com)) | "Free 80-check website security scan, plus deep code scan via GitHub." | Free Quick Scan; Advanced (GitHub/ZIP) paid (pricing not publicly disclosed at scan time — **flag for Rob**) | No published traction numbers. Active marketing site, claims "covers everything Mozilla Observatory + SecurityHeaders.com check, plus 60+ more." | Free + sticky comparison vs. competitor freebies; URL + source-code scan in same product | Security-only positioning (no UX/copy/persona findings); pricing opacity hurts SMB conversion | Developers + freelancers who can connect GitHub | **Stalled-to-Vulnerable** — feature set is real but distribution is unclear | LaunchLook covers UX/copy/findings/integrations PLUS security-lite (when shipped); easier for non-technical buyer |
| **VibeSafe** ([vibesafe.io](https://vibesafe.io) + GitHub action) | "Free security scanner for AI-generated code. SAST + secrets on every PR." | Free GitHub Action; web scan free | Two competing repos ([vibesafeio/vibesafe-action](https://github.com/vibesafeio/vibesafe-action), [slowcoder360/vibesafe](https://github.com/slowcoder360/vibesafe) 21⭐ / 7 forks). 0 forks on the GH Action repo at scan time — **early but live in GitHub Marketplace** | "Copy AI Fix Prompt → paste into Cursor" UX is identical to LaunchLook's Quick Start Guide concept; auto-PR comments | Open source = hard to monetize; brand name collision with "VibeSafe" (multiple unrelated projects) | Devs who use GitHub PRs (excludes pure Lovable/Bolt no-code users) | **Stalled** — OSS toy, no clear business model | LaunchLook serves the no-code user who never opens a PR; paid model funds depth |
| **SchemaReports** ([schemareports.com](https://schemareports.com)) | "Free 12-phase AI audit. 0-100 visibility score. Real fixes." | Free (1/mo) → **Pro $19 / Multi-Business $49 / Prospector $75 / Agency $99** | Active marketing; agency-focused (GoHighLevel integration suggests real B2B GTM). No public review counts. | **Identical $19/$49/$99 ladder to LaunchLook** validates the price points exist in the market; free tier hook; PDF + Markdown export | Focused on GEO / AI search, not customer-readiness — pivoted away from generalist QA | SMB owners + GoHighLevel agencies | **Vulnerable** — niche positioning (AI search) leaves the customer-readiness wedge open | LaunchLook's broader "is your product ready?" framing covers what they explicitly don't |
| **Cursor Bugbot** ([cursor.com](https://cursor.com/help/account-and-billing/bugbot-usage-based-billing)) | "AI PR review inside Cursor. 80% bug resolution at merge." | Was $40/seat/mo, now **usage-based ~$1.00–$1.50 per PR run** (May 2026 change); High effort costs more | Massive — Cursor has millions of users. Bugbot has documented 0.7-0.95 bugs/run resolved at 79% at merge | Deep IDE integration; Learned Rules get smarter; Autofix cloud agent; published yield numbers | GitHub-only (4.5/10 platform support per third-party review); requires Cursor subscription; complex billing | Pro devs and small teams already paying for Cursor | **Entrenched at PR level** but not URL-audit level — **different job-to-be-done** | LaunchLook serves the user *before* they have a repo to PR against, and the user who never uses Cursor (Lovable/Bolt/v0 chat-only) |
| **VibeEval** ([vibe-eval.com](https://vibe-eval.com)) + [pypi vibeval](https://pypi.org/project/vibeval/) | "AI-powered E2E + security test simulation for vibe-coded apps." | Not publicly priced — **flag for Rob** | Active marketing site; PyPI package v0.1.0; positions as "QA team for vibe coders" | Behavioral simulation (real-user paths); load testing; explicitly markets to Lovable/Cursor/Bolt | No public pricing creates friction; CLI-first product excludes no-code buyers | More technical vibe coders (uses Claude Code) | **Stalled-to-Vulnerable** — interesting but the buyer is the wrong shape | LaunchLook delivers a PDF a non-technical founder can read, not a test runner |
| **Vibe Code QA** ([codeqa.aivyuh.com](https://codeqa.aivyuh.com)) | "5 AI agents review your repo. A-F grade in 60s." | Quick Scan free; Standard Audit (paid); Full QA (multi-repo, paid) — exact $ not on landing page | Self-dogfood example (15K LOC scan in 35s); no third-party reviews surfaced | Multi-agent positioning; A-F grade is sticky/shareable; PDF compliance export | Repo-only (no URL scan path); positioning blurs between QA tool and audit | Mid-market teams worried about AI-generated PR rubber-stamping | **Stalled** — no clear traction signals | LaunchLook scans live URL (any vibe-coding platform), not just GitHub repos |
| **Hordus.ai GEO Site Audit** ([hordus.ai](https://hordus.ai)) | "Full website crawl for AI search readiness." | Enterprise / quote-based | Tel Aviv company, launched April 29, 2026 (eaglecountry press release) | Brand-positioning crossover for B2B; full-site crawl | Enterprise sales motion excludes solo vibe coders entirely | B2B marketers | **Stalled at LaunchLook's tier** — different market entirely | LaunchLook serves the indie founder who can't afford a quote-based product |
| **AuditAI** ([auditaiseo.com](https://auditaiseo.com)) | "Chrome extension: 35+ AI search signals, A-F grade, AI Citation Simulation." | Free / $29 / $97 | Chrome extension, no signup, "no card" — strong activation play. PH-style launch energy. | "AI Citation Simulation" feature is genuinely novel; Chrome extension = zero-friction install | SEO/citation-only scope; doesn't address security, UX, or product-readiness | SEO consultants and marketers | **Vulnerable / Early** — niche but executing well on activation | Doesn't compete on LaunchLook's product-readiness wedge |
| **Free AI SEO Auditor (Launly)** ([launly.com/products/free-ai-seo-auditor](https://launly.com/products/free-ai-seo-auditor)) | "Open-source AI search audit. 0-100 score. Paste URL, no signup." | Free, OSS | **135 votes / 20 comments on Product Hunt May 12, 2026** — meaningful signal of audience appetite for free audit tools | "No signup" + "open source" = max trust; copy-paste fix prompt for Cursor; AI-search angle | OSS = no revenue model; narrow to SEO; no follow-up sale | Vibe coders + SEO crowd | **Stalled** — viral on launch, but no monetization path | LaunchLook has a real product + paid tiers + follow-up; Launly is a lead magnet at best |
| **IsItSafeBro / Sandyaa / Crucible / vibescore / vibeaudit / vibe-check** (various GitHub repos) | OSS scanners with various flavors | Free | <50 stars each; minimal traction; mostly weekend projects | Validates demand exists for "scan my vibe-coded app" | All OSS, no revenue, no marketing | Devs who scroll GitHub | **Dead / Stalled** | LaunchLook has a paid SaaS funnel; OSS toys don't compete for buyer time |

### Tier 2 — Adjacent (general website QA / audit)

| Name + URL | Pitch | Pricing | Traction | Worked | Failed | Buyer | Entrenchment | LaunchLook's wedge |
|---|---|---|---|---|---|---|---|---|
| **PageSpeed Insights** ([pagespeed.web.dev](https://pagespeed.web.dev)) | "Google's free page performance + Lighthouse audit." | Free; API: 25,000 calls/day free | Effectively universal — every SEO consultant, dev, and marketing team uses it. Backed by CrUX real-user data | Free, Google-backed, fast, becomes part of Search Console workflow | Performance/SEO-only; opaque to non-technical readers; "fix this opportunity" suggestions are jargon-heavy | Every web professional | **ENTRENCHED — DO NOT COMPETE** | LaunchLook translates technical findings into plain English + AI fix prompts a vibe coder can actually act on |
| **Lighthouse (Chrome DevTools)** | "Built into every Chrome browser." | Free | Universal in dev community | Zero install, instant results | Same jargon problem; lab data not real-user | Devs | **ENTRENCHED — DO NOT COMPETE** | Same as PageSpeed wedge — translation + curation |
| **WebPageTest** ([webpagetest.org](https://webpagetest.org)) | "Deep web performance testing across locations." | Free (basic) + Pro tiers | Industry standard for perf engineers since 2008 | Insanely detailed waterfall; multi-location; long-tail credibility | Wildly intimidating UI; useless to non-technical buyer | Perf engineers | **ENTRENCHED in narrow segment** | LaunchLook's buyer never sees WebPageTest; not actually competing |
| **GTmetrix** ([gtmetrix.com](https://gtmetrix.com)) | "Performance audit with Lighthouse + WebPageTest data." | Free / $14.95+/mo | Real long-tail brand in agency/freelancer space | Pretty visualizations; scheduled monitoring | Performance-only; "score chasing" trap | SMB + freelance devs | **Entrenched** in perf niche | Not competing on perf alone |
| **Microsoft Clarity** ([clarity.microsoft.com](https://clarity.microsoft.com)) | "Free unlimited heatmaps + session recordings forever." | **$0, no caps** | Microsoft-backed; tens of thousands of sites; near-universal among bootstrappers who heard "use Clarity" | Truly free, no asterisks; rage-click detection; Copilot natural-language queries | No surveys; data sold to Bing Ads (privacy-aware customers dislike); cannot scan static issues | Indie founders + small teams | **ENTRENCHED — DO NOT COMPETE** | LaunchLook is a one-off pre-launch QA, not ongoing analytics; different job-to-be-done |
| **Hotjar** ([hotjar.com](https://hotjar.com)) | "Heatmaps + session replay + surveys." | Free 35 sessions/day; Plus $39/mo; Business $99/mo; Scale $213/mo | 900,000+ orgs per Genesys Growth analysis | Surveys + feedback widgets; established brand | Daily session caps frustrate growing sites; Contentsquare migration triggered price complaints | UX-conscious SMB + mid-market | **Entrenched** but losing ground to Clarity | Different category — observation vs. audit |
| **FullStory** | "Enterprise session replay + StoryAI revenue attribution." | Custom; $25K-100K+/yr | Series B+ companies | Revenue attribution; deep analytics | No public pricing; sales call required | Enterprise | **Entrenched** in enterprise | Not LaunchLook's buyer |
| **LogRocket** | "Session replay + perf monitoring with generous free tier." | Free (1K sessions/mo) → Team $69/mo | Strong solo founder default | Conditional Recording on Pro | Replay-only focus | Solo devs + startups | **Entrenched** in segment | Different job |
| **Wappalyzer** ([wappalyzer.com](https://wappalyzer.com)) | "Tech stack detection + sales enrichment." | Browser ext free; API: 1 credit/URL, 5/live URL | Industry standard since 2008 | Massive cached database; sales-team distribution | Doesn't audit anything — only identifies | Sales/GTM teams | **Entrenched** in different category | Not competing |
| **BuiltWith** ([builtwith.com](https://builtwith.com)) | Same as Wappalyzer | Free lite + paid plans | Industry standard | Same | Same | Sales/GTM | **Entrenched** in different category | Not competing |
| **Fiverr "website review" / "UX audit" gigs** | Manual review by freelancer | **$5–$500+** per gig; midpoint ~$50-$100 for SEO audits, $80-$200 for UX | "Established sellers" have 100+ reviews on top-page gigs; per Fiverr Tutorials data, the credibility floor for SEO audits is $80-$100 | Cheap entry; human in loop; many languages | Quality wildly variable; AI-slop infiltration in 2025-2026 has eroded buyer trust at <$50; turnaround days, not minutes | Solopreneurs without dev budget | **Stalled / Vulnerable** — trust has cratered as AI-slop floods the platform | LaunchLook is faster (hours), structured PDF, branded credibility, founder-vetted |
| **Upwork "website audit"** | Same but project-based | $50-$500 typical | Larger projects (>$500) get traction | Real expert pool exists | High-touch sales motion; slow; vibe coders don't think to look here | Slightly larger companies | **Vulnerable in vibe-coder segment** | Same wedge — speed + price + audience fit |

### Tier 3 — Adjacent (security scanners)

| Name + URL | Pitch | Pricing | Traction | Worked | Failed | Buyer | Entrenchment | LaunchLook's wedge |
|---|---|---|---|---|---|---|---|---|
| **Snyk** ([snyk.io](https://snyk.io)) | "Developer-first security for code + deps + IaC + containers." | Free; Team $25/dev/mo (5 min, 10 max devs); Ignite $105/dev/mo ($1,260/yr); Enterprise custom | Dominant in DevSecOps; integrated into Cursor's security workflows | Free tier wide enough to hook; IDE integrations; brand recognition | Vibe coder is not a "contributing developer" — wrong unit of pricing; jargon-heavy UI; per-product upsell tax | Pro devs / DevSecOps teams | **Entrenched** in DevSecOps; **DO NOT COMPETE** | LaunchLook is for the founder who doesn't know what SCA or SAST means |
| **StackHawk** ([stackhawk.com](https://stackhawk.com)) | "Shift-left DAST that runs in CI/CD." | Pro $588/yr/contributor (min 25); Enterprise $708; **Vibe single-user $5/mo** (new — sits in AI assistant) | Enterprise AppSec brand; **NEW: "Vibe" $5/mo plan** is direct shot at LaunchLook's segment | $5/mo vibe-priced tier just shipped; runs inside Cursor | Still requires AI-assistant integration setup; not for no-code | Solo devs using AI assistants | **Entrenched** in enterprise; **Vulnerable in indie segment** (new entry) | LaunchLook delivers a finished PDF, not a DAST scanner you have to configure |
| **Detectify** ([detectify.com](https://detectify.com)) | "EASM + app scanning, attack-surface-based pricing." | App Scan from €90/mo (1 domain); Surface Monitoring from €302/mo (25 subdomains) | Established Swedish brand; mid-market | Continuous monitoring; Crowdsource intel | Indie pricing is steep; complex pricing axes | Mid-market security teams | **Entrenched** mid-market | Different buyer entirely |
| **Intruder** ([intruder.io](https://intruder.io)) | "Continuous attack-surface scanning." | $99/mo+ tiers | SMB sec brand | Easy onboarding for non-security teams | Pen-test-style framing intimidates non-technical | SMB IT/sec | **Entrenched** in SMB sec | Not in LaunchLook's lane |
| **OWASP ZAP** | Free OSS DAST | Free | Universal in security community | Free | CLI-heavy; intimidating | Pen testers | **Entrenched** in OSS sec | Not in lane |
| **AWS Security Agent** (preview May 2026) | "Full-repo code review reasoning like a human researcher." | AWS-pricing (TBD) | Massive AWS distribution potential | Reasons about trust boundaries, not pattern matching | AWS-only; preview-stage; complex setup | AWS customers | **Pending** — could become entrenched fast in AWS shops | LaunchLook is AWS-agnostic and pre-deploy |
| **Crucible** ([github.com/crucible-security/crucible](https://github.com/crucible-security/crucible)) | OSS LLM agent red-teaming | Free | Active OSS project | OWASP LLM Top 10 + Agentic mapping | LLM-specific (not site audit) | LLM app builders | **Stalled / niche** | Different scope |

### Tier 4 — Adjacent (UX / conversion review services)

Top 3 most relevant:

- **Baymard Institute** ([baymard.com](https://baymard.com)) — Research subscriptions $200-$700/mo; **Checkout UX Audit $7,000** one-off (e-commerce only). Gold standard for e-com UX research. Enterprise buyer; not in LaunchLook's segment but informs the "expert audit" mental model.
- **UXAudit.Now** ([uxaudit.now](https://uxaudit.now)) — Self-serve $0-$499/mo; 1,450+ research-backed guidelines across 5 platforms; explicit positioning against Baymard's $9,500/yr floor. Mid-market wedge between Baymard and LaunchLook.
- **Maze** ([maze.co](https://maze.co)) — Free (1 study/mo) / $99 Starter / Enterprise $12-62K/yr. Prototype testing, not site audit. 7M+ participant panel locked behind Enterprise. Not direct competition.
- **UserTesting** — Custom, $25K-50K+/yr. Enterprise only. Out of frame.

### Tier 5 — Indirect, consumer-facing ("roast" culture)

Top 3 most relevant:

- **Dan Kulkov / MakerBox** ([makerbox.club/landing-page-roasting](https://www.makerbox.club/landing-page-roasting)) — **$99 one-time, 20-min video roast, 300+ landing pages roasted.** Marc Lou's go-to ("I never launch without Dan's roasting"). Money-back conversion guarantee. **Direct LaunchLook competitor at the Pro tier price point.**
- **Olly Meakings / Roast My Landing Page** ([roastmylandingpage.com](https://www.roastmylandingpage.com)) — **$350 one-time, 15-min video, 500+ five-star reviews, 850+ pages roasted, 20-year CRO veteran.** Sells social proof + outcome guarantee. Premium roast tier.
- **Sébastien / fffuel** ([fffuel.co/rrroast](https://fffuel.co/rrroast)) — **$89 one-time** 20-year web creator. Same format. Cheaper alternative to Olly.
- **LandingPill** (Dan Kulkov, in progress) — productized version of his roast, branded as "your brutally honest friend."
- **Roast My Web** ([roastmyweb.com](https://www.roastmyweb.com)) — AI-version of the roast format with bootstrap-founder testimonials. Hybrid LaunchLook lookalike.
- **Marc Lou himself** — does *not* sell roasts; advocates for Dan Kulkov. Influencer with $90K/mo revenue and ~200K followers. Real distribution lever if LaunchLook can earn a mention.

---

## 3. Patterns

### What has consistently worked

1. **Free/near-free hook → paid upgrade.** PageLens ($1 Launch Scan), VibeDoctor (3 free scans/day), SchemaReports (1 free audit/mo), Launly AI SEO Auditor (open-source, 135 PH votes in 2 weeks), ZeriFlow (free 80-check), AuditAI (free Chrome extension, no signup). **Every tool with traction has a $0–$5 entry point.** LaunchLook's $19 Starter is the highest entry price in the cohort.

2. **Markdown / Cursor / Claude fix-prompt export.** PageLens, VibeDoctor, VibeSafe, Vibe Audit, Launly all converged on this. The "paste-ready fix prompt" is now table stakes, not a differentiator. LaunchLook's Quick Start Guide is the right product — it's just no longer unique.

3. **Founder-personality content marketing.** VibeDoctor's "solo founder watched AI coders ship broken apps" origin-story PR launch (May 6, 2026) was their primary distribution moment. Dan Kulkov, Olly, and Sébastien sell themselves as the product. Marc Lou's $90K/mo solo brand is the meta-pattern. **Solo-founder narrative converts in this segment.**

4. **Persona-style "what a real user sees" framing.** PageLens has shipped "persona reviews"; AuditAI has "AI Citation Simulation" (asks the LLM what it would say); LaunchLook's planned "Testers" cast is in the same lineage. Buyers want to feel like a person evaluated their site, not a linter.

5. **One-off purchase over subscription for indie buyers.** PageLens, MakerBox, Olly, fffuel, Vibe Code QA all sell one-off audits. VibeDoctor's subscription-only model is the outlier and slows their conversion. Indie founders pre-launch want to pay once, get a report, move on. **LaunchLook's one-time pricing is correct.**

6. **Specific traction numbers in copy.** Olly ("500+ 5-star reviews"), Dan ("300+ pages roasted"), VibeDoctor's PR ("9% had at least one High or Critical finding"). **Hard numbers convert.** LaunchLook needs its own once it has them.

### What has consistently failed

1. **"AI does the whole thing, no human review."** Roast My Web (AI-only) has bootstrap testimonials but no break-out traction. The "feels like AI slop" pattern is so well-known that **VibeDoctor explicitly markets that its checks "no other tool catches" because tools just regurgitate Lighthouse.** Pure AI output without human curation is the genre's commodity bottom. **LaunchLook's founder spot-check is the correct response to a real market failure.**

2. **Pure OSS "vibe-X" scanners.** vibesafe (21⭐), vibescore, vibeaudit, IsItSafeBro, Sandyaa, Crucible — all built, none monetized, low star counts. The buyer doesn't want to clone a repo. Tools that started as OSS and never wrapped a paid front-end have stalled.

3. **CLI-first products for non-technical buyers.** VibeEval ships a Python CLI alongside a marketing site for vibe coders — wrong audience for the delivery mechanism. The buyer who uses Lovable does not `pip install`.

4. **Enterprise sales for the indie segment.** Detectify (€90+/mo), FullStory (custom $25K+), UserTesting ($25K+). They tried to sell to small founders early and ran away. **Hordus.ai's quote-only "GEO audit" launch in April 2026 is repeating the mistake** — it cannot capture indie founders.

5. **Bugbot-style "pay per scan/PR" billing for non-team buyers.** Cursor moved Bugbot to usage-based billing in May 2026. Solo founders historically hate metered billing — see Anthropic's API confusion, Vercel's bill-shock complaints. **Do not adopt this pricing shape for LaunchLook.**

6. **Score-chasing as the only outcome.** GTmetrix and PageSpeed Insights both produce scores that engineers learned to chase, then ignore when ROI fell apart. A single 0-100 score is sticky as a screenshot but loses retention. **Numerical scores work as bait, not as the whole product.**

### Table stakes (must-have)

- Free or sub-$5 entry scan (LaunchLook's queued "free 3-findings hook" is this — **prioritize shipping**).
- Markdown / Cursor-ready paste-prompt export per finding.
- Security headers, secret scanning, basic accessibility checks.
- Sub-60-second turnaround for the freemium hook.
- PDF export for the buyer to save/share.
- Plain-English explanations alongside fixes.
- Vibe-coding-platform-aware (Lovable, Bolt, v0, Replit, Cursor, Base44 explicitly mentioned in copy).

### Graveyard (don't build)

- **Per-PR or per-scan usage billing for indie buyers.** Cursor's own buyer base resisted this; Vercel's mid-market did too. Indie founders want a sticker price.
- **CLI-only tools for non-technical buyers.** Skip the CLI entirely until you have a developer/agency tier; the buyer is not in a terminal.
- **Numerical score as primary product.** Useful as a bait/share asset; do not depend on it for retention.
- **Multi-AI consensus ("we ran it past 3 models").** csmoove530/vibe-codebase-audit shipped this; no traction. Sounds smart, costs you in compute, doesn't move conversion.
- **"GitHub repo only" audits.** Excludes Lovable/Bolt/v0/Base44 users who never see GitHub. Live-URL-first is correct.
- **Full-stack pentest framing.** Equixly and Crucible are positioning here; vibe coders will not buy "Agentic AI Hacker" — they will buy "Will my app embarrass me?"
- **Embed-a-badge gimmick** (PageLens shipped it on Weekly Monitor). Verified-badge fatigue is real; few sites display these.

---

## 4. Strategic Recommendations

### 4.1 Who is entrenched — avoid head-on

1. **PageSpeed Insights / Lighthouse / Microsoft Clarity / Google CrUX.** Free, Google/Microsoft-backed, integrated into Search Console, Chrome DevTools, and Edge. ~25,000 free API calls/day means *any* competitor can resell their data — and many do. **Never position LaunchLook as "faster than Lighthouse" or "better than PageSpeed."** Position as **the translator and curator** — *"PageSpeed tells you to optimize LCP; LaunchLook tells you that your checkout button is below the fold and your trial CTA copy reads like a 2019 SaaS template."*

2. **Cursor Bugbot.** Cursor has captured the AI IDE buyer. Bugbot is improving (effort levels, $1-1.50/run pricing) and integrated where the work happens. Avoid the PR-review / repo-level job-to-be-done entirely. **LaunchLook lives upstream of the PR** — at the live-URL moment when the vibe coder asks "is this ready?"

3. **Snyk.** Owns DevSecOps mindshare; will eventually ship something for indie devs. **Do not market against Snyk on the depth-of-security axis** — you will lose. Position as "the report your non-technical co-founder can read."

4. **Microsoft Clarity (specifically).** The "free forever" promise is so compelling that nearly every cost-conscious bootstrapper installs it. LaunchLook should **not** ship a heatmap, session replay, or ongoing analytics feature — it would invite an obvious "but Clarity is free" objection. Stay in pre-launch one-off audit territory.

### 4.2 Who can be uprooted

1. **PageLens AI — uproot via founder-curation positioning + community distribution. Timeline: 6 months.** PageLens has shipped a strong product but appears to lack a brand voice / community presence (no review counts surfaced; thin social proof). Their weakness is they look like a tool, not a person. LaunchLook's "founder-curated" + "Testers" cast can outflank them on emotional differentiation while the field is still small. Move now: (1) ship the free 3-finding hook to match their $1 floor, (2) write the "I personally reviewed 100 vibe-coded apps and here's what I found" content piece (Marc Lou playbook), (3) **launch on Product Hunt with a side-by-side comparison** that shows persona-tagged findings the AI alone misses. PageLens has no human in the loop — that's the lever.

2. **Fiverr/Upwork "UX audit" gigs (~$50-$200 tier).** Vulnerable because trust has cratered as AI-slop infiltrates the platform; turnaround is days, not hours; quality is variable. **LaunchLook at $49 with founder spot-check + branded PDF + 24-hour turnaround eats this segment without competing on price.** Timeline: 3 months once distribution is dialed in. The play: (a) buy 5-10 Fiverr UX audits yourself, screenshot their outputs vs. yours, post the comparison. (b) Run Google Ads on "Fiverr UX audit" — Fiverr buyers have wallet open, AI-slop is the wedge. (c) List on Indie Hackers + r/SaaS as the antidote to "I paid $25 and got a ChatGPT printout."

3. **The OSS "vibe-X" cohort (vibesafe, vibescore, vibeaudit).** They have stars but no buyers. **Uprootable via "we run all 39 vibesafe rules plus 60 more, vetted by a human, delivered as a PDF, for $19."** Timeline: 3 months. The play is to **explicitly cite their rule libraries** ("includes all 39 Vibe Audit rules plus...") and pull their audience into your funnel via SEO and direct shoutouts. They're free tools; people want a finished report.

4. **(Stretch) Dan Kulkov ($99 video roast).** Probably *not* uprootable — Dan has the Marc Lou endorsement and 300+ landing pages, plus a personality moat. But LaunchLook can **flank with a hybrid** — "AI scan ($49) + human roast ($150) for $179 total" — and offer the bundle to Dan's wait-listed customers (he delivers in 24h; you can deliver in 1h). Don't replace Dan; partner-adjacent.

### 4.3 Three highest-leverage feature bets (vs. three to skip)

**BUILD (high leverage, proven elsewhere):**

1. **Free 3-finding hook (already queued — ship first).** Validated by Launly's 135 PH votes, PageLens's $1 scan, VibeDoctor's free tier, SchemaReports's free audit. The market has standardized on this as the front door. Without it, LaunchLook starts every customer conversation at a $19 disadvantage. **This is the single most important shipping priority.**

2. **Persona-tagged findings ("The Testers" cast — already queued).** PageLens shipped "persona reviews" already and it's their most distinctive feature in screenshots. LaunchLook's planned "Testers" cast is more emotionally rich (named characters vs. generic personas). **Brand-defining feature. Build it next.**

3. **MCP server / Cursor integration.** PageLens shipped this in 2026 and it positions them inside the workflow. LaunchLook should ship an MCP server so the buyer can ask Claude inside Cursor "what should I fix from my LaunchLook scan?" — this creates a *second* moment of value after the PDF. Low cost, high differentiation against the OSS cohort that doesn't have MCP infrastructure.

**SKIP (graveyard — competitors have proven these don't move the needle):**

1. **Subscription tier ("Watch") — defer past initial launch.** VibeDoctor went subscription-only and slowed their conversion (one-off buyers won't commit). The market signal is one-off + occasional re-scan, not monthly billing. **Ship "Confidence Check" (paid re-scan) as a one-off add-on, not a subscription, until you have 100+ paying customers asking for monitoring.**

2. **Verified-badge embed.** PageLens shipped this on Weekly Monitor; almost nobody embeds these in 2026. SSL-padlock and TrustPilot won; vendor-vanity badges lost.

3. **Multi-model AI consensus.** "We ran your site past Claude + GPT + Gemini" sounds smart and adds zero conversion. Computationally expensive, marketing-flat. Use Claude Sonnet 4.5 alone and put the savings into curation depth.

### 4.4 Pricing reality check

LaunchLook's $19 / $49 / $99 ladder is **directionally right but mispriced at the bottom**. Cross-checking:

- **PageLens AI:** $1 / $15 / $29. LaunchLook is **6-20× more expensive per tier**, with no clear feature delta in the buyer's mind (both deliver markdown export + PDF + 25+ findings). At Starter, the PageLens $1 trial *is* the comp.
- **VibeDoctor:** Free / $15 / $49 / $129. Same shape, lower entry.
- **SchemaReports:** $19 / $49 / $99 — **identical ladder, validates the upper tiers** for tracked-site/monitoring use cases. This is your strongest pricing precedent at $99.
- **Dan Kulkov:** $99 (human, 20-min video). Pro tier comp — buyers comparing LaunchLook Pro to Dan need to understand the AI + curation hybrid value clearly.
- **Olly:** $350 (human, 15-min video, 850+ done). Validates a $200-300 "Pro+" or "Founder Roast" tier above current Pro.
- **fffuel:** $89 (human video). Same comp as Dan.

**Concrete pricing recommendations:**

1. **Replace the $19 Starter with a $0 / $5 / $9 entry** to match the genre's $0-$5 hook standard. The 5-findings cap is fine; the price is wrong. Even **$9** would beat every direct AI competitor on margin while staying above OSS noise.
2. **Hold $49 Full** — this is the sweet spot validated by SchemaReports, MakerBox bundle pricing, and Fiverr midpoint.
3. **Hold $99 Pro** — validated by SchemaReports, Dan Kulkov.
4. **Add a $199-$249 "Founder Roast"** that bundles AI audit + a Rob-recorded Loom walkthrough (your current Pro deliverable, productized + premium-priced). Fills the gap between LaunchLook Pro ($99) and Olly ($350). Caps your delivery capacity (you can only do so many Looms/week), but each one converts referrals.
5. **Eventually a $19-29/mo "Watch" tier** for repeat re-scan + regression detection — but only after 100+ one-off buyers ask for it. **Do not lead with subscription.**

### 4.5 Distribution lessons (solo founder, no ad budget)

What worked for the winners in this segment:

- **Marc Lou's playbook (works):** Build in public on X, sell the founder personality, document revenue publicly. He's at $90K/mo solo and influences Dan Kulkov's bookings. Indie founders in this segment trust other indie founders. **Rob should be tweeting his vibe-coded findings library and dogfooding LaunchLook on his own old projects.**
- **VibeDoctor's playbook (works):** PRLog press release + Bolt Discord + Indie Hackers post + Reddit r/vibecoding. Free version as the hook. The press release was the single distribution event documented in their origin story. **Replicable for $0-$300.**
- **PageLens's playbook (mixed):** Blog content about dogfooding ("we audited our own site"), MCP server launch as a content event. Strong content; unclear traction. Worth borrowing the content idea.
- **Olly's playbook (works):** 850+ landing page roasts as proof; specific guarantee ("if conversion doesn't go up, I refund"); long-form testimonial library. **Refund guarantee converts at the $99-$350 tier.**
- **Dan Kulkov's playbook (works):** Marc Lou's tweet endorsement was the inflection point. **One influencer endorsement in this segment is worth more than 6 months of ads.** Rob should aim for Marc Lou, Pieter Levels, or Dan himself to mention LaunchLook on X.

What didn't work:
- **Product Hunt alone.** Top-5 PH finishes give 2,000-3,500 visitors at 1.5-3.5% conversion = 30-120 free signups. Not enough. Multiple PH launches (one for each major feature) compound better than a single hero launch.
- **Cold outreach for $19-$99 SaaS.** Math doesn't work — average vibe coder is on X / Reddit / Discord, not LinkedIn. Don't waste cycles on cold email at this price point.
- **Enterprise content.** Hordus.ai, FullStory, Baymard all over-index on enterprise content marketing. Not your buyer.

**Top 3 actions for Rob this quarter:**
1. Ship free 3-finding hook → tweet a side-by-side "I audited 10 Lovable apps free — here's the worst finding" thread weekly.
2. Get on the Bolt + Lovable + Cursor Discords; offer one free Pro audit per week to a community member, document publicly.
3. Pitch Marc Lou / Pieter Levels / Dan Kulkov on giving them a free founder roast in exchange for a tweet if they like it. Asymmetric upside.

---

## 5. Per-Competitor Deep Dives (Top 5)

### 5.1 PageLens AI — the twin

PageLens AI is the most dangerous competitor LaunchLook will face. Same audience (vibe coders shipping with Lovable/Bolt/Cursor), same workflow (URL in → markdown export for AI agents), same scan-time promise (5 minutes), same "AI-built apps" framing. They shipped a $1 Launch Scan, a $15 25-page audit, and a $29 desktop+mobile pack — pricing below LaunchLook at every tier. They shipped an MCP server and a "dogfood loop" blog post. They have persona reviews already. Public reviews are zero (Wavel.io) — meaning either they're early or they haven't generated reviews yet. **The good news:** they look like a tool, not a person. They have no founder face on the site, no "I personally reviewed X apps" content, no roast-culture energy. **LaunchLook's wedge:** founder-curated spot-check + "Testers" cast + Loom walkthrough at Pro = an emotional brand layer they don't have. **Move within 90 days or they own the SEO.**

### 5.2 VibeDoctor — the engineering-heavy threat

Solo-founder origin story (Patna, India), shipped May 6, 2026 via PRLog with "129+ checks in 30 seconds." Free tier with 3 scans/day, paid tiers from $15/mo. Strongest technical depth in the cohort (Gitleaks, Trivy, SonarQube, ESLint all under the hood). Real testimonials on pricing page from indie devs ("VibeDoctor caught exposed keys before prod"). **Weakness:** subscription-only model misfits the one-off indie buyer; brand "VibeDoctor" is generic and crowded by 8+ "vibe-X" tools that confuse the market. **LaunchLook's wedge:** one-time pricing, founder narrative in English, no GitHub repo required (live URL works for the Lovable-only buyer).

### 5.3 SchemaReports — the pricing precedent

Uncannily uses the **identical $19 / $49 / $99 ladder** for AI-search visibility audits. Free tier (1 audit/mo). GoHighLevel integration suggests they target agencies as well as direct buyers. They validated that this exact pricing ladder works in adjacent territory. **They are not direct competition** — their wedge is "your site for AI search," LaunchLook's is "your site for customers." But their existence confirms LaunchLook's pricing isn't crazy at the upper tiers. **Action: study their PDF format and free-tier funnel; their entry is broader than LaunchLook's.**

### 5.4 Dan Kulkov / MakerBox — the Pro-tier comp

$99 one-time, 20-minute video roast, 300+ landing pages roasted, Marc Lou's go-to. **Conversion-rate-or-refund guarantee.** This is the price-equivalent product to LaunchLook Pro ($99 with Loom walkthrough). Dan's wedge is pure human expertise (20 years of CRO knowledge in his head). LaunchLook Pro's wedge is **AI breadth (40 findings, integrations review) + human curation (Rob's spot-check + Loom)**. The honest pitch is: Dan finds the 5 highest-leverage problems by intuition; LaunchLook finds 40 problems with AI breadth and prioritizes them with human judgment. **Buyers should choose LaunchLook when they want comprehensive coverage; Dan when they want pure tactical CRO opinion.** Both can coexist; do not try to be Dan.

### 5.5 Cursor Bugbot — the workflow-adjacent gorilla

Not direct competition, but the gravitational pull is real: every vibe coder eventually opens Cursor. Bugbot's new $1-1.50/PR billing (May 2026) makes it accessible to indie devs; "high effort" finds 35% more bugs. **The risk to LaunchLook:** Cursor could ship "Bugbot for URLs" (scan the deployed app, not just the PR) in 2026-2027. Mitigation: **own the buyer relationship before Cursor does.** Bugbot lives in the IDE; LaunchLook should live in the buyer's email + PDF library, with an MCP server as the bridge. If the buyer's first audit memory is Rob's PDF, they will pay $49 even if Cursor later ships free URL scans (because they have brand trust). If the buyer's first memory is Bugbot's PR comment, LaunchLook becomes irrelevant.

---

## 6. Appendix: Notable Quotes & Sources

**On vibe-coded apps failing in production:**
> *"In February 2026, security researcher Taimur Khan found 16 vulnerabilities — 6 of them critical — in a single Lovable-built app. That one app leaked data from over 18,000 people."* — Level Up Coding ([gitconnected.com](https://levelup.gitconnected.com/vibe-coding-wont-replace-engineers-it-s-creating-a-new-kind-of-tech-disaster-b0f5780c21e8))

> *"AI-generated code... at 2.74× the rate of [hand-written code]. 9% had at least one High or Critical finding."* — VibeDoctor founder story ([vibedoctor.io/blog](https://vibedoctor.io/blog/solo-founder-production-readiness-platform-ai-coders))

> *"Zhao et al. (2025) tested AI coding agents on 200 real feature requests... over 80% of functionally correct solutions contained security vulnerabilities."* — Equixly ([equixly.com](https://equixly.com/blog/2026/04/07/vibe-coding-security/))

**On the founder-personality distribution lever:**
> *"I never launch without Dan's roasting."* — Marc Lou, [LinkedIn post 2024](https://www.linkedin.com/posts/marclouvion_codefast-landing-page-converts-like-crazy-activity-7269032519889494016-97jB) (Marc Lou has ~200K LinkedIn followers and $90,790/mo revenue per his own copy)

**On PageLens AI's positioning:**
> *"What used to require a senior performance consultant, a six-week engagement, and a five-figure invoice now takes five minutes and starts at $1."* — [PageLens AI scoring page](https://www.pagelensai.com/score)

**On the converged "markdown for AI agents" format:**
> *"A Markdown export that we built specifically for AI coding agents — no chrome, no screenshots, just findings, stable rule IDs, evidence and suggested fixes, in the format Claude / Cursor / Copilot Workspace / Codex actually parse cleanly."* — [PageLens dogfood loop blog](https://www.pagelensai.com/blog/dogfood-loop)

**On Cursor Bugbot effectiveness:**
> *"With default effort, Bugbot finds 0.7 bugs per run, on average. Over 79% of these bugs are resolved by users at merge time."* — [Cursor changelog May 11, 2026](https://cursor.com/changelog/05-11-26)

**On the Lighthouse/PageSpeed entrenchment:**
> *"PageSpeed Insights is probably the most widely-used website performance tool. Google provides it for free and promotes it to website operators as the best place to start."* — DebugBear

**On Microsoft Clarity's free moat:**
> *"Pricing: $0. Data retention: 30 days, fixed. ...completely free with no usage caps, providing unlimited heatmaps and session recordings for any site."* — Multiple sources (luniq.io, devtoolpicks.com)

**On Launly's Product Hunt traction (signal for free-audit appetite):**
> *"▲ 135 votes, 20 comments. Launched May 12, 2026."* — Launly Free AI SEO Auditor on Product Hunt

**Key sources consulted (full list):**
- pagelensai.com (pricing, blog, FAQ, scoring)
- vibedoctor.io (pricing, checks, founder blog, PR launch)
- zeriflow.com, vibesafe.io, codeqa.aivyuh.com
- cursor.com (Bugbot docs + May 2026 blog + changelog)
- vibe-eval.com, pypi.org/project/vibeval
- schemareports.com, auditaiseo.com, launly.com, hordus.ai
- makerbox.club/landing-page-roasting (Dan Kulkov)
- roastmylandingpage.com (Olly Meakings)
- fffuel.co/rrroast (Sébastien)
- baymard.com, uxaudit.now, maze.co
- snyk.io, detectify.com, stackhawk.com
- clarity-insights.com, propicked.com, luniq.io (analytics comparisons)
- developers.google.com/speed/docs (PageSpeed Insights)
- wappalyzer.com (tech detection)
- Fiverr Tutorials (gig pricing landscape)
- Equixly, gitconnected.com, getautonoma.com (vibe-coding failure documentation)
- GitHub repos: vibesafeio/vibesafe-action, slowcoder360/vibesafe, stef41/vibescore, jackdog668/vibeaudit, csmoove530/vibe-codebase-audit, benavlabs/vibe-check, crucible-security/crucible, patheonsceo/IsItSafeBro

**Flagged for Rob to validate (no public traction data found):**
- PageLens AI customer count / MRR
- VibeDoctor scan volume / customer count
- ZeriFlow paid pricing tiers
- VibeEval pricing
- Roast My Web actual sales numbers

---

*End of report. Length: ~3,300 words.*
