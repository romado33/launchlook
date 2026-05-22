# LaunchLook — Go-live checklist

**Current pricing:** Starter Package **$9** · Launch **$29** · Follow-up re-scan quoted by email.

## 1. Site (Vercel)

- [x] Root `vercel.json` copies `landing/` → `dist/` (do **not** set Root Directory to `landing` unless you remove that build)
- [x] https://launchlook.app loads
- [ ] `images/og.png` present (social preview)
- [ ] Hard-refresh after each deploy

## 2. Stripe

- [ ] Two Payment Links only: **Starter Package $9**, **Launch $29**
- [ ] Success URL on both: `https://launchlook.app/thanks`
- [x] URLs in `landing/assets/config.js` (`stripe.starter`, `stripe.launch`)

## 3. Intake (required before cold outreach)

- [ ] Tally form built from `templates/intake-form-spec.md` (include security notice at top)
- [ ] Paste publish URL into `landing/assets/config.js` → `intakeFormUrl`
- [ ] Test: pay (or open `/thanks`) → intake button opens Tally
- [ ] Until Tally is live: `/thanks` falls back to pre-filled email to hello@launchlook.app

## 4. Email

- [ ] `hello@launchlook.app` receiving (ImprovMX, Google Workspace, or GoDaddy forward)
- [ ] Resend domain verified (for delivery/welcome emails)
- [ ] `.env`: `FROM_EMAIL`, `ADMIN_EMAIL`

## 5. Legal & trust

- [x] `privacy.html` / `terms.html` say LaunchLook (not Onceover)
- [x] Sample report at `/sample`
- [x] Founder + trust copy on homepage

## 6. Public checklist

- [x] https://github.com/romado33/launchlook-prelaunch-checklist
- [x] `githubChecklist` in `config.js`

## 7. Smoke test (do in incognito)

- [ ] Homepage hero + pricing (Starter Package / Launch)
- [ ] Stripe $9 test → lands on `/thanks`
- [ ] Stripe $29 test → lands on `/thanks`
- [ ] `/checklist`, `/sample`, `/privacy`, `/terms`
- [ ] Footer GitHub link works

## 8. Start selling

- [ ] 30 targeted DMs/Looms (see `templates/cold-outreach-loom-script.md`)
- [ ] Goal: **3 strangers pay $9** before more automation

## Brand reference

| | Value |
|---|--------|
| Name | **LaunchLook** |
| Domain | **launchlook.app** |
| Tiers | **Starter Package $9**, **Launch $29** |
| Config | `window.LAUNCHLOOK_CONFIG` |
