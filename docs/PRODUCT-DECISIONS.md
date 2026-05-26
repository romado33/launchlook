# Product Decisions

Canonical reference for tier structure, pricing, deliverables, dropped ideas, deferred ideas, and competitive positioning. Future workers read this before reintroducing anything we explicitly killed, before adding tiers, or before opening a new competitive front.

Companion docs:
- `SIMPLICITY-GUARDRAILS.md` (the brand discipline rules)
- `TESTERS-CAST.md` (the 7 personas)

---

## §1 Tier ladder (canonical)

The tier ladder is **fixed at 4 tiers**: Free / Starter / Scale Up / Pro. Do not add a 5th. Do not rename one. See §3 for what we explicitly killed.

| Tier | Price | Findings cap | Verified badge validity | Key deliverables |
|---|---|---|---|---|
| Free | $0 | 3 (top severity only) | none | Email-gated. Used as lead magnet. |
| Starter | $19 | 10 | 30 days | Main Report PDF, QSG PDF, 30-day Verified badge |
| Scale Up | $49 | 30 | 90 days | + cross-user data isolation check, comprehensive checklist PDF |
| Pro | $99 | 40 | 180 days | + integrations review, recorded Loom walkthrough, Handoff Report, GitHub integration (when shipped), deep links in QSG |

### Add-ons (any paid tier)

| Add-on | Price | Notes |
|---|---|---|
| Confidence Check re-scan | $19 standalone, $9 within 14 days of original audit | Free 1x with Pro. |
| Badge re-verification | $9 per re-check | Future "always verified" subscription planned at $19/year. |
| Handoff Report for Starter / Scale Up | $99 add-on | Pro tier already includes it. |

### Webflow SKU

Identical tier structure and identical pricing as the main SKU. Different `/webflow` landing page. Platform-aware fix prompts (Webflow-specific actions, not generic web). Treat Webflow as a parallel SKU, not a new tier.

---

## §2 Free → Starter deduplication rule

When a buyer used the free hook (top 3 findings) and then upgrades to Starter for the same email + URL within 90 days, the AI must surface **10 NEW findings**, excluding the original 3.

- UX promise: "You're not paying $19 just to re-read your free preview."
- Storage: finding fingerprints (severity + brief description hash + element selector hash) per email + URL combo, kept in Notion.
- Window: 90 days from the original free audit. After 90 days, the site has likely changed; full audit re-runs without dedup.
- This rule is non-negotiable. Free → Starter conversion is the most fragile moment in the funnel; reusing findings would burn it.

---

## §3 Deliberately DROPPED ideas

These were considered, then killed. Do **not** reintroduce any of them without explicit user approval. If a future worker (human or agent) is about to ship one of these, stop and escalate.

- **Founder Roast tier ($229)**, dropped May 26, 2026. Reason: simplicity discipline plus operational burden (booking system, Discord follow-up, live calls). Top tier is Pro at $99. (See `SIMPLICITY-GUARDRAILS.md` §2.4.)
- **5th tier of any kind.** Cap is 4 (Free / Starter / Scale Up / Pro).
- **A/B testing module.** Wrong product shape (continuous, not pre-launch). Vacuum already filled by VWO + Statsig + GrowthBook + Mida and 7 others.
- **Hotjar / Crazy Egg replacement.** Microsoft Clarity is free forever, Microsoft-backed. Unwinnable.
- **GEO / AI-visibility tracking (Lorelight-style).** The prior winner (Lorelight) shut down Oct 31, 2025 with a post-mortem saying "the problem didn't need solving." We will not run that experiment again.
- **Generic free SEO audit.** PageSpeed + Ahrefs Free + SEODiff + FreePageRank + Launly already filled the space.
- **Lighthouse CI replacement.** Wrong audience. CI users are devs, not vibe coders.
- **Spec / Requirements helper (pre-build).** Different product wedge. Park as a future sibling product, NOT mixed into LaunchLook.
- **App-store compliance product.** Different platform (mobile + marketplaces). Future sibling product, not LaunchLook.
- **Migration helper ("Vibe Code Exit Plan").** Needs codebase / repo access. Different security model. Defer until 50+ customers ask for it.

If a worker has a strong case to revive one, write a separate proposal note and ping the user. Do not silently re-add.

---

## §4 Deliberately DEFERRED ideas

These are queued, not killed. They ship when their criteria are met, not before.

| Idea | Trigger to revisit |
|---|---|
| Watch subscription tier | Defer until 100+ paying one-off customers ask. VibeDoctor's subscription-only model is converting worse than one-off competitors. |
| Site-builder expansion beyond Webflow (WordPress, Squarespace, Wix, Framer, Shopify) | Defer until ≥30 paying vibe-coder customers AND the Webflow SKU validates. Most of these platforms are saturated or structurally wrong. |
| GitHub Marketplace App (LaunchLook as a GitHub App) | Defer until ≥30 paying customers AND the audit pipeline holds at higher volume. |
| Cross-user isolation as a standalone SKU | Defer until 30+ paying customers ask for it specifically. Currently bundled in Scale Up and Pro. |
| Linear / Asana / ClickUp / Slack webhook integrations | Defer until customer-requested. |
| Notion delivery option | Parked. Revisit when the Pro tier has ≥10 customers. |

