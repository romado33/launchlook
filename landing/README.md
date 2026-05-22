# Landing page (BL-05, BL-06)

Static site for **LaunchLook** at [launchlook.app](https://launchlook.app). No build step. Tailwind via Play CDN.

## Files

| File | Purpose |
|------|---------|
| `index.html` | Home — hero, what we check, sample, pricing, FAQ, footer |
| `checklist.html` | Free pre-launch checklist (BL-06) |
| `privacy.html`, `terms.html`, `thanks.html` | Legal + post-checkout |
| `assets/config.js` | Default `LAUNCHLOOK_CONFIG` (domain, emails) |
| `assets/config.local.js` | Stripe / Tally / GitHub URLs (gitignored) |
| `assets/tailwind-brand.js` | Shared Tailwind theme (load before CDN) |
| `assets/apply-config.js` | Wires `data-launchlook-*` elements |
| `images/og.png` | Social preview image (1200×630) |
| `vercel.json` | Clean URLs, security headers |

## Local preview

```bash
cd landing
python -m http.server 8000
# http://localhost:8000
```

## Deploy to Vercel

```bash
npm install -g vercel
cd landing
vercel          # first time — project name: LaunchLook
vercel --prod   # production
```

## Custom domain (BL-01)

1. Vercel → Project → Settings → Domains
2. Add `launchlook.app` and `www.launchlook.app` (redirect www → apex)
3. Set DNS records at your registrar
4. SSL provisions automatically

## Site config

Copy `assets/config.local.js.example` → `assets/config.local.js`:

```javascript
window.LAUNCHLOOK_CONFIG = Object.assign(window.LAUNCHLOOK_CONFIG || {}, {
  stripe: { quickCheckup: "...", launchPack: "...", polish: "..." },
  intakeFormUrl: "https://tally.so/r/...",
  githubChecklist: "https://github.com/YOU/launchlook-prelaunch-checklist",
});
```

Stripe Payment Link **success URL**: `https://launchlook.app/thanks`

## Routes

| URL | File |
|-----|------|
| `/` | `index.html` |
| `/checklist` | `checklist.html` |
| `/privacy` | `privacy.html` |
| `/terms` | `terms.html` |
| `/thanks` | `thanks.html` |

## Before launch

1. Add `images/og.png` (1200×630) or remove `og:image` meta until ready.
2. Replace sample report placeholder with a real screenshot.

## Lighthouse (BL-05 acceptance)

Performance > 85 · Accessibility > 90 · Best Practices > 90 · SEO > 90

If the Tailwind CDN hurts Performance, build CSS locally (see `docs/03-build-queue.md`).
