# Free 2-Finding Audit — Daily Workflow

The free 2-finding audit is the primary CTA on the landing page (see `PRODUCT-DECISIONS.md` §1, §7). This doc is Rob's daily playbook for processing the queue. It also documents the Notion schema, the dedup contract, and the abuse-watch checks.

Companion docs:

- `AI-AUDIT-PIPELINE.md` — pipeline internals, including the dedup section
- `PRODUCT-DECISIONS.md` — tier ladder + Free → Starter dedup rule (§2)
- `SIMPLICITY-GUARDRAILS.md` — customer-facing voice rules
- `ROB-REMAINING-TODO.md` — operational checklist (also references this file)

---

## §1 What the form does

`landing/index.html` and `landing/webflow.html` both have a free-audit form in the hero:

- Two required fields: URL + email
- One optional field: **launch_concern** (max 500 chars) — founder's biggest launch concern. Stored in Notion Free Audit DB; injected into findings generation prompt as a soft ranking hint. Captured on the homepage form.
- Submit POSTs JSON to `/api/free-audit` (see `api/free-audit.py`)
- Plausible goal `FreeAuditSignup` fires on click
- The form's `free-audit.js` handler shows inline errors and redirects to `/thanks-free-audit` on success
- No-JS fallback: native POST routes through the same serverless function; it returns a 303 to the same thanks page

The serverless function:

1. Rate-limits: ≤ 3 free audits per email / 30 days, ≤ 10 per IP / day
2. Validates the URL (http/https only, no localhost, no private IP ranges)
3. Validates the email (basic regex)
4. **30-day dedupe gate** (`scripts/ai_audit/free_audit_lookup.recent_delivery`): same email + same hostname inside the 30-day window returns `{status: "duplicate"}` with an upsell message + payload, and the customer receives the Starter upsell email instead of a queue-confirmation. No second row is written.
5. Otherwise, writes a new row to the free-audit Notion DB with `Status = queued`
6. Fires emails via Resend (best-effort; API still returns `queued` if mail fails):
   - **Customer:** queue confirmation (BCCs `ADMIN_EMAIL` when set and different from the submitter)
   - **Founder:** dedicated ops email **to** `ADMIN_EMAIL` with URL, email, IP, source, and a Notion link
   - Requires `RESEND_API_KEY`, verified `FROM_EMAIL`, and **`ADMIN_EMAIL`** in Vercel (use an inbox you actually read, e.g. your Gmail if `@launchlook.app` is send-only)

Per the SIMPLICITY-GUARDRAILS, the actual AI generation does NOT auto-run on every form submit. That stays manual to manage margin + abuse risk. The daily flow is in §3 below.

---

## §2 Notion free-audit DB schema

Create a new Notion DB and share it with the LaunchLook integration. Set the env var `NOTION_FREE_AUDIT_DB_ID` to its id (in Vercel and locally in `.env`).

To verify or recreate the database automatically:

```bash
python scripts/ensure_free_audit_notion_db.py
python scripts/ensure_free_audit_notion_db.py --create-if-missing
```

If the configured ID is missing or the integration cannot see it, `/api/free-audit` returns HTTP 500 and nothing is saved.

| Property name | Type | Notes |
|---|---|---|
| `Request` | title | Auto-set by the handler to `email -- hostname`. Just for human scanning in Notion. |
| `Email` | email | Required; rate-limit key. |
| `URL` | url | Required; hostname dedup key. |
| `IP` | rich_text | Client IP from `x-forwarded-for`. Rate-limit key per day. |
| `Status` | select | One of `queued`, `processing`, `draft_ready`, `failed`, `delivered`, `skipped`, `abuse`, legacy `processed`. |
| `Source` | select | `index`, `webflow`, or `api` (inferred from Referer). |
| `Platform` | select | `vibe-coder` or `webflow`. Drives the LLM's platform-conditional prompt. |
| `Finding Fingerprints` | rich_text | Semicolon-separated 16-hex fingerprints written back AFTER the offline pipeline approves the 3 findings. This is what `scripts/ai_audit/dedup.py` reads on the next paid Starter audit. |
| `Finding Summaries` | rich_text | Optional. Plain-English one-liner per finding, newline-separated. Surfaces in the LLM prompt as "Plain-English summary of the prior free findings" so the model sees more than just hashes. |

Schema lives in code at:

- `api/free-audit.py` — `_build_props()` writes the first six fields
- `scripts/ai_audit/free_audit_lookup.py` — reads `Finding Fingerprints` + `Finding Summaries`, writes them back via `persist_free_audit_fingerprints()`; `recent_delivery()` reads the most recent (email, hostname, created_time) tuple for the 30-day submission-time dedupe gate.

If you rename a column in Notion, update both modules in the same commit.

---

## §3 Daily flow (automation + human gate)

See **`docs/AUTOMATION-PIPELINE.md`** for the full architecture (free + paid). Summary:

