# LaunchLook — Build the Tally intake form (checklist)

**Time:** ~30–45 minutes

**All copy-paste text (questions, thank-you, notifications):** [`TALLY-COPY-PASTE.md`](TALLY-COPY-PASTE.md) ← open this while you build the form.

**When done:** paste publish URL into `landing/assets/config.js` → `intakeFormUrl` → push. Update [`ROB-REMAINING-TODO.md`](ROB-REMAINING-TODO.md).

---

## Before you open Tally

| Prerequisite | Where |
|--------------|--------|
| Stripe success URLs → `/thanks` | [Stripe Payment Links](https://dashboard.stripe.com) — values in [`TALLY-COPY-PASTE.md` § Stripe](TALLY-COPY-PASTE.md#stripe-set-in-dashboard-not-tally) |
| Inbox works | `hello@launchlook.app` → your real inbox |
| Notion (optional day 1) | **LaunchLook Ops** → **Customers** DB — [`templates/notion/customers-db.csv`](../templates/notion/customers-db.csv) |

---

## Build steps

- [ ] 1. Create form at [tally.so](https://tally.so) — **Start from scratch**
- [ ] 2. Form settings (title, single page, English) — [`TALLY-COPY-PASTE.md` § Form settings](TALLY-COPY-PASTE.md#form-settings-before-questions)
- [ ] 3. Paste **Block 0** (security text)
- [ ] 4. Add **Questions 1–15** in order — copy labels, help, options from [`TALLY-COPY-PASTE.md`](TALLY-COPY-PASTE.md)
- [ ] 5. Set **conditional logic** — [cheat sheet](TALLY-COPY-PASTE.md#conditional-logic-cheat-sheet)
- [ ] 6. Paste **thank-you page**
- [ ] 7. Turn on **email notifications** → `hello@launchlook.app`
- [ ] 8. (Optional) **Notion** integration → Customers DB
- [ ] 9. **Publish** → wire `intakeFormUrl` in `config.js` → push
- [ ] 10. Run **test checklist** at bottom of [`TALLY-COPY-PASTE.md`](TALLY-COPY-PASTE.md#test-before-outreach)

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Thanks page still mailto | `intakeFormUrl` empty or not deployed — set in `config.js` and push |
| Conditionals don’t show | Tier option text must match exactly `Full Package ($29)` — re-copy from Q8 in [`TALLY-COPY-PASTE.md`](TALLY-COPY-PASTE.md) |
| URL question rejects staging | Use **Link** field; allow `http` and `https` |
| Notion row missing | Re-authorize integration; map required fields |

---

## Related docs

| Doc | Purpose |
|-----|---------|
| [`TALLY-COPY-PASTE.md`](TALLY-COPY-PASTE.md) | **Verbatim paste content** |
| [`templates/intake-form-spec.md`](../templates/intake-form-spec.md) | BL-07 technical spec |
| [`ROB-REMAINING-TODO.md`](ROB-REMAINING-TODO.md) | Everything left for Rob |
| [`07-launchlook-go-live.md`](07-launchlook-go-live.md) | Full go-live + E2E |

Paste your Tally URL in chat to wire `config.js` automatically.
