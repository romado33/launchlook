# Free 3-Finding Audit — Daily Workflow

The free 3-finding audit is the primary CTA on the landing page (see `PRODUCT-DECISIONS.md` §1, §7). This doc is Rob's daily playbook for processing the queue. It also documents the Notion schema, the dedup contract, and the abuse-watch checks.

Companion docs:

- `AI-AUDIT-PIPELINE.md` — pipeline internals, including the dedup section
- `PRODUCT-DECISIONS.md` — tier ladder + Free → Starter dedup rule (§2)
- `SIMPLICITY-GUARDRAILS.md` — customer-facing voice rules
- `ROB-REMAINING-TODO.md` — operational checklist (also references this file)

---

## §1 What the form does

`landing/index.html` and `landing/webflow.html` both have a free-audit form in the hero:

- Two fields: URL + email
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
6. Fires a one-line founder-voice confirmation email via Resend (best-effort; logs a warning if Resend is unavailable, customer still gets queued)

Per the SIMPLICITY-GUARDRAILS, the actual AI generation does NOT auto-run on every form submit. That stays manual to manage margin + abuse risk. The daily flow is in §3 below.

---

## §2 Notion free-audit DB schema

Create a new Notion DB and share it with the LaunchLook integration. Set the env var `NOTION_FREE_AUDIT_DB_ID` to its id (in Vercel and locally in `.env`).

| Property name | Type | Notes |
|---|---|---|
| `Request` | title | Auto-set by the handler to `email -- hostname`. Just for human scanning in Notion. |
| `Email` | email | Required; rate-limit key. |
| `URL` | url | Required; hostname dedup key. |
| `IP` | rich_text | Client IP from `x-forwarded-for`. Rate-limit key per day. |
| `Status` | select | One of `queued`, `processed`, `delivered`, `skipped`, `abuse`. |
| `Source` | select | `index`, `webflow`, or `api` (inferred from Referer). |
| `Platform` | select | `vibe-coder` or `webflow`. Drives the LLM's platform-conditional prompt. |
| `Finding Fingerprints` | rich_text | Semicolon-separated 16-hex fingerprints written back AFTER the offline pipeline approves the 3 findings. This is what `scripts/ai_audit/dedup.py` reads on the next paid Starter audit. |
| `Finding Summaries` | rich_text | Optional. Plain-English one-liner per finding, newline-separated. Surfaces in the LLM prompt as "Plain-English summary of the prior free findings" so the model sees more than just hashes. |

Schema lives in code at:

- `api/free-audit.py` — `_build_props()` writes the first six fields
- `scripts/ai_audit/free_audit_lookup.py` — reads `Finding Fingerprints` + `Finding Summaries`, writes them back via `persist_free_audit_fingerprints()`; `recent_delivery()` reads the most recent (email, hostname, created_time) tuple for the 30-day submission-time dedupe gate.

If you rename a column in Notion, update both modules in the same commit.

---

## §3 Daily flow (manual, for now)

### 30-day dedupe rule (customer-facing behavior)

Before Rob even sees the row, `api/free-audit.py` calls `free_audit_lookup.recent_delivery(url, email, days=30)`. A re-submission of the same URL + email inside 30 days of the last delivery returns the Starter upsell response instead of generating a second free audit; the customer receives an upsell email pointing at `https://launchlook.app/#pricing` (which carries the `data-launchlook-stripe="starter"` button so the Plausible `StarterCheckout` goal still fires). Same URL with a different email is treated as a different person and delivers normally. After 30 days the same email + URL pair counts as a fresh submission. The customer never sees the word "dedup" or "fingerprint" — only "I keep the findings consistent for 30 days so you can re-check after fixing" (no em-dashes, `SIMPLICITY-GUARDRAILS.md` §6). This is the cheapest defense against the free-tier harvest vector of repeat submissions fishing for more findings.

### Queue-processing steps

1. **Pull the queue.** In Notion, filter the free-audit DB by `Status = queued`, sorted ascending by created time. Aim to clear the queue within 24 hours of arrival.
2. **Skim for abuse.** Same IP, same hostname pattern, throwaway domain, or anything that looks like a competitor scraping us → set `Status = abuse` and skip. The 10-per-IP-per-day rate limit catches most of this automatically.
3. **Spin up a customer YAML** for the row. Use the audit UI's "new customer" flow or copy `customers/example-jane-sparkle.yaml` and fill in:
   - `email`, `app_url`, `tier: "Starter Package"` (we run the AI at Starter cap; deliver only the top 3 per §4)
   - `platform: webflow` if the row's Platform is webflow
4. **Run the pipeline:** `python scripts/ai_audit.py --free --customer <slug>`
   - The pipeline reads `email + url` from the YAML, runs the standard capture → prescreen → HTML → security-lite → LLM flow, and produces a draft YAML.
   - **No prior fingerprints** on a free audit (this IS the first audit), so the EXCLUDE_FINGERPRINTS block is empty.
5. **Review in the audit UI.** Drop false positives, sharpen wording, pick the **top 3 by severity** (per `PRODUCT-DECISIONS.md` §1). Keep the persona tags subtle (`SIMPLICITY-GUARDRAILS.md` §3.4).
6. **Deliver:** `python scripts/deliver_report.py --free --customer <slug>` — sends a short founder-voice email with just the 3 findings inline (no PDF for the free tier). Mark the Notion row `Status = delivered`.
7. **Persist fingerprints back to Notion.** Once delivered, write the 3 fingerprints into the row's `Finding Fingerprints` column. Either:
   - Manual: copy the hashes from the pipeline log + paste into Notion, OR
   - Programmatic (preferred): the deliver step calls `free_audit_lookup.persist_free_audit_fingerprints(row_id=..., fingerprints=..., summaries=...)`. (Hook the call wherever the free-tier deliver script lands; this is queued in `ROB-REMAINING-TODO.md` for the automation pass.)

If the customer later buys Starter for the same email + URL inside 90 days, the paid pipeline auto-looks-up those fingerprints and excludes them from the 10 new findings (see `AI-AUDIT-PIPELINE.md` Free → Starter dedup section).

---

## §4 What the customer receives

One short email, founder voice, single paragraph, signed `-- Rob`. No PDF, no portal, no logo, no upsell bombardment. Per `SIMPLICITY-GUARDRAILS.md` §5:

```text
Subject: Your 3 findings for <hostname>

Hi,

Took a walk through <site>. The three highest-impact things to fix before
you share publicly:

1. <plain-English headline> — <one-sentence "why it matters">
2. ...
3. ...

If you want the rest of the picture (up to 10 findings across every category, plus paste-ready fix prompts you can drop into your AI builder), Starter is $19: https://launchlook.app/#pricing

Your Starter findings build on these three, so you're not paying $19 to re-read the same things.

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
