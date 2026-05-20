# Onceover — Product Specification

## The product

Onceover is a paid pre-launch checkup service for vibe-coded web apps. A founder pays, sends their URL plus a short intake form, and receives a Notion page with:

- A summary verdict (overall ready / needs work / not ready)
- A prioritized list of 5-10 findings (Critical / High / Medium / Low severity)
- For each finding: plain-English explanation, screenshot evidence, and a copy-paste fix prompt for their AI builder
- (At higher tiers) An AI-generated one-page Quick Start Guide for their users
- (At highest tier) A follow-up verification scan after fixes

## Three tiers

### Quick Checkup — $7

- 5-7 findings
- Mobile and desktop spot-check
- Plain-language explanations
- Copy-paste fix prompts
- Notion page delivery
- 24-hour turnaround

Used by: founders unsure whether the product is for them. The impulse-purchase entry point.

### Launch Pack — $29

- Everything in Quick Checkup, plus:
- Full checkup (10-15 findings instead of 5-7)
- Cross-user data check (with two test accounts the founder provides)
- AI-generated one-page Quick Start Guide for their users
- 12-hour turnaround
- Shareable Notion link they can send to teammates

Used by: founders actively launching and willing to invest in doing it right. This is the centerpiece tier.

### Launch Pack + Polish — $59

- Everything in Launch Pack, plus:
- Follow-up verification scan after the founder applies fixes
- Email check-in 7 days after launch with offer to spot-check customer feedback
- Custom touchups to the Quick Start Guide based on founder feedback

Used by: founders who want hand-holding. The premium upsell.

## What's in scope

- **Polish**: broken buttons, broken links, console errors, network failures, mobile layout breaks
- **Placeholders**: leftover lorem ipsum, default platform copy, "Your Company Name," bracket placeholders, placeholder emails
- **Trust pages**: missing /privacy, /terms, /contact
- **Basic permissions**: cross-user data visible, logged-out access to protected routes
- **UX states**: missing empty states, missing error states, missing loading states
- **Sharing**: missing meta tags, default favicons, generic page titles
- **Brand consistency**: inconsistent terminology, mixed capitalization, leftover platform branding
- **The Quick Start Guide** (at $29+ tiers): one-page user-facing doc generated from crawled content plus founder intake

## What's out of scope (and why)

- **Deep security scanning** — VAS, VibeEval, and Escape.tech compete here at a level we can't match. We'll partner with them, not compete.
- **Code-level audits** — Sherlock Forensics, Beesoul, and others charge $1,500+ for human code review. Different product, different buyer.
- **Multi-page help centers** — A one-page Quick Start is the right MVP scope. Multi-page docs are a future product.
- **Auto-fixing issues** — We give fix prompts, not patches. The founder applies them via their AI builder.
- **Continuous monitoring** — One-time scans only at MVP. Continuous is a v2 offering.
- **Mobile apps (iOS/Android)** — Web only.
- **Backend / API security testing** — Out of scope. Recommend a security tool as a complement.

## Positioning

**Tagline**: A friendly pre-launch checkup for your vibe-coded app.

**One-sentence pitch**: Send us your app's URL. We'll spot what your users will notice, write you a fix list you can paste into Lovable, and draft a one-page guide your users can actually read.

**Differentiation from competitors**:
- Sounds like a friend, not a security tool. Plain language, no jargon.
- Covers polish and UX, not just security.
- Includes user-facing documentation generation (unique).
- Priced for impulse purchase, not enterprise procurement.
- Manual quality control via human-curated reports, not pure automated scans.

## Voice and tone

- Warm, plain, second person.
- No marketing words: leverage, seamless, robust, innovative, cutting-edge, powerful, streamline.
- Active voice over passive.
- Short sentences. Concrete verbs.
- Acknowledge that vibe coders are smart people building real things — never condescending.
- Acknowledge what AI builders do well — they're not the enemy.
- Reference UI elements by their actual visible label, in quotes, not internal names.

## What success looks like at each timescale

### Week 1
- Domain bought, landing page live, Stripe live, first 5 cold outreach Looms sent.

### Week 2
- First paying customer. First delivered report.

### Month 1
- 3-5 paying customers. Findings Library has 10+ new entries beyond the seed 35.

### Month 2
- 8+ paying customers. Quick Start Guide prompt producing near-ready docs with minimal editing. First referral.

### Month 3
- 15+ paying customers. Playwright crawler doing initial data capture. Price test underway.

### Month 6
- 50+ paying customers. Recurring revenue from re-checkups. First case study published. Considering v1 features.

## Out of scope for MVP, on roadmap for later

- Automated scanner UI (customer types URL on website, scan runs automatically, report appears in dashboard) — v1, after customer 30
- Continuous monitoring subscription — v2
- Agency white-label tier — v2
- Browser extension — never
- Integration with vibe coding platforms' APIs — v2 at earliest
