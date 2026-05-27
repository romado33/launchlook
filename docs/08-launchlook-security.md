# LaunchLook — Security posture (launchlook.app)

**Last reviewed:** May 2026

LaunchLook is a **static marketing site** plus **local Python scripts** (Notion, Resend, Stripe). There is no customer login, no API on the public site, and no database on Vercel.

This doc is what we checked for **our own app**. It is not a substitute for VAS/VibeEval on customer apps.

---

## Public site (Vercel)

| Control | Status |
|--------|--------|
| HTTPS only | Vercel + HSTS |
| Security headers | `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`, `COOP`, **CSP** (root `vercel.json`) |
| Secrets in Git | `.env`, `config.local.js` gitignored; build strips them from `dist/` |
| Secret URLs blocked | `/assets/config.local.js`, `/.env` → 404 |
| Public config | `config.js` only has **public** Stripe Payment Link URLs (not secret keys) |
| XSS surface | No `innerHTML` / `eval`; `apply-config.js` only allows `https:` Stripe/GitHub/Tally URLs |
| External links | `rel="noopener noreferrer"` on third-party tool links |
| Post-pay intake | Mailto fallback; no credentials collected on-site |

### Accepted tradeoffs (MVP)

- **Tailwind Play CDN** (`cdn.tailwindcss.com`) — convenience vs. supply-chain risk; no SRI on the dynamic CDN build. Mitigation: CSP limits script origin to that host only.
- **Google Fonts** — third-party stylesheet; limited to `fonts.googleapis.com` / `fonts.gstatic.com` in CSP.
- **No pentest** — polish/UX checkup product; terms say not a security audit.

---

## Operator tooling (local / GitHub Actions)

| Control | Status |
|--------|--------|
| API keys | `.env` only; documented in `.env.example` with empty values |
| Stripe secret | Used only in `scripts/referral_create.py`, never in `landing/` |
| CI secrets | GitHub Actions `secrets.*` for follow-up job only |
| Pre-commit | Avoid committing `sk_live`, `secret_`, `whsec_` patterns (manual review) |

Run dependency checks when you change Python deps:

```bash
pip install pip-audit
pip-audit -r <(python -c "import tomllib; ...")  # or audit your venv after pip install -e .
```

---

## What LaunchLook does **not** guarantee

- RLS / API / auth bugs in **customer** apps (Ship Package does a basic cross-user **visibility** check only).
- OWASP Top 10 coverage, CVE scanning, or compliance (SOC2, HIPAA).
- Security of Stripe, Tally, Notion, or Resend (use their dashboards and MFA).

For deep scans on **your** vibe-coded app, use [VAS](https://vibeappscanner.com) or similar in addition to LaunchLook.

---

## After deploy — quick verify

1. https://launchlook.app/assets/config.local.js → **404**
2. Browser devtools → no CSP errors on homepage, `/thanks`, `/checklist`
3. Stripe buttons still open `buy.stripe.com` links
4. [securityheaders.com](https://securityheaders.com/?q=https://launchlook.app) — expect improved grade after CSP deploy
