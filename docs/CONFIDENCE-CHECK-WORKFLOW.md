# Confidence Check / Saboteur re-scan workflow

The Confidence Check (also marketed as "Send in The Saboteur") is a one-off
paid add-on available to any paying LaunchLook customer. It re-runs the audit
against the same URL the customer already paid to have reviewed, then ships a
short focused report covering:

1. What's now fixed
2. What's still showing up
3. New things that turned up that the fixes might have introduced

Companion docs:
- `SIMPLICITY-GUARDRAILS.md` (especially §2.6 add-ons below main pricing, §3.4 Saboteur voice)
- `PRODUCT-DECISIONS.md` §1 add-ons table
- `TESTERS-CAST.md` §6 The Saboteur

---

## §1 What it is and pricing

| Field | Value |
|---|---|
| Product name | Confidence Check (CTA copy: "Send in The Saboteur") |
| Standalone | **$19** |
| Within 14 days of last audit | **$9** (encourages quick iteration loop) |
| Available to | Any paying customer (Starter, Scale Up, Pro) |
| Free with | 1× included with every Pro purchase |
| Deliverable | Short-form PDF (2 to 4 pages) emailed within 24 hours of URL submission |

The persona voice is The Saboteur (per `TESTERS-CAST.md` §6): mischievous,
"chaos monkey trying to break things." Conversational, plain English. NOT
QA-report or pen-test style.

---

## §2 Stripe Payment Links Rob needs to create

Both links are created manually in Stripe Dashboard → Payment Links.

### $19 standalone link

- Price: **$19.00 USD** (one-time)
- Description: "LaunchLook Confidence Check (Saboteur re-scan)"
- **Metadata** (this is the discriminator the webhook uses): key `product`, value `confidence_check`
- Success URL: `https://launchlook.app/thanks`
- After Rob creates it: paste the URL into the Vercel env var
  `STRIPE_PAYMENT_LINK_SABOTEUR` and into `landing/assets/config.js`
  under `stripe.saboteur` (or set via `config.local.js`)

### $9 within-14-days link

- Price: **$9.00 USD** (one-time)
- Description: "LaunchLook Confidence Check ($9 within 14 days)"
- **Metadata**: key `product`, value `confidence_check`
- Success URL: `https://launchlook.app/thanks`
- After Rob creates it: paste the URL into the Vercel env var
  `STRIPE_PAYMENT_LINK_SABOTEUR_DISCOUNTED` and into `config.js` under
  `stripe.saboteurDiscounted`

The $9 link is **not** exposed on the landing page. Rob sends it manually in
the post-delivery email when a customer asks for a re-check inside the
14-day window. Automating that send is q-future-automation.

---

## §3 Notion DB Rob needs to create

Create a database called **Confidence Checks** in the LaunchLook Ops
workspace and share it with the existing Notion integration. Schema:

| Property | Type | Notes |
|---|---|---|
| `customer_email` | Email | The Stripe customer email |
| `original_audit_id` | Text | Slug of the original audit (best-effort, blank if unknown) |
| `paid_at` | Date | Set automatically by the webhook |
| `price_paid` | Text | "Confidence Check ($19)" or "Confidence Check ($9)" |
| `status` | Select | Options: `queued`, `delivered` |

After creation, paste the DB ID into Vercel env vars and into local `.env`:

```
NOTION_CONFIDENCE_CHECK_DB_ID=<paste from Notion URL>
```

If this env var is unset, the webhook logs a warning and silently skips the
Notion write (the customer still gets the confirmation email).

---

## §4 Daily flow for Rob

1. **Watch for new payments.** The webhook (api/stripe-webhook.py) writes a
   row to the Confidence Checks Notion DB with `status = queued` and emails
   the customer asking for the URL via the intake form.
2. **When the URL arrives:** open Notion → Confidence Checks DB → filter
   `status = queued`. For each row, run:
   ```
   python scripts/confidence_check.py --customer <slug> --original <original_audit_id>
   ```
   The slug typically matches the original audit slug. The script:
   - Re-walks the URL (stub mode for now; real Playwright + LLM is wired
     behind `--provider anthropic|openai` and lazy-imports the existing
     pipeline).
   - Buckets findings into fixed / still_present / new.
   - Picks one of the four standardized verdict labels (same vocabulary as
     the main audit).
   - Writes `data/confidence_checks/<slug>-<timestamp>.yaml`.
3. **Manual review in audit_ui** (which already exists): open the YAML in
   the UI, tighten The Saboteur's wording, drop false positives.
4. **Deliver:**
   ```
   python scripts/deliver_report.py --confidence-check --customer <slug>
   ```
   Dry-run by default. The script renders the short-form PDF and a preview
   of the email body. Once happy:
   ```
   python scripts/deliver_report.py --confidence-check --customer <slug> --send
   ```
5. **Mark `status = delivered`** in the Notion row.
6. **If the customer is still inside their 14-day window after delivery and
   asks for another:** send them the $9 Stripe Payment Link manually via the
   delivery email reply. (The `$9` link automation is deferred per
   `PRODUCT-DECISIONS.md` §4.)

The Confidence Check intentionally has no QSG. It's a short focused report,
not a full audit.

---

## §5 Voice rules

The report copy is The Saboteur's voice. Examples that pass review:

> I poked at the homepage CTA again — looks fixed. Good.

> I tried the same broken flow you had before. Still broken. The fix didn't take.

> I clicked through the new checkout flow you added. It works, but I noticed
> the success page has a typo in the heading.

NOT cold/clinical. NOT QA-report style. Per `SIMPLICITY-GUARDRAILS.md` §3.4
and §3.8 (founder-voice, plain English).

Banned vocabulary on customer-facing surfaces (per `SIMPLICITY-GUARDRAILS.md`
§6): `regression test`, `unit test`, `chaos monkey`, `pen-test`. Use the
plain-English phrasing the customer uses ("re-scan," "re-walk," "send in The
Saboteur").

---

## §6 Files of interest

- `scripts/confidence_check.py` — pipeline entry point
- `scripts/deliver_report.py` — `--confidence-check` flag for delivery
- `templates/confidence_check/report.html.j2` — short-form PDF template
- `templates/email/confidence_check_email.{txt,html}.j2` — delivery email
- `api/stripe-webhook.py` — `handle_confidence_check_purchase`
- `data/confidence_checks/` — generated YAMLs (gitignored)
- `output/confidence_checks/<customer>/confidence-check.pdf` — rendered PDFs
