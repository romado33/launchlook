# LaunchLook — Success Metrics

*Last updated: May 2026. Solo-founder service, pre-revenue, early-adopter phase.*

---

## §0 Problem Validation — the Lorelight test

> *"The problem didn't need solving."*
> — Lorelight post-mortem, Oct 2025 (see `docs/PRODUCT-DECISIONS.md` §2)

This is the test that must pass before any of the other metrics below mean anything. Revenue, conversion rates, and refund rates are lag indicators. By the time they signal "problem didn't need solving," you've already spent months building.

The early signal is simpler: **do free users act on the findings before any money changes hands?**

### What "acted on" looks like

A free-tier user has acted if any of the following happen within 7 days of delivery:

| Observable signal | How to track |
|---|---|
| Replies to the free findings email with a question, confirmation, or "I fixed this" | Read your inbox; log in `logs/email_sends.jsonl` |
| Submits the upgrade form (even if they don't pay yet) | Stripe / Tally intake |
| Forwards the email to a co-founder or developer | "A colleague mentioned" in a reply |
| Mentions the finding in social/Indie Hackers/Discord | Google Alert on "LaunchLook" |

You do NOT need analytics for this. At low volume, read every reply.

### The failure threshold

After **20 free deliveries**:

- If **fewer than 3** (15%) have any observable action signal → the problem is not painful enough, or the findings are not credible enough. Do not invest further in paid acquisition. Run a user interview with at least 5 free-audit recipients and ask directly: "Did you check the finding? Why or why not?"
- If **3–6** (15–30%) have action signal → the problem is real but findings quality or framing may be weak. Review the 5 most-delivered free findings for specificity and actionability.
- If **6+** (30%+) have action signal → validated. The problem is real and painful. Scale the acquisition.

### The deduplication corollary

`PRODUCT-DECISIONS.md` §2 states: *"You're not paying $19 to re-read your free preview."* The free hook must deliver two findings that are **immediately actionable** — not vague observations. If a free user opens the email and the finding says "your mobile experience could be improved," they won't act on it and they won't upgrade. If it says "your signup button is hidden off-screen on a 375px iPhone — here is the exact paste-into-builder text to fix it," they'll paste it in before closing the email.

Review the quality of every free delivery manually for the first 30 free audits. The free findings are the product validation instrument, not just a marketing hook.

### The false-positive trap

A high free → paid conversion rate (Section 2) does **not** automatically prove the problem is real. Founders buy out of anxiety, FOMO, and the sunk-cost of having already submitted the form. A finding they never read but paid $19 to "have" is a refund waiting to happen, not problem validation. Watch for:

- Refund requests that arrive without any engagement (no prior reply, no Fix Check)
- Customers who can't describe what they fixed when you ask in a follow-up email

Both are signs the purchase was anxiety-driven, not problem-driven.

---

## How to read this document

Metrics are split into three horizons:

- **Month 1–3 (Validation)** — prove the concept pays for itself
- **Month 4–12 (Traction)** — build a repeatable revenue engine
- **Year 2+ (Sustainability)** — reach founder-income level

Each metric has a **floor** (something is broken if you're below this), a **target** (healthy, sustainable business), and a **stretch** (doing well). These numbers are calibrated for a solo founder with no paid acquisition budget.

---

## 1. Revenue

### Monthly Recurring-ish Revenue (MRRR)
LaunchLook is transactional, not subscription. Use a rolling 30-day revenue figure instead of MRR.

| Horizon | Floor | Target | Stretch |
|---|---|---|---|
| Month 1–3 | $0 (still fine) | $200 | $500 |
| Month 4–12 | $200/mo | $800/mo | $2,000/mo |
| Year 2+ | $800/mo | $2,500/mo | $5,000/mo |

**$2,500/month = ~$30,000/year** — meaningful solo-founder income from a side project without employees or paid ads.

### Revenue per audit (blended average)
Mix of free conversions, Starters, Scale Ups, Pros, and Handoff add-ons.

| Target blend | Implied avg. order |
|---|---|
| 60% Starter ($19), 25% Scale Up ($49), 10% Pro ($99), 5% Handoff add-on ($49) | ~$33–35 per paying audit |

To hit $800/month at a $34 average, you need ~24 paid audits/month (~6/week).

---

## 2. Funnel Conversion

### Free trial → paid upgrade

The single most important ratio in the business. A free trial is only valuable if it converts.

| Horizon | Floor | Target | Stretch |
|---|---|---|---|
| Month 1–3 | 5% | 15% | 25% |
| Month 4–12 | 10% | 20% | 30% |

**Context:** SaaS free-to-paid is typically 2–5%. A human-reviewed service with a clear upgrade path and a 2-finding hook should land higher. 15–20% is achievable if the free findings are genuinely useful and the upgrade path is frictionless. If you're below 10% consistently, the free findings aren't landing — review the quality, framing, and email copy.

### Landing page → free trial submit

| Floor | Target | Stretch |
|---|---|---|
| 2% | 5% | 10% |

**Context:** Landing-page conversion for a one-step free form is typically 3–8% for targeted traffic. Under 2% means the hero or offer isn't landing. Over 8% means you're doing something unusually right.

### Email open rate (founder notification emails)

| Floor | Target |
|---|---|
| 25% | 45% |

Plain-text transactional emails from a named person to a named founder should open well. Below 25% usually means deliverability issues or the subject line is too generic.

---

## 3. Quality Signal

### Refund rate

| Floor (bad) | Target | Stretch |
|---|---|---|
| < 10% refunds | < 5% | < 2% |

7-day refund policy. A refund means the report wasn't useful. Track *why* — if refunds cluster on a specific tier or builder type, that's a product signal.

### Fix Check repeat-purchase rate

Customers who come back for a re-scan after applying fixes. This is the loyalty signal.

| Horizon | Floor | Target |
|---|---|---|
| Month 4–12 | 5% of paid customers | 15% |
| Year 2+ | 10% | 25% |

A 15% Fix Check rate means 1 in 7 paid customers comes back. At $19 ($9 early-window), this adds meaningful revenue and validates that the first report was actionable.

### Customer satisfaction (informal)

No formal NPS in v1. Proxy signals:
- Unprompted positive reply to delivery email (track in `logs/email_sends.jsonl`)
- Wall of Launches opt-ins
- Referral mentions ("a friend sent me")

Target: at least 1 positive reply per 10 deliveries.

---

## 4. Operations / Capacity

### Audit turnaround time

| Floor (must fix) | Target | Stretch |
|---|---|---|
| < 7 days | < 3 days | < 24 hrs (paid tiers) |

Turnaround is a trust signal. A founder who submits Friday wants the report before Monday's pitch. If you're regularly hitting 5+ days, that's a conversion-killer for future referrals.

### Rob's time per paid audit

This is your effective hourly rate denominator.

| Task | Est. time |
|---|---|
| Automated pipeline run | 5–10 min (unattended) |
| Human review / finding triage | 20–35 min |
| Report delivery + email send | 5 min |
| **Total per paid audit** | **30–50 min** |

At $34 blended revenue and 40 min/audit, you're billing ~$51/hour of active time. At Scale Up ($49, 35 min), ~$84/hour. Protect this — scope creep and back-and-forth emails are margin killers.

### Max sustainable audit volume (solo)

At 40 min/audit and a 10-hour week budget: ~15 paid audits/week, ~60/month.

**Capacity ceiling before hiring/tooling change: ~60 paid audits/month = ~$2,000/month.**

If you hit the ceiling before hitting $2,000/month, the blended price is too low. Raise prices before hiring.

---

## 5. Growth

### Organic traffic (landing page)

| Horizon | Floor | Target |
|---|---|---|
| Month 1–3 | < 100 visits/mo (still fine, pre-SEO) | 300/mo |
| Month 4–12 | 300/mo | 1,000/mo |
| Year 2+ | 1,000/mo | 5,000/mo |

Primary organic levers: /webflow, comparison pages (/vs-pagelens), and the Wall of Launches as link surface. (Note: /built-with-ai was retired May 2026; its content was merged into the main landing page.)

### Referral-sourced audits

Target by Month 6: at least 20% of new paid audits trace back to a referral or word-of-mouth. If referral rate is under 10% after 50 paid deliveries, the reports aren't "shareable" enough — review framing and the referral note in the delivery email.

### Wall of Launches entries

| Month 3 | Month 6 | Month 12 |
|---|---|---|
| 3 entries | 10 entries | 25 entries |

The wall works as social proof once it has ~5 entries. Reaching out to every delivered customer with "can I add you?" is the manual step.

---

## 6. Failure modes to watch for

| Signal | What it means | What to do |
|---|---|---|
| < 3 free users act on findings in first 20 deliveries | **Problem may not be painful enough** (Lorelight failure) | Run 5 user interviews before investing further; review finding specificity |
| Free trial submit rate < 2% for 30 days | Hero/offer not landing | A/B test the H1 and form CTA copy |
| Free → paid conversion < 8% for 30 days | Free findings aren't useful enough or upgrade friction | Review finding quality; check email copy |
| Refund rate > 10% | Reports not meeting expectations | Review at least 5 refunded reports for patterns |
| Zero Fix Checks after 50 deliveries | Findings aren't actionable | Add a "what to do next" section in delivery email; simplify fix prompts |
| Turnaround > 7 days consistently | Queue not draining | Check automation pipeline; reduce tier complexity |
| No positive unprompted replies after 20 deliveries | Reports are correct but not delightful | Review delivery email tone; add personal one-liner per report |

---

## 7. When to declare it working

**Minimum viable success (Month 6):**
- At least 30% of first 20 free recipients showed an observable action signal (§0 Lorelight test)
- At least 30 paid audits delivered
- Blended revenue above $800/month for two consecutive months
- Refund rate under 8%
- At least one Fix Check repeat purchase
- At least one unprompted referral

**If all six are true by Month 6, the model is validated. Start raising prices and investing in SEO.**

**If the first criterion fails, stop all other investment and run user interviews first.** No amount of landing page optimisation fixes a problem that isn't painful enough.

---

## 8. Comparable benchmarks (solo service businesses)

| Business type | Free → paid conv. | Revenue at 12 months | Refund rate |
|---|---|---|---|
| Solo SaaS (typical) | 2–5% | $500–$2k MRR | < 5% |
| Done-for-you productised service | 10–25% | $2k–$10k/mo | < 3% |
| Automated audit tool ($19–$99) | 8–15% | $1k–$5k/mo | < 5% |

LaunchLook is closest to the **productised service** row. Human review is the premium that justifies higher conversion and lower refund rate than pure SaaS.

---

*See also: `docs/BUSINESS-REVIEW-2026-05-27.md`, `docs/LESSONS-LEARNED.md`*
