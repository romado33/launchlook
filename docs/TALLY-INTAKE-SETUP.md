# LaunchLook — Build the Tally intake form (manual editor)

**Time:** ~30–45 minutes

## Copy file (plain text)

Open **[`TALLY-INTAKE-PASTE.txt`](TALLY-INTAKE-PASTE.txt)** in Notepad or VS Code.

Work top to bottom. For each section, add the Tally block type shown, then paste text between `>>> PASTE START` and `<<< PASTE END`.

Thank-you page text is at the bottom of the same file (or use [`TALLY-THANK-YOU-PASTE.txt`](TALLY-THANK-YOU-PASTE.txt)).

Do **not** paste from `.md` files — Tally will show formatting junk.

---

## Before you open Tally

| Prerequisite | Value |
|--------------|--------|
| Stripe success URL | `https://launchlook.app/thanks` |
| Notification email | `hello@launchlook.app` |

---

## Checklist

- [ ] New form → **Start from scratch**
- [ ] Form title: `LaunchLook — Post-purchase intake`
- [ ] Block 0: **Text** (security notice) — paste from file
- [ ] Questions 1–15 in order — paste titles, descriptions, placeholders, options
- [ ] Q7, Q8, Q9: use **Bulk insert options** for option lists
- [ ] Logic on Q9, Q10, Q11, Q12 (see bottom of paste file)
- [ ] Q15 checkbox required, above Submit
- [ ] Thank you page — paste from file
- [ ] Notifications → `hello@launchlook.app`, all answers
- [ ] Test Starter path (Q9–12 hidden) and Full path (Q9–12 visible)
- [ ] Publish → `intakeFormUrl` in `config.js` → push

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Conditionals missing | Q8 options must be exactly `Starter Package ($9)` and `Full Package ($29)` |
| Thanks page on site is mailto | Set `intakeFormUrl` in config and deploy |

---

Paste your Tally URL in chat to wire `config.js`.
