# LaunchLook — Build the Tally intake form (checklist)

**Time:** ~30–45 minutes

## Which copy file?

| Method | File |
|--------|------|
| **Recommended** | [`TALLY-AI-ONE-SHOT.txt`](TALLY-AI-ONE-SHOT.txt) → Tally **Create form with AI** |
| Field-by-field | [`TALLY-INTAKE-PASTE.txt`](TALLY-INTAKE-PASTE.txt) |
| Thank-you only | [`TALLY-THANK-YOU-PASTE.txt`](TALLY-THANK-YOU-PASTE.txt) |

Do **not** paste from `TALLY-COPY-PASTE.md` (that file is only an index).

**When done:** paste publish URL into `landing/assets/config.js` → `intakeFormUrl` → push.

---

## Before you open Tally

| Prerequisite | Where |
|--------------|--------|
| Stripe success URLs → `/thanks` | Stripe Payment Links dashboard |
| Inbox works | `hello@launchlook.app` |
| Notion (optional) | **LaunchLook Ops** → **Customers** — [`templates/notion/customers-db.csv`](../templates/notion/customers-db.csv) |

---

## Build steps

- [ ] 1. **AI path:** Paste [`TALLY-AI-ONE-SHOT.txt`](TALLY-AI-ONE-SHOT.txt) into Tally Create with AI  
      **OR manual path:** Add blocks from [`TALLY-INTAKE-PASTE.txt`](TALLY-INTAKE-PASTE.txt) in order
- [ ] 2. Verify Q8 options are exactly `Starter Package ($9)` and `Full Package ($29)`
- [ ] 3. Set conditional logic on Q9–Q12 (see end of TALLY-INTAKE-PASTE.txt)
- [ ] 4. Paste thank-you from [`TALLY-THANK-YOU-PASTE.txt`](TALLY-THANK-YOU-PASTE.txt)
- [ ] 5. Notifications → `hello@launchlook.app`, include all answers
- [ ] 6. (Optional) Notion integration
- [ ] 7. Publish → `intakeFormUrl` in `config.js` → test `/thanks`

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Pasted markdown, looks wrong | Use `.txt` files only |
| Conditionals don’t show | Tier text must be exactly `Full Package ($29)` |
| Thanks page still mailto on site | Set `intakeFormUrl` and deploy |

---

Paste your Tally URL in chat to wire `config.js` automatically.
