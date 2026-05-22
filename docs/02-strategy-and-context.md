# LaunchLook — Strategy and Context

## Why this product exists

The vibe coding ecosystem (Lovable, Bolt, Base44, Replit, v0) is growing explosively. Lovable hit $400M ARR; 87% of Fortune 500 companies have adopted at least one vibe coding platform. The ecosystem is producing hundreds of thousands of apps built by non-technical founders.

Research is clear about the problem:
- 380,000 vibe-coded apps publicly accessible online
- Of those, roughly 5,000 leak sensitive data
- 40-62% of AI-generated code contains security vulnerabilities
- Vibe coders frequently ship apps with broken buttons, placeholder text, missing trust pages, and inconsistent UX

The voice-of-customer is unambiguous: founders are scared at the moment of launch. They've built something they're proud of but they don't know what they don't know. They post things like "Guys, I'm under attack — I'm not technical, this is taking me longer than usual to figure out."

## Why the competitive landscape is crowded but has gaps

Multiple competitors already exist in the security-scanning space:
- **VAS (vibeappscanner.com)** — $9-$99/mo, deep DAST security scanning
- **VibeEval (vibe-eval.com)** — agent-based security testing, $19/mo
- **Vibeship (vibeship.co)** — SAST source-code scanning, requires GitHub OAuth
- **Escape.tech** — raised $18M for pentest-replacement scanning
- **Tenzai** — security research and testing for AI-coding tools
- **Sherlock Forensics**, **Beesoul**, **Vibe App Rescue**, **Spring Code** — human-led audits at $1,500+
- **testers.ai / VibeEval** — AI-persona-based functional testing

These competitors share three weaknesses:

1. **They sound like security tools.** Their copy is full of "RLS policies," "endpoints," "authorization checks," "CSP headers." Their target user — a non-technical vibe coder — doesn't speak that language.

2. **They cover security only.** Polish (broken buttons, placeholder text, brand inconsistency) is largely unserved. testers.ai covers some functional issues but targets QA professionals.

3. **They have no documentation generation.** Nobody is generating user-facing Quick Start Guides for vibe-coded apps. CodeGuide targets developer-facing docs, which is a different problem.

LaunchLook wedges into all three gaps simultaneously, while staying out of the security competitors' direct path. We complement them.

## Why manual-first

The instinct to "build a scanner" is wrong for two reasons:

1. **We don't yet know what to scan for.** Building a Playwright crawler before doing 10+ manual audits means coding for imagined issues, not real ones. Manual audits reveal the recurring patterns that justify automation.

2. **The product's voice and judgment is the differentiator.** Pure automated scans produce the same output that VAS and VibeEval already produce, only worse. Our edge is human curation — the editor's voice, the plain-language explanation, the appropriate severity calibration. Automation supports that, doesn't replace it.

Manual-first also matches the constraint: 5 hours/week is enough to deliver 3-4 manual reports plus outreach. It is not enough to build a scanner from scratch. Scanner work is deferred until customer volume justifies it.

## Lessons from comparable products

**Stripe** started with founders personally onboarding the first businesses. The API came later, shaped by what they learned.

**Dropbox** launched as a 3-minute screencast video, not a product. 75,000 signups before code was written.

**Nomad List** was a public Google Sheet for its first year. No auth, no database, no app. Just a spreadsheet that grew.

**Superhuman** did 1:1 onboarding calls for years. Founders personally got customers up and running.

The pattern: do unscalable things first, learn what's actually valuable, then automate. LaunchLook follows this pattern deliberately.

## The 60-day decision point

At day 60, evaluate:

- **8+ paying customers?** Wedge is real. Begin light automation. Consider raising entry tier from $7 to $9 or $12.
- **3-7 paying customers?** Wedge is unclear. Iterate the pitch and outreach script before automation. Run another 30 outreach attempts.
- **0-2 paying customers?** The pitch, audience, or product is wrong. Don't build more. Investigate what's broken in the funnel.

Critical: the quality bar matters more than the quantity. If 8 customers buy but only 2 report it as "useful," the product itself is wrong, not the marketing. Watch this signal carefully.

## Why Starter Package is $9 (updated from early $7 tests)

- Impulse purchase range. Below conscious deliberation.
- Lower than every direct competitor's entry tier.
- Signals "low-stakes check," matching the friendly positioning.
- Creates room for Full Package ($29) and email-quoted follow-ups without sticker shock.
- Generates more customers per outreach attempt, accelerating learning.

Counter-arguments and rebuttals:
- "$7 is too cheap to be taken seriously" — possibly. We'll know by day 30 if conversion rates and qualitative feedback support a raise. The premium tiers ($29, $59) anchor value if buyers are worried about the $7 signal.
- "$7 doesn't pay for the time" — true if it stays manual. Manual delivery at $7 = ~$21/hr. Once automation lands, effective rate jumps to $60+/hr. The $7 tier is an acquisition cost, not a revenue source.

## Why Notion (not a custom dashboard)

- Zero engineering needed.
- Already premium-feeling.
- Customers can comment, share, forward.
- Easy to template and clone.
- Customers don't need accounts; share by link.
- When automation lands, scripts can write to Notion via API without a custom UI.

A custom dashboard is on the roadmap for v1 (after customer 30) only if Notion becomes a friction point.

## Why we publish a free public checklist

The Pre-Launch Checkup checklist (see `04-content-and-copy.md`) is deliberately given away free. Three reasons:

1. **Trust.** Anyone reading it sees we know what we're talking about.
2. **SEO.** "Pre-launch checklist for Lovable apps" is a search term we can own quickly.
3. **Referenceable.** Other content creators (newsletters, YouTubers, Discord mods) will link to it. Each link compounds.

The checklist costs us nothing to maintain. It generates leads forever.

## Pricing levers we can pull later

If $7 isn't converting:
- Raise to $9, $12, $15. Test in 1-week sprints.
- Try free initial scan with paid full report (~$19). Common in competitor space.

If we want subscription revenue:
- Monthly continuous-scan tier at $19/mo (matches VibeEval).
- Bundle 3 scans for $19, with 6-month expiry.

If agency interest emerges:
- White-label tier at $99-299/mo with branded reports.

None of these are MVP scope. Document, don't build.

## Risks and mitigations

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Competitor adds a polish module | Medium | Move fast on Quick Start Guide differentiation; partner with VAS rather than compete |
| Quality of QSG is poor and embarrassing | Medium | Owner is a 15-year tech writer; QA every QSG personally for the first 30 customers |
| Manual delivery doesn't scale | High by design | That's the point — automate after customer 30 |
| $7 attracts low-quality customers | Medium | Tier system funnels serious buyers to $29/$59 |
| Lovable/Bolt add their own pre-launch checks | High eventually | We position around polish + docs, not the security checks they're likely to add |
| Owner burns out at 5 hrs/week | Medium | Strict scope; back-of-house tooling reduces per-customer time; clear go/no-go criteria |
| Vibe coding hype fades | Low (over 60-day horizon) | The ecosystem is too established to collapse in 60 days; reassess at month 6 |