When you ship any of these, move the row from §4 to a new "Shipped" section at the bottom of this file with a date.

---

## §5 Competitive positioning (canonical)

### Entrenched competitors: do NOT compete head-on

- **PageSpeed Insights / Lighthouse / Microsoft Clarity.** Free, Google / Microsoft-backed. We will lose any "faster than Lighthouse" framing.
- **Cursor Bugbot.** Owns the IDE / PR workflow. We do not live in the IDE.
- **Snyk.** Owns DevSecOps mindshare. We do not pretend to be a security platform.

LaunchLook's wedge is **the translator + curator**. Never "faster than Lighthouse." Never "deeper than Snyk." We translate raw signal into a plainspoken, prioritized PDF a non-technical buyer can act on.

### Uprootable competitors (with windows)

| Competitor | Window | How we uproot |
|---|---|---|
| **PageLens AI** | 6 months (closes Q3 / Q4 2026) | Closest twin. Uproot via founder-curation + Testers cast + plainspoken brand voice. |
| **Fiverr / Upwork UX-audit gigs** ($50–$200) | ~3 months | Trust cratered from AI-slop output. LaunchLook eats this via comparison content. |
| **OSS "vibe-X" cohort** (vibesafe, vibescore, vibeaudit) | Ongoing | Stars but no buyers. Cite their rule libraries directly, then offer "all their checks plus 60 more, human-vetted, PDF, $19." |

If a new competitor appears in the "uprootable" lane, add a row above. If a new competitor appears in the "entrenched" lane, do not add a row: write a strategy note instead and escalate to the user.

---

## §6 Brand positioning one-liner

> **"PageLens is a scanner. LaunchLook is a scanner with judgment."**

Use this exact phrasing in `/vs-pagelens`, in comparison content, and in founder-voice copy. Do not paraphrase. Do not soften it.

---

## §7 Pricing rationale

Each tier price is intentional. Re-evaluate only against the trigger noted, not on instinct.

- **Free $0.** Top-of-funnel hook. Closes the $0–$5 entry gap PageLens occupies at $1. Email-gated for lead capture.
- **Starter $19.** Impulse buy, sub-$20 psychology. Re-evaluate after 4 weeks of free → Starter conversion data; consider dropping to $9 only if conversion stalls below target.
- **Scale Up $49.** Matches SchemaReports's mid-tier identically. Full offer for serious pre-launchers (cross-user isolation check, full checklist).
- **Pro $99.** Anchors the upper end. Matches Dan Kulkov's roast price. Includes recorded Loom + integrations review + Handoff Report. This replaces the killed Founder Roast tier (see §3).

Pricing is fixed across both the main SKU and the Webflow SKU. Do not introduce platform-specific pricing without explicit user approval.

---

## §8 Deliverable definitions (canonical)

So future workers don't quietly re-scope what each tier ships, here is the binding definition of every deliverable referenced in §1.

- **Main Report PDF.** The customer-facing audit. Verdict, findings (sorted by severity), one-page "if you only fix three things" summary. Plain-English titles, founder voice. Bound by `SIMPLICITY-GUARDRAILS.md` §3. Ships at Starter, Scale Up, and Pro.
- **QSG PDF.** Paste-ready fix prompts ordered by severity, self-contained. Deep links allowed at Pro tier when the buyer's AI builder supports them. Bound by `SIMPLICITY-GUARDRAILS.md` §4. Ships at Starter, Scale Up, and Pro.
- **Verified badge.** A signed badge confirming an audit passed on a given date, validity window per tier (30 / 90 / 180 days). Re-verification is a $9 add-on (see §1).
- **Comprehensive checklist PDF.** The full pre-launch list. Customer-facing copy says "full checklist" or "launch checklist" (per `SIMPLICITY-GUARDRAILS.md` §6 vocabulary rules). Ships at Scale Up and Pro.
- **Cross-user data isolation check.** Verifies that one logged-in user cannot read or modify another user's data. Bundled in Scale Up and Pro. Standalone SKU is deferred (see §4).
- **Integrations review.** A pass over any third-party integrations the buyer is using (auth, payments, email, analytics) for misconfiguration. Pro only.
- **Recorded Loom walkthrough.** Rob walks the buyer through the report and the top three fixes. 5 to 10 minutes. Pro only. Not live; not a Founder Roast (see §3).
- **Handoff Report.** A standalone PDF designed to be handed to a developer or contractor, with technical context the main report deliberately strips out. Pro only by default; $99 add-on for Starter and Scale Up buyers.
- **GitHub integration.** When shipped, opens findings as PRs. Pro only. Currently deferred (see §4) until pipeline holds at higher volume.

If a future worker is about to ship something not on this list as part of a tier, that is scope creep: stop and escalate.

---

## §9 Change log convention

When you change anything in this file:

1. Add a one-line entry below with date and rule reference.
2. If you killed something, move it to §3.
3. If you deferred something, move it to §4 with its trigger.
4. If you shipped a deferred item, move it to a "Shipped" section with date.

