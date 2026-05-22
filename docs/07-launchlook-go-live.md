# LaunchLook — Go-live checklist

**Current pricing:** Starter Package **$9** · Full Package **$29** · Follow-up re-scan quoted by email.

**Rob's master todo:** [`ROB-REMAINING-TODO.md`](ROB-REMAINING-TODO.md) · **Tally paste file:** [`TALLY-COPY-PASTE.md`](TALLY-COPY-PASTE.md)

## 1. Site (Vercel)

- [x] Root `vercel.json` copies `landing/` → `dist/` and owns **cleanUrls + rewrites** (do **not** set Root Directory to `landing`)
- [x] https://launchlook.app loads
- [x] `images/og.png` present (social preview — verify in Slack after deploy)
- [ ] Hard-refresh after each deploy

## 2. Stripe

- [x] Two Payment Links: **Starter Package $9**, **Full Package $29** — both tested OK
- [x] Success URL → `https://launchlook.app/thanks` (verified)
- [x] Checkout URLs in `landing/assets/config.js` (`stripe.starter`, `stripe.launch`)

## 3. Intake (required before cold outreach)

- [x] `intakeFormUrl` in `config.js` → `https://tally.so/r/9qodVE` (deployed)
- [x] `tallyThanksUrl` in `config.js` → `https://tally.so/r/Y5xO5J` (set as **redirect after submit** on form 9qodVE in Tally)
- [ ] Tally form **9qodVE** — paste fields from [`TALLY-PASTE-ONLY.txt`](TALLY-PASTE-ONLY.txt) (guide: [`TALLY-INTAKE-SETUP.md`](TALLY-INTAKE-SETUP.md))
- [ ] Notifications → `hello@launchlook.app` · test Starter + Full paths
- [ ] Test: pay (or open `/thanks`) → intake button opens Tally (not mailto-only)
- [x] `/thanks` mailto fallback if `intakeFormUrl` is ever empty

## 4. Email

- [ ] `hello@launchlook.app` receiving (ImprovMX, Google Workspace, or GoDaddy forward)
- [ ] Resend domain verified (for delivery/welcome emails)
- [ ] `.env`: `FROM_EMAIL`, `ADMIN_EMAIL`

## 5. Legal & trust

- [x] `privacy.html` / `terms.html` say LaunchLook (not Onceover)
- [x] Sample report at `/sample` (includes example copy-paste fix prompt)
- [x] Founder + trust copy on homepage (LinkedIn when `linkedinUrl` set in `config.js`)
- [x] Simplified free checklist at `/checklist`

## 6. Public checklist

- [x] https://github.com/romado33/launchlook-prelaunch-checklist
- [x] `githubChecklist` in `config.js`

## 7. Security (launchlook.app)

- [x] Headers + CSP in root `vercel.json` (see `docs/08-launchlook-security.md`)
- [ ] After deploy: `/assets/config.local.js` returns 404; homepage has no CSP console errors

## 8. Payment + intake E2E (do in incognito — blocks first paying customer)

Run **both** tiers on desktop and once on your phone:

- [x] Click **Get Starter Package — $9** → Stripe checkout opens
- [x] Pay → redirects to `https://launchlook.app/thanks` (Starter + Full tested)
- [ ] Intake opens (Tally) or mailto fallback works
- [ ] Intake asks only safe info; Full Package shows test-account fields only when selected
- [ ] You receive the submission (Tally email → hello@launchlook.app)
- [ ] Customer gets confirmation (welcome email when Resend is wired)
- [x] Repeat for **Get Full Package — $29**
- [ ] `/checklist`, `/sample`, `/privacy`, `/terms` all load
- [ ] Footer GitHub link works

## 9. Start shmoozing (do this next)

- [x] Tally `intakeFormUrl` in `landing/assets/config.js` (site wired — finish Tally dashboard + §8 E2E first)
- [ ] Section 8 complete on phone
- [ ] 30 targeted DMs/Looms (`templates/cold-outreach-loom-script.md`)
- [ ] Goal: **3 strangers pay $9** — stop polishing code after that

## 10. Consistency quick check

- [ ] Site says **Starter Package** / **Full Package** everywhere customer-facing
- [ ] Stripe dashboard product names can differ; Payment Link success URLs must match `/thanks`
- [ ] Internal code may still use `stripe.launch` — that's fine

## Brand reference

| | Value |
|---|--------|
| Name | **LaunchLook** |
| Domain | **launchlook.app** |
| Tiers | **Starter Package $9**, **Full Package $29** |
| Config | `window.LAUNCHLOOK_CONFIG` |
