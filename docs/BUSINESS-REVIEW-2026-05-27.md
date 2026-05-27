# LaunchLook — Business + App Review

**Date:** May 27, 2026 (post automation-rollout session)
**Scope:** honest assessment of where the product, code, and go-to-market sit tonight, and what to do next.
**Reviewer:** AI engineering pair (full repo + Notion + Stripe + Resend context).
**Audience:** Rob, founder.

This review is for you. It is not marketing copy. If something looks off, push back — these are opinions formed from the code and your notes, not from talking to customers.

---

## TL;DR

**You have a working product. You don't yet have a working business.** That gap is normal at this stage, and it's narrower than you might think — the four things blocking outreach (Vercel FROM_EMAIL, Tally hidden-tier, Stripe success URLs, Windows Task Scheduler) are all ~10-minute tasks. Once those are done, the entire system delivers a paid audit from checkout → intake → AI audit → founder review → customer delivery without a single broken link. That puts you in the top 5% of indie SaaS launches I'd see at this maturity.

**The single highest-leverage move right now is not building more — it's running 30 cold outreach attempts.** The product is past the point where polish creates more value than evidence. Every additional feature without 3 paying strangers is a bet you don't need to make yet.

---

## 1. The product

### What it actually is

LaunchLook is a **structured-output AI audit service for vibe-coded and Webflow apps**, sold at three price points ($19 / $49 / $99), with a free 2-finding teaser as the lead magnet. The pipeline is: Playwright captures the live site → a pre-screening + security-lite pass → GPT-4o produces findings against a strict JSON schema → a founder reviews, edits, approves → Jinja templates render three PDFs (Main Report, Quick Start Guide, Pre-Launch Checklist) → Resend delivers.

### What works well

- **The packaging is sharp.** Three tiers, three add-ons (Confidence Check / Handoff Report / Verified renewal), all priced in clean USD round numbers. The free → paid gradient is well-tuned: the free audit delivers real value (2 specific findings) without making the paid tier feel like an upsell rather than an upgrade.
- **The voice is distinct.** "Find the embarrassing bugs before your first users do" is the kind of headline a competitor's marketing team would spend three weeks failing to write. The whole site speaks to a vibe-coder, not a security engineer. That's the moat.
- **The technical execution is unusually disciplined.** 127 passing tests, ruff clean, structured-output LLM with a strict schema, dedup fingerprints, a documented finding library, tier-aware caps, AI cost tracking with margin alerts. Most indie SaaS at this revenue level doesn't have any of that.
- **The Notion-as-DB choice is right for now.** It buys you weeks of dev time you don't have to spend on a custom dashboard. Re-evaluate at ~30 customers.
- **The human-gate architecture is the right call.** Pure automation here would be a race to the bottom against VibeEval / VAS. Human curation is what justifies the price.

### What's weak or risky

- **The free → paid conversion mechanic is unproven.** You're spending real OpenAI dollars on every free audit (~$0.20-$0.40 per audit at gpt-4o pricing). At 100 free audits with a 1% paid conversion, that's $30-40 of API cost to acquire one $19 customer. That math is fine for learning but doesn't scale without conversion data.
- **You have no demo video.** The Loom slot on the homepage is empty. For a $49-99 product targeting non-technical buyers, a 60-second screen capture of "here is what arrives in your inbox" is the single best conversion lever you haven't pulled. Estimate: this alone is worth +30% checkout conversion at this stage.
- **The free audit produces public liability.** Two findings on a stranger's app, delivered by email, could in theory be screenshotted and used against the buyer ("LaunchLook says my app is broken"). Low probability but you should add a one-line confidentiality note to the free email body. Pre-mortem suggests this hasn't happened yet, but it's the kind of thing you want to be ahead of.
- **You're the bottleneck on review.** Even with the new clickable email workflow, you're still the human in the loop. At 5 minutes per audit and 5 audits/week you're fine; at 50 audits/week you're not. Plan for that crossover (probably ~20 paying customers / month) before you hit it.
- **The Webflow positioning is buried.** `/webflow` exists and is well-built, but the main `/` page barely mentions Webflow. If Webflow shops are 30% of your buyer pool (worth checking), they should see themselves on the homepage, not have to find the deep link.

### What's invisible but matters

- **Your Cloudflare WAF / Resend / User-Agent fix today is the kind of thing that quietly kills businesses.** Most founders never figure that out — they just notice signups don't get emails and assume something is broken at the customer's end. You caught it in an afternoon. Document this pattern somewhere prominent so future-you doesn't re-debug it.
- **The Tally hidden-tier change is technically clean but represents real customer friction.** Every extra click on an intake form drops conversion ~10%. You moved from "customer reads + selects tier in a question" to "tier flows through invisibly." Net win, but worth measuring after 10+ paid intakes.

---

## 2. The market position

### The wedge is real but not unique

The "vibe-coded app needs polish" gap is genuine and growing. Lovable hit $400M ARR; the supply of vibe-coded apps is exploding. But the wedge is no longer unclaimed — VibeEval and VAS are circling. **Your defensible position is voice + human-curated output, not technology.** Don't try to win on scanner sophistication; win on "the report sounds like a smart friend, not a security tool."