1. **Vercel** (`/api/free-audit`) writes Notion `Status = queued` and sends queue confirmation. It does **not** run Playwright or the LLM.
2. **Local worker** (cron or manual): `python scripts/process_audit_queue.py`
   - Discovers `queued` rows, sets `processing` → runs capture, prescreen, HTML, security-lite, perf, a11y, **form smoke**, LLM (Starter cap) → `draft_ready`
   - Emails **`ADMIN_EMAIL`** a review checklist (customer is **not** emailed)
3. **You review:** `python scripts/audit_ui.py --slug <slug> --review-ai` — drop false positives, pick the **top 2** (`FREE_AUDIT_DELIVER_COUNT`).
4. **Deliver manually:** founder-voice email with 2 findings inline (no PDF). Mark Notion `Status = delivered`.
5. **Persist fingerprints:** `free_audit_lookup.persist_free_audit_fingerprints(...)` after delivery (still manual hook; see `ROB-REMAINING-TODO.md`).

Paid jobs use the same worker after Tally + Stripe set `Status = Intake Received` and the intake checkbox. Worker never calls `deliver_report.py --send`.

### 30-day dedupe rule (customer-facing behavior)

Before Rob even sees the row, `api/free-audit.py` calls `free_audit_lookup.recent_delivery(url, email, days=30)`. A re-submission of the same URL + email inside 30 days of the last delivery returns the Starter upsell response instead of generating a second free audit; the customer receives an upsell email pointing at `https://launchlook.app/#pricing` (which carries the `data-launchlook-stripe="starter"` button so the Plausible `StarterCheckout` goal still fires). Same URL with a different email is treated as a different person and delivers normally. After 30 days the same email + URL pair counts as a fresh submission. The customer never sees the word "dedup" or "fingerprint" — only "I keep the findings consistent for 30 days so you can re-check after fixing" (no em-dashes, `SIMPLICITY-GUARDRAILS.md` §6). This is the cheapest defense against the free-tier harvest vector of repeat submissions fishing for more findings.

If the customer later buys Starter for the same email + URL inside 90 days, the paid pipeline auto-looks-up those fingerprints and excludes the prior **2** from the 10 new findings (see `AI-AUDIT-PIPELINE.md` Free → Starter dedup section).

---

## §4 What the customer receives

One short email, founder voice, single paragraph, signed `-- Rob`. No PDF, no portal, no logo, no upsell bombardment. Per `SIMPLICITY-GUARDRAILS.md` §5:

```text
Subject: Your 2 findings for <hostname>

Hi,

Took a walk through <site>. The two highest-impact things to fix before
you share publicly:

1. <plain-English headline> — <one-sentence "why it matters">
2. ...

If you want the rest of the picture (up to 10 findings across every category, plus paste-into-builder fix text you can drop into your AI builder), Starter is $19: https://launchlook.app/#pricing

Your Starter findings build on these two, so you're not paying $19 to re-read the same things.

-- Rob
hello@launchlook.app
```

No "AI-powered," no "comprehensive," no em-dashes (§6). Dedup is never mentioned by name to the customer.

For a re-submission inside 30 days (the dedupe gate in §3) the customer receives a short upsell email instead of the queue-confirmation: it names the prior submission date, points at Starter ($19), and gives the date the free check opens back up. Same founder voice, same no-em-dashes rule, signed `-- Rob`.

---

## §5 Abuse + budget watch

Daily quick checks:

- **Queue depth.** Filter `Status = queued`. If it's growing faster than you can clear it, raise the email rate limit's window from 30 days to 60 (one-line change in `api/free-audit.py` -- `since_email = now - timedelta(days=60)`).
- **Same-domain bursts.** Sort by `URL` and look for repeated hostnames from different emails. Set `Status = abuse` and consider adding a hostname-level rate-limit if it's chronic.
- **Resend bounces.** If the confirmation email bounces, the row stays `queued` regardless. Check the Resend dashboard for hard bounces before processing.
- **LLM cost.** The free pipeline burns one LLM run per audit. If volume gets noisy, batch-process every 2 to 3 days instead of daily. Eventually convert to a true async queue with a budget cap.

If you ship more than 5 free audits in a single day for two weeks straight, that's the trigger to invest in the auto-pipeline (queued in `ROB-REMAINING-TODO.md`).

---

## §6 Change log

| Date | Change |
|---|---|
| 2026-05-26 | q4 shipped: free-audit hero on `/` and `/webflow`, `/api/free-audit` serverless function with rate limits + Notion + Resend confirmation, `scripts/ai_audit/dedup.py` + `free_audit_lookup.py`, pipeline wiring, `/thanks-free-audit` page, token-gated `/checklist` (paid Scale Up + Pro deliverable). Cites SIMPLICITY-GUARDRAILS §2.1, §3.1, §5, §6 and PRODUCT-DECISIONS §1, §2, §7. |
| 2026-05-26 | 30-day fingerprint dedupe gate added: `free_audit_lookup.recent_delivery()` + branch in `api/free-audit.py`. Same URL + email inside 30 days returns the Starter upsell response (no second free audit, no second row, upsell email replaces the queue confirmation). Cites SIMPLICITY-GUARDRAILS §5, §6. |
