# LaunchLook — Go-live checklist

Use after `launchlook.app` is purchased. Repo may still live in a folder named `onceover/` locally until you rename it (close Cursor/terminals first).

## 1. DNS + Vercel

- [ ] `cd landing && vercel --prod`
- [ ] Vercel → Domains → add `launchlook.app` (+ `www` → redirect to apex)
- [ ] Registrar DNS records match Vercel
- [ ] Visit https://launchlook.app — landing loads

## 2. Email

- [ ] `hello@launchlook.app` (and optional `rob@launchlook.app`) receiving mail
- [ ] Resend: verify `launchlook.app` domain
- [ ] `.env`: `FROM_EMAIL`, `ADMIN_EMAIL`

## 3. Stripe

- [ ] Products renamed LaunchLook (Quick $7 / Launch $29 / Polish $59)
- [ ] Payment Link success URL: `https://launchlook.app/thanks`
- [ ] `landing/assets/config.local.js` — paste three Stripe URLs

## 4. Intake

- [ ] Tally form live; URL in `config.local.js` → `intakeFormUrl`
- [ ] Notion workspace **LaunchLook Ops** wired (BL-03)

## 5. Public checklist repo (BL-16)

- [ ] Publish `external/launchlook-prelaunch-checklist` as `github.com/YOU/launchlook-prelaunch-checklist`
- [ ] URL in `config.local.js` → `githubChecklist`

## 6. Smoke test

- [ ] Pricing buttons enabled (not greyed out)
- [ ] Test Stripe purchase → `/thanks` → intake link works
- [ ] Footer mailto: `hello@launchlook.app`

## Brand reference

| | Value |
|---|--------|
| Name | **LaunchLook** |
| Domain | **launchlook.app** |
| Config global | `window.LAUNCHLOOK_CONFIG` |
| HTML hooks | `data-launchlook-stripe`, `data-launchlook-email`, etc. |