| Date | Change |
|---|---|
| 2026-05-26 | Initial canonical doc. Founder Roast ($229) tier dropped same day; top tier locked at Pro $99. |
| 2026-05-26 | Added §10 (Analytics goals tracked). Plausible installed across all landing pages. |
| 2026-05-26 | vs-pagelens comparison page shipped at `/vs-pagelens`. SEO + FAQ destination only, not in main nav. Inherits §2.7 (no nav link). One FAQ entry added to `/` and `/webflow` per §2.7 + §6 (neutral, no SaaS-speak). |
| 2026-05-26 | q3b shipped: AI-sounding copy detection, Scale-Ready audit (Scale Up+), Compliance-Lite finding categories added to the data-driven taxonomy in `scripts/ai_audit/finding_categories.yaml`. Buyer-facing names per `SIMPLICITY-GUARDRAILS.md` §6: "copy that sounds AI-written," "growth-readiness checks," "common legal must-haves." Internal names (Scale-Ready, Compliance-Lite, AI-sounding copy detection) stay inside dev docs and the YAML's `display_name_internal` field only. |
| 2026-05-26 | q14+q16+q20 shipped: `performance_speed` finding category (Core Web Vitals translator via PageSpeed Insights API, 24h cached) and `accessibility_checks` finding category (axe-core 4.10 injected into Playwright) added to the data-driven taxonomy. Buyer-facing names per `SIMPLICITY-GUARDRAILS.md` §6: "performance & speed" and "accessibility checks." Internal names (Core Web Vitals, LCP, INP, CLS, axe-core, WCAG) stay inside dev docs and YAML `display_name_internal` only. AI-builder deep links (Cursor / Lovable / Bolt / v0 / Webflow) added to `templates/qsg/qsg.html.j2`, gated to the Pro Package tier per §1. Never marketed on `landing/index.html` or `landing/webflow.html` per `SIMPLICITY-GUARDRAILS.md` §2.5 + §6. |
| 2026-05-26 | q6 shipped: Confidence Check / Saboteur re-scan add-on ($19 standalone / $9 within 14 days of last audit), available to all paid tiers. Lives BELOW the main pricing grid on `landing/index.html` and `landing/webflow.html` per `SIMPLICITY-GUARDRAILS.md` §2.6 (add-on, not a competing tier). Stripe webhook routes confidence_check metadata to a separate Notion Confidence Checks DB; new pipeline at `scripts/confidence_check.py`; short-form PDF via `templates/confidence_check/`. See `CONFIDENCE-CHECK-WORKFLOW.md`. |
| 2026-05-26 | q19 shipped: GitHub integration for Pro tier (opt-in, manually triggered by Rob, never auto-runs from delivery pipeline). One issue per finding tagged with the persona that caught it; optional PR summary comment when the audit was triggered against a PR. Customer surfaces touched: one bullet in the Pro tier card on `landing/index.html` + `landing/webflow.html`, and one conditional paragraph in the post-purchase delivery email per `SIMPLICITY-GUARDRAILS.md` §2.5 (integrations invisible on the main landing). Library: `scripts/github_integration.py`. CLI: `scripts/github_push.py`. Full setup + failure-recovery docs at `docs/GITHUB-INTEGRATION.md`. |
| 2026-05-26 | q5+q13 shipped: persona tagging extended from Snoop-only to all 7 Testers across the report PDF (`templates/report/report.html.j2`), the AI generation pipeline (`scripts/ai_audit/prompts/system.txt`, `scripts/ai_audit/llm_client.py`, `scripts/ai_audit/pipeline.py`), and the audit_ui review form (`scripts/audit_ui/`). Lean "Made by Rob" founder section added below pricing on `landing/index.html` and `landing/webflow.html` (placeholder photo at `landing/images/rob.jpg`, real headshot tracked in `docs/ROB-REMAINING-TODO.md`). Small "Meet the cast" footer tooltip added to `landing/index.html`, `landing/webflow.html`, `landing/sample.html`, `landing/checklist.html` per `SIMPLICITY-GUARDRAILS.md` §2.6 (footer tooltip, never a hero section), §2.9 (founder bio is 2 to 3 sentences with a photo, not a hero), §3.4 (persona tags subtle on findings), and §6 (no em-dashes, no corporate vocab). |

---

## §10 Analytics goals tracked

Conversion measurement via Plausible (privacy-friendly, no cookie banner needed per `SIMPLICITY-GUARDRAILS.md` §2). Goals:

- `FreeAuditSignup` — free 3-finding audit form submission
- `StarterCheckout` — Starter $19 button click
- `ScaleUpCheckout` — Scale Up $49 button click
- `ProCheckout` — Pro $99 button click
- `IntakeFormStart` — Tally intake form opened
- `RescanAddOn` — Confidence Check re-scan CTA click

Page views auto-tracked: `/`, `/webflow`, `/sample`, `/checklist`, `/thanks`, `/privacy`, `/terms`, `/vs-pagelens` (when live).

Funnel of interest: page view → free audit → Starter checkout → Scale Up upsell.
