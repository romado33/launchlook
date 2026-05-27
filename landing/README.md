# Landing page (BL-05, BL-06)

Static site for **LaunchLook** at [launchlook.app](https://launchlook.app). No build step. Tailwind via Play CDN.

## Files

| File | Purpose |
|------|---------|
| `index.html` | Home — hero, what we check, sample, pricing, FAQ, footer (vibe-coder SKU: Lovable / Bolt / v0 / Cursor / Replit / Base44) |
| `webflow.html` | **LaunchLook for Webflow** — parallel SKU at `/webflow`. Webflow-specific hero, finding categories, FAQ, $19/$49/$99 pricing. Reuses the same Stripe Payment Links and the same Tally intake form (customer picks "Webflow" in Q7). See `docs/WEBFLOW-EXPANSION.md`. |
| `checklist.html` | Free pre-launch checklist (BL-06) |
| `privacy.html`, `terms.html`, `thanks.html` | Legal + post-checkout |
| `assets/config.js` | `LAUNCHLOOK_CONFIG` — Stripe links, `supportEmail`, `intakeFormUrl`, `linkedinUrl` |
| `assets/config.local.js` | Optional overrides (gitignored) |
| `assets/tailwind-brand.js` | Shared Tailwind theme (load before CDN) |
| `assets/apply-config.js` | Wires `data-launchlook-*` elements |
| `images/og.png` | Social preview — Option A minimal (1200×630) |
| `images/logo-icon.svg` | Header mark (accent check, matches OG) |
| `images/favicon.svg` | Tab icon (cream + check) |
| `vercel.json` | Clean URLs, security headers |

## Local preview

```bash
cd landing
python -m http.server 8000
# http://localhost:8000
```

## Deploy to Vercel

Production deploys from the **repo root** (`vercel.json` copies `landing/` → `dist/`). **Clean URLs and rewrites** must live in root `vercel.json` — Vercel does not apply routing from `dist/vercel.json` after the build.

```bash
# From repo root (recommended)
git push origin main   # Vercel auto-deploys

# Or CLI from landing/ (preview only; keep landing/vercel.json in sync with root)
cd landing
vercel --prod
```

## Custom domain (BL-01)

1. Vercel → Project → Settings → Domains
2. Add `launchlook.app` and `www.launchlook.app` (redirect www → apex)
3. Set DNS records at your registrar
4. SSL provisions automatically

## Site config

Edit `assets/config.js` (committed) or `config.local.js` (gitignored override):

- `intakeFormUrl` — after Tally publish; paste from [`docs/TALLY-COPY-PASTE.md`](../docs/TALLY-COPY-PASTE.md)
- `stripe.starter` / `stripe.scaleup` / `stripe.pro` — Payment Links ($19 / $49 / $99)
- `supportEmail` — `hello@launchlook.app`
- `linkedinUrl` — footer + Who's behind section

Stripe Payment Link **success URL** (dashboard): `https://launchlook.app/thanks`

**Rob's remaining setup:** [`docs/ROB-REMAINING-TODO.md`](../docs/ROB-REMAINING-TODO.md)

## Routes

| URL | File |
|-----|------|
| `/` | `index.html` (vibe-coder SKU) |
| `/webflow` | `webflow.html` (Webflow SKU — parallel landing page) |
| `/sample` | 301 → `/r/jane-sparkle-marketplace.html` (sample report — formerly `sample.html`, deleted May 2026) |
| `/checklist` | 301 → `/` (standalone checklist page deleted May 2026; the Pre-Launch Checklist is now a bundled PDF deliverable on every paid tier — see `templates/pre_launch_checklist.html.j2`) |
| `/privacy` | `privacy.html` |
| `/terms` | `terms.html` |
| `/thanks` | `thanks.html` (shared by both SKUs; copy is platform-agnostic) |
| `/r/{slug}` | `r/{slug}.html` (hosted shareable reports per customer; static fallback is `r.html`) |

## Before launch

1. Add `images/og.png` (1200×630) or remove `og:image` meta until ready.
2. Replace sample report placeholder with a real screenshot.

## Lighthouse (BL-05 acceptance)

Performance > 85 · Accessibility > 90 · Best Practices > 90 · SEO > 90

If the Tailwind CDN hurts Performance, build CSS locally (see `docs/03-build-queue.md`).
