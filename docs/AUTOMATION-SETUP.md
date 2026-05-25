# AUTOMATION-SETUP

Tier 1 automation = two Vercel webhooks (Tally, Stripe) + two prep scripts
(screenshots, prescreener). All of it leans on env vars; this doc lists every
one and where to put it.

## Env vars at a glance

| Var | Used by | Set in `.env` | Set in Vercel |
|---|---|---|---|
| `NOTION_TOKEN` | webhooks + scripts | yes (already) | yes |
| `NOTION_CUSTOMERS_DB_ID` | webhooks + scripts | yes (already) | yes |
| `STRIPE_SECRET_KEY` | stripe webhook (optional, only if SDK needs API calls) | rename from `STRIPE_API_KEY` | yes |
| `STRIPE_WEBHOOK_SECRET` | stripe webhook | yes (new) | yes |
| `TALLY_WEBHOOK_TOKEN` | tally webhook | yes (new) | yes |
| `RESEND_API_KEY` | (PDF worker) | yes (already) | yes |

`.env` is gitignored. Vercel envs live in Project -> Settings -> Environment Variables.

> Note: the local `.env` currently uses `STRIPE_SECRET_KEY` already (good). If any older copy of `.env` still has `STRIPE_API_KEY`, rename it to `STRIPE_SECRET_KEY`. The stripe webhook falls back to `STRIPE_API_KEY` for safety, but new code should use the new name.

---

## 1. Resend

Already wired for the PDF worker. If you ever lose the key:

1. Go to <https://resend.com/api-keys>
2. Create API key -> `Full access`
3. Copy the value (starts `re_...`) into `.env` as `RESEND_API_KEY=...`
4. Push the same value to Vercel: `vercel env add RESEND_API_KEY production` (or paste via Dashboard)

---

## 2. Stripe webhook

1. Stripe Dashboard -> Developers -> Webhooks -> **Add endpoint**
2. Endpoint URL: `https://launchlook.app/api/stripe-webhook`
3. Events to send: select **`checkout.session.completed`** (and only that)
4. Click **Add endpoint**, then on the endpoint detail page click **Reveal** under "Signing secret". Copy the value (starts `whsec_...`).
5. Save it locally: append `STRIPE_WEBHOOK_SECRET=whsec_...` to `.env`
6. Save it on Vercel: Project -> Settings -> Environment Variables -> add `STRIPE_WEBHOOK_SECRET` for **Production**, **Preview**, and **Development**.
7. Test by clicking **Send test webhook** in Stripe's UI, then check the function logs in Vercel. A success looks like `{"status": "created" | "updated", ...}`. A signature failure returns 400.

### Local dry-run

```powershell
# In one terminal:
stripe listen --forward-to http://localhost:3000/api/stripe-webhook
# In another:
stripe trigger checkout.session.completed
```

`stripe listen` prints a `whsec_...` secret for the listener - export it as
`STRIPE_WEBHOOK_SECRET` for the local server only.

---

## 3. Tally webhook

Tally's free plan does not sign webhooks, so we use a shared secret in the URL.

1. Generate a random token. PowerShell:

   ```powershell
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. Save it twice:
   - `.env` -> `TALLY_WEBHOOK_TOKEN=<paste>`
   - Vercel -> `TALLY_WEBHOOK_TOKEN=<same value>`
3. In Tally, open the intake form `9qodVE` -> **Integrations** -> **Webhooks** -> Add webhook.
4. URL: `https://launchlook.app/api/tally-webhook?t=<TALLY_WEBHOOK_TOKEN>` (paste the literal token where shown)
5. Send the test event from Tally's UI. Success: `{"status": "created", "page_id": "..."}`. Bad token: 401.

If the token is ever leaked, rotate by generating a new one and updating both env entries plus the Tally webhook URL.

---

## 4. Local smoke tests

These do **not** need any webhook configured.

```powershell
# 1. Install deps once
pip install -r requirements-automation.txt
playwright install chromium

# 2. Screenshot smoke test against a public site (no Notion needed)
python scripts/capture_screenshots.py --url https://example.com
# -> output/customers/example-com/index.html

# 3. Prescreener smoke test
python scripts/prescreen_findings.py --url https://example.com
# -> output/customers/example-com/prescreen-findings.md

# 4. Real-customer run after the row is in Notion
python scripts/capture_screenshots.py --customer-id <first-8-of-page-id>
python scripts/prescreen_findings.py  --customer-id <first-8-of-page-id>
```

Both scripts accept a unique-prefix of the Notion page id - copy the URL from the row in Notion and grab the last segment.

---

## 5. Vercel env via CLI

If you have the Vercel CLI installed and linked to the project:

```powershell
# Pull current envs locally (sanity check)
vercel env pull .env.vercel.local

# Add a new secret to production
vercel env add STRIPE_WEBHOOK_SECRET production
# (paste value when prompted)

# Repeat for preview / development if you want webhook tests on preview deploys
vercel env add STRIPE_WEBHOOK_SECRET preview
vercel env add STRIPE_WEBHOOK_SECRET development
```

Otherwise paste via Dashboard -> Settings -> Environment Variables.

---

## 6. Verifying the deployed functions

After a deploy, in a browser:

- `https://launchlook.app/api/tally-webhook` -> 200 JSON `{"status":"ok", ...}` (GET sanity ping)
- `https://launchlook.app/api/stripe-webhook` -> 200 JSON `{"status":"ok", ...}`

Then POST a test event from Tally / Stripe and watch the function logs in the Vercel dashboard. If a 500 mentions `MissingEnvError`, the corresponding env var is unset on that environment.

---

## 7. Python version note

Vercel auto-detects Python 3.12 for files in `api/*.py`. No `runtime.txt` or `Pipfile` is needed. The `vercel.json` `functions` block only sets `maxDuration: 30` so the Notion round-trip never hits the default 10s ceiling.
