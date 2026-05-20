# Landing page (BL-05, BL-06)

Static single-page site. No build step. Tailwind via Play CDN. Two pages plus deployment config.

## Files

| File | Purpose |
|------|---------|
| `index.html` | Home page — hero, what we check, sample, pricing, FAQ, footer |
| `checklist.html` | The free pre-launch checklist (BL-06) |
| `vercel.json` | Vercel routing + security headers config |
| `images/` | OG card, logo, sample report screenshot (populate when ready) |

## Local preview

The simplest way:

```bash
cd landing
python -m http.server 8000
# open http://localhost:8000
```

Or use VS Code / Cursor's Live Preview / Live Server.

## Deploy to Vercel

First-time setup (one command):

```bash
npm install -g vercel
cd landing
vercel
```

When prompted:
- **Set up and deploy?** Y
- **Which scope?** your personal account
- **Link to existing project?** N
- **What's your project's name?** onceover
- **In which directory is your code located?** ./
- **Want to modify settings?** N

Subsequent deploys:

```bash
vercel --prod
```

## Custom domain

After the domain is bought and Vercel deploy works:

1. Vercel dashboard → Project → Settings → Domains
2. Add `onceover.app` (or whichever TLD Rob bought) and `www.onceover.app`
3. Follow the DNS records Vercel shows you. Set them at the registrar.
4. Wait 5–60 minutes for DNS propagation.
5. Vercel auto-provisions an SSL cert.

## Things that need updating before publishing

Search for `REPLACE_ME` across both HTML files:

1. **Stripe Payment Links** — three URLs in `index.html` pricing cards. Update after BL-02 (Stripe setup).
2. **GitHub repo link** — footer of both pages. Update after BL-16 (free checklist GitHub repo published).
3. **OG image** — `og:image` URL points at `/images/og.png` which doesn't exist yet. Create a 1200×630 OG card or remove the meta tag until ready.
4. **Sample report section** — currently has placeholder finding cards. Once a real audit is run, swap the screenshot in.

## TLD-dependent strings

If the domain is NOT `onceover.app`, update everywhere:

- `<meta property="og:url" content="https://onceover.app/" />` (both pages)
- `mailto:hello@onceover.app` (footer of both pages)
- `og:image` URL

PowerShell global-replace from repo root:

```powershell
Get-ChildItem -Recurse -Include *.html,*.md,*.txt | ForEach-Object {
  (Get-Content $_ -Raw) -replace 'onceover\.app', 'onceover.io' | Set-Content $_
}
```

## Lighthouse targets (from `docs/03-build-queue.md`)

- Performance > 85
- Accessibility > 90
- Best Practices > 90
- SEO > 90

If Performance dips below 85 with the Tailwind CDN, swap to a built CSS file:

```bash
npx tailwindcss -i ./styles.input.css -o ./styles.css --minify
```

And replace the `<script src="https://cdn.tailwindcss.com">` tag with `<link rel="stylesheet" href="/styles.css">`.

## Mobile target

Confirmed-tested viewports:

- 375px (iPhone SE) — no horizontal scroll
- 414px (iPhone 14 Pro Max)
- 768px (iPad)
- 1280px (laptop)
- 1920px (desktop)
