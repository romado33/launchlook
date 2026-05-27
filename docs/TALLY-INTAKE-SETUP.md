# LaunchLook — Build the Tally intake form (manual editor)

**Time:** ~30–45 minutes (new form) · ~10 minutes (hidden-tier upgrade on existing form)

## Copy file (plain text)

**Paste text only:** [`TALLY-PASTE-ONLY.txt`](TALLY-PASTE-ONLY.txt) (no instructions in file)

**Which block type each line is:** [`TALLY-INTAKE-PASTE.txt`](TALLY-INTAKE-PASTE.txt)

Thank-you page text is at the bottom of the same file (or use [`TALLY-THANK-YOU-PASTE.txt`](TALLY-THANK-YOU-PASTE.txt)).

Do **not** paste from `.md` files — Tally will show formatting junk.

---

## Before you open Tally

| Prerequisite | Value |
|--------------|--------|
| Intake form (edit in Tally) | `https://tally.so/r/QKOX1A` — already in `config.js` |
| After-submit redirect (set in Tally) | `https://launchlook.app/thanks` (static page) |
| Stripe success URLs | Tier-specific — see "Hidden-tier setup" below |
| Notification email | `hello@launchlook.app` |

---

## Hidden-tier setup (replaces Q8) — ~10 min

The old Q8 ("Which tier did you buy?") asked customers to re-select what they already paid for on Stripe. Replace it with a Tally hidden field populated from the Stripe success URL. Cleaner for customers, same data in Notion.

### 1 — Update Stripe Payment Link success URLs (run once)

Each main-tier link now redirects to a tier-specific URL:

| Tier | Success URL |
|------|-------------|
| Starter ($19) | `https://launchlook.app/thanks?tier=starter` |
| Scale Up ($49) | `https://launchlook.app/thanks?tier=scale_up` |
| Pro ($99) | `https://launchlook.app/thanks?tier=pro` |

```bash
python scripts/stripe_payment_links.py update-success-urls --dry-run
# looks correct? remove --dry-run to apply
python scripts/stripe_payment_links.py update-success-urls
```

Add-on links (Confidence Check, Handoff Report) keep the flat `/thanks` URL.

### 2 — Add a hidden `tier` field in Tally (QKOX1A)

1. Open `https://tally.so/r/QKOX1A` in edit mode.
2. Click **+** → **Hidden field**.
3. Set the field label to `tier` and the **URL parameter key** to `tier`.
4. Save. Tally will now receive `?tier=starter` (or `scale_up` / `pro`) from the Stripe redirect and populate this field automatically.

### 3 — Delete Q8 and update conditional logic

1. Delete **Q8** ("Which tier?").
2. For Q9, Q10, Q11, Q12 — change the conditional from:
   - "Show when Q8 = Scale Up Package ($49) OR Pro Package ($99)"
   - to: **"Show when [hidden tier] = scale_up OR pro"**

That's it. The webhook (`api/tally-webhook.py`) already maps `scale_up` → `Scale Up Package` and `pro` → `Pro Package` in `TIER_MAP`.

### Fallback / backward compatibility

Old responses that still have Q8 data continue to work — the TIER_MAP keeps all legacy Q8 display-text keys. You can delete Q8 from the form without redeploying any code.

---

## Full form checklist (new form)

- [ ] New form → **Start from scratch**
- [ ] Form title: `LaunchLook — Post-purchase intake`
- [ ] Block 0: **Text** (security notice) — paste from file
- [ ] Questions 1–7, then 9–15 (Q8 removed — use hidden tier field instead)
- [ ] **Q7 (Which platform built it?) — add `Webflow`** between `v0` and `Other`
- [ ] **Hidden field** with URL-param key `tier` (see step 2 above)
- [ ] Logic on Q9, Q10, Q11, Q12: show when hidden `tier` = `scale_up` OR `pro`
- [ ] Q15 checkbox required, above Submit
- [ ] Thank you page — paste from file
- [ ] **After submit** → redirect to `https://launchlook.app/thanks`
- [ ] Notifications → `hello@launchlook.app`, all answers
- [ ] Test Starter path (Q9–12 hidden) and Scale Up/Pro path (Q9–12 visible)
- [x] `intakeFormUrl` in `config.js` → `QKOX1A` (already deployed)

### Webflow option for Q7 (5-min add)

LaunchLook for Webflow (the `/webflow` SKU at `launchlook.app/webflow`) reuses this same intake form. Webflow customers will land here from the Webflow landing page, so Q7's dropdown needs to include `Webflow` so they can self-identify.

Updated Q7 option list (in order):

```
Lovable
Bolt
Base44
Replit
v0
Webflow
Other
```

Open Tally → Q7 → **Edit options** → add `Webflow` between `v0` and `Other`. No conditional logic needs to change (Q9–Q12 trigger off hidden `tier`, not Q7 platform).

When the Tally webhook fires into the AI pipeline, the platform value `Webflow` should be passed through to `scripts/ai_audit.py --platform webflow --builder Webflow`. See `docs/WEBFLOW-EXPANSION.md` for the full handoff.

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Q9–12 never appear | Confirm hidden field URL-param key is exactly `tier`; check Stripe links use `?tier=scale_up` / `?tier=pro` |
| Tier blank in Notion | Run `update-success-urls`; or check `tallyPrefill.tier = "tier"` in `config.js` |
| Thanks page on site is mailto | Set `intakeFormUrl` in config and deploy |

---

Site already points at **QKOX1A**. Only update `config.js` if you publish a new Tally URL.

### Optional: pre-fill App URL from `/thanks`

After a free audit, `/thanks` and `/thanks-free-audit` pass the customer's email (and App URL when configured) into the Tally link.

1. In Tally, add a **hidden field** for the app URL (note the URL-param key).
2. Set `tallyPrefill.appUrl` in `landing/assets/config.js` to that key (e.g. `"app_url"`).
3. Email prefill uses `?email=` automatically on the standard email question.
