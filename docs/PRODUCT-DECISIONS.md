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
| Handoff Report for Starter / Scale Up | $49 add-on | Pro tier already includes it. Dropped from $99 on 2026-05-26 to slot into the upsell ladder: Scale Up + Handoff = $98, intentionally $1 below Pro $99. Old $99 add-on made the bundle $148, above Pro, so it never sold. |

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
- **Handoff Report.** A standalone PDF designed to be handed to a developer or contractor, with technical context the main report deliberately strips out. Pro only by default; $49 add-on for Starter and Scale Up buyers (dropped from $99 on 2026-05-26 — see §9 change log).
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
| 2026-05-26 | Handoff Report add-on dropped from $99 → $49 (autonomous batch worker). Anchoring math: Scale Up $49 + Handoff $49 = $98, sits just below Pro $99, intentional upsell ladder. Old bundle was $148 (above Pro), so the add-on never sold. New Stripe Payment Link `plink_1TbNP9BxCiPye3m0c5A1DNfq` (URL `https://buy.stripe.com/3cIdR864B3nu7Rx4Gk3cc06`) wired into `landing/assets/config.js` `stripe.handoff`. Webhook routing was already metadata-first (`product=handoff_report`); the `HANDOFF_REPORT_CENTS_TO_LABEL` dict gained a `4900` entry. Landing copy, FAQ, deliver_report.py, share_report.py, and consistency_check.py all updated to read `$49`. |

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