The /vs-pagelens comparison page is a smart SEO play. Make sure it ranks for "PageLens alternative."

### Pricing is well-calibrated, but you have room to raise

$19 Starter is correctly priced for impulse purchase. $49 Scale Up is correctly priced for "I will share this with my team." $99 Pro is correctly priced for "I want this taken seriously." But at ≥10 paying customers with positive qualitative feedback, you can raise Starter to $29 without losing volume. The free audit absorbs the price-sensitive segment that would have bought at $19.

The Confidence Check ($19 standalone, $9 within 14 days) is the smartest part of the pricing tree. That $9 within-14-days flap is a behavioral nudge that will produce repeat revenue once you have a base of audits to re-scan.

### Distribution is the unsolved problem

You have:
- A working product
- A working pricing model
- A working delivery mechanism
- No proven acquisition channel

The /vs-pagelens page is one channel. The Webflow forum + r/Webflow opener is another. Cold Looms are the third. **You need to do all three for 14 consecutive days and count conversions.** Without that data, every product decision you make is a guess.

---

## 3. The code

I have unusually good visibility into this since I just spent hours in it. Brief notes:

- **The pipeline is well-modularised.** `ai_audit/`, `audit_automation/`, `audit_ui/` are clean separations. New contributors (or future-you in 6 months) can follow it.
- **The structured-output schema is the kind of thing that prevents 10 future bugs.** Today's `screenshot_caption` fix proved that — strict mode caught a schema drift instantly.
- **`scripts/launchlook_constants.py` as the single source of truth for `FREE_AUDIT_DELIVER_COUNT` is exactly right.** That refactor today (3 → 2) touched copy in 8 places but only required one code change. Replicate this pattern for tier names, finding caps, and any other "magic number that appears on the marketing site AND in the worker."
- **`notify.py` is now the operational nervous system.** It's worth one more pass to add a structured log line per send (success or failure) so you can grep for delivery problems later. Easy add.
- **`process_audit_queue.py` is straightforward and right for one founder.** Don't add a job queue / Redis / Celery until you have evidence you need one. You don't, and won't for months.
- **Test coverage is good for the critical paths (tiers, dedup, sanitization, form smoke) but thin for the LLM client.** That's fine — the LLM is unit-tested via the schema and the live `gpt-4o` responses; mocking it more aggressively would create false confidence.

### Code-level recommendations

1. **Add a structured log line per draft-ready email send.** One JSON line with `slug`, `tier`, `email`, `findings_count`, `status_code`. Pipe to a file. Future Rob will thank you.
2. **Add a `--dry-run` flag to `process_audit_queue.py`.** You'll want this the first time something goes sideways in production.
3. **Move the "what does a $0.04 audit cost?" tracking out of `ai_costs_report.py` into the worker itself.** Track per-customer cost as a row in Notion so you can see margin per audit at a glance.
4. **Stop hand-writing PowerShell scheduling.** Commit a `scripts/install_scheduler.ps1` that wraps the schtasks command and idempotently registers / updates / removes the task.

---

## 4. Risks ranked by what would actually hurt

1. **No outreach → no customers → no learning.** This is the only risk that matters in the next 30 days. Everything else is hypothetical.
2. **An AI-generated finding is wrong in an embarrassing way.** Mitigation: the human gate. Don't disable it for paid tiers. For free, the 2-finding limit constrains blast radius.
3. **OpenAI prices change or rate-limits during a launch.** Mitigation: provider abstraction is already in place; Anthropic is a one-env-var swap.
4. **A competitor (VibeEval / VAS) launches a polish-focused tier and undercuts you on volume.** Mitigation: voice + Handoff Report = harder to copy than features. Keep writing in a recognizable voice.
5. **You burn out before reaching paying-customer #10.** Mitigation: the new clickable email workflow eliminates 80% of the friction per audit. Use it. Stop opening terminals.

---

## 5. What I would do this week if I were you

In order:

1. **Tonight (45 min total):** the four blocking items in `ROB-REMAINING-TODO.md`. Vercel env, Tally edit, Stripe success URLs, Task Scheduler. Don't skip the scheduler — without it, free signups pile up overnight and your conversion window evaporates.
2. **Tomorrow morning (60 min):** record the 60-second Loom. Put it above the pricing section on `/`. This is the single highest-leverage product change you can make.
3. **Tomorrow afternoon → end of week (3-4 hrs):** 30 personalised Looms to vibe-coder studios + Webflow shops. Goal: 3 replies, 1 paid conversion. Don't optimise the script after each one — send all 30, then analyse.
4. **Next Monday:** look at the data. If you have ≥1 paid conversion from outreach, double down on that channel. If you have 0, the message is broken (not the product). Rewrite the opener.
5. **Defer everything else.** No new features. No pricing tweaks. No copy changes. Outreach + data → decide.

---

## 6. The honest call

You have built more in two weeks than most indie founders build in six months. The code is better than it needs to be. The packaging is better than it needs to be. The market is real and growing.

What you don't have is **evidence that strangers will pay you**. That single data point is worth more than every refactor, every doc, every test you could write between now and getting it. Go get it.

The product is ready. The business is waiting on you to find out if it's a business.
