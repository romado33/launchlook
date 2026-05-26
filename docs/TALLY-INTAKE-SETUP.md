# LaunchLook — Build the Tally intake form (manual editor)

**Time:** ~30–45 minutes

## Copy file (plain text)

**Paste text only:** [`TALLY-PASTE-ONLY.txt`](TALLY-PASTE-ONLY.txt) (no instructions in file)

**Which block type each line is:** [`TALLY-INTAKE-PASTE.txt`](TALLY-INTAKE-PASTE.txt)

Thank-you page text is at the bottom of the same file (or use [`TALLY-THANK-YOU-PASTE.txt`](TALLY-THANK-YOU-PASTE.txt)).

Do **not** paste from `.md` files — Tally will show formatting junk.

---

## Before you open Tally

| Prerequisite | Value |
|--------------|--------|
| Intake form (edit in Tally) | `https://tally.so/r/9qodVE` — already in `config.js` |
| After-submit redirect (set in Tally) | `https://tally.so/r/Y5xO5J` |
| Stripe success URL (dashboard) | `https://launchlook.app/thanks` |
| Notification email | `hello@launchlook.app` |

---

## Checklist

- [ ] New form → **Start from scratch**
- [ ] Form title: `LaunchLook — Post-purchase intake`
- [ ] Block 0: **Text** (security notice) — paste from file
- [ ] Questions 1–15 in order — paste titles, descriptions, placeholders, options
- [ ] Q7, Q8, Q9: use **Bulk insert options** for option lists
- [ ] **Q7 (Which platform built it?) — add `Webflow` to the option list** (between `v0` and `Other`). This is what routes Webflow customers through to the right fix-prompt voice. See "Webflow option for Q7" below.
- [ ] Logic on Q9, Q10, Q11, Q12 (see bottom of paste file)
- [ ] Q15 checkbox required, above Submit
- [ ] Thank you page — paste from file
- [ ] **After submit** → redirect to `https://tally.so/r/Y5xO5J` (thanks form; URL also in `config.js` as `tallyThanksUrl`)
- [ ] Notifications → `hello@launchlook.app`, all answers
- [ ] Test Starter path (Q9–12 hidden) and Full path (Q9–12 visible)
- [x] `intakeFormUrl` in `config.js` → `9qodVE` (already deployed — skip unless you publish a new form)

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

Open the form in Tally → click Q7 (`Which platform built it?`) → **Edit options** → add `Webflow` between `v0` and `Other`. No conditional logic needs to change (Q9–Q12 still trigger off Q8 tier, not Q7 platform).

When the Tally webhook fires into the AI pipeline, the platform value `Webflow` should be passed through to `scripts/ai_audit.py --platform webflow --builder Webflow`. See `docs/WEBFLOW-EXPANSION.md` for the full handoff.

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Conditionals missing | Q8 options must be exactly `Starter Package ($9)` and `Full Package ($29)` |
| Thanks page on site is mailto | Set `intakeFormUrl` in config and deploy |

---

Site already points at **9qodVE**. Only update `config.js` if you publish a new Tally URL.
