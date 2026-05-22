# LaunchLook — Build the Tally intake form (step by step)

**Time:** ~30–45 minutes · **Spec:** [`templates/intake-form-spec.md`](../templates/intake-form-spec.md)

When done you’ll have a URL like `https://tally.so/r/AbCdEf` → paste into `landing/assets/config.js` → `intakeFormUrl` → push to GitHub.

---

## Before you open Tally

### Stripe (both Payment Links)

| Setting | Value |
|---------|--------|
| **After payment / Success URL** | `https://launchlook.app/thanks` |
| Cancel (if shown) | `https://launchlook.app/#pricing` |

Customers read expectations on `/thanks`, then click through to Tally.

### Notion (optional for day 1, recommended)

1. Create workspace **LaunchLook Ops** (or use existing).
2. New database **Customers** with at least these columns:

| Column | Type |
|--------|------|
| Name | Title or text |
| Email | Email |
| App URL | URL |
| Tier | Select (Starter Package $9, Full Package $29) |
| Payment Date | Date |
| Intake Received | Checkbox |
| Delivery Due | Date |
| Delivered | Checkbox |
| Notes | Long text |

Extra Tally fields (builder, anxiety, test accounts) can map to **Notes** until you add more columns.

3. You’ll connect Tally → Notion in **Integrations** after the form is built.

### Email

- Tally will email **hello@launchlook.app** on each submission (set in Notifications).
- Confirm that inbox works before you go live.

---

## 1. Create the form

1. Go to [tally.so](https://tally.so) → **+ Create form** → **Start from scratch**.
2. **Title:** `LaunchLook — Post-purchase intake`
3. **Settings → General:** one page (default). No login required.
4. **Settings → Language:** English.

---

## 2. Security notice (first block)

Add block: **Text** (not a question).

Paste:

```
Please read before submitting

• Only submit temporary test accounts. Do not submit personal passwords, admin credentials, API keys, database credentials, real customer data, health data, children's data, or payment information.

• For Full Package ($29) only: create temporary test accounts (not real users). Submit credentials here only — not by email.

• We delete test credentials within 24 hours of delivery. Rotate or delete test accounts after your report arrives.
```

---

## 3. Questions (in this order)

For each: add the block type noted → paste label, help text, options.

| # | Tally type | Question label | Required | Help / options |
|---|------------|----------------|----------|----------------|
| 1 | Short text | What's your name? | Yes | Placeholder: `First name is fine` |
| 2 | Email | Email | Yes | Help: `Match the email you used at checkout if you can — makes things easier.` |
| 3 | Link (URL) | App URL | Yes | Help: `The live URL. Staging URLs work too if they're publicly reachable.` Enable validation: must be URL |
| 4 | Short text | What does your app do? | Yes | Max 200 chars if Tally allows. Placeholder: `A shared to-do list for small teams.` Help: `One sentence. Plain language.` |
| 5 | Long text | Who's your main user? | Yes | Help: `1–2 sentences. Who's going to use this? What do they do?` |
| 6 | Long text | What's the main thing they do in your app? | Yes | Help: `The one thing your app is for. The main workflow.` |
| 7 | Multiple choice | Which platform built it? | Yes | Single select. Options: `Lovable` · `Bolt` · `Base44` · `Replit` · `v0` · `Other` |
| 8 | Multiple choice | Which tier did you purchase? | Yes | Single select. Options exactly: `Starter Package ($9)` · `Full Package ($29)`. Help: `We'll match against Stripe — this confirms what you expect.` |

### Conditional block — Full Package only

**Question 9** — Multiple choice · **Can we use test accounts?**

- Options:
  - `Yes — I'll provide two test accounts`
  - `I'll create test accounts using my own signup flow — you provision them`
  - `No — skip the cross-user check`
- Help: `The cross-user check needs two signed-in sessions. We can sign up fresh test accounts ourselves if you prefer — we delete them after the audit.`
- **Logic:** Show only when **Q8** = `Full Package ($29)`
- Required when visible

**Question 10** — Long text · **Test account 1 — email and password**

- Placeholder: `Email: ... / Password: ...`
- Help: `We'll only use these for the audit. Credentials are deleted within 24 hours of delivery.`
- **Logic:** Show only when **Q9** = `Yes — I'll provide two test accounts`
- Required when visible

**Question 11** — Long text · **Test account 2 — email and password**

- Same logic as Q10

**Question 12** — Email · **Your support email (for the Quick Start Guide)**

- Help: `We'll put this in your one-page user guide so people know how to reach you.`
- **Logic:** Show only when **Q8** = `Full Package ($29)`
- Required when visible

### Everyone sees these

| # | Tally type | Label | Required |
|---|------------|-------|----------|
| 13 | Long text | Anything specific you want us to check? | No | Help: `Anything broken you're worried about? Optional.` Placeholder: `I'm not sure the booking page works on mobile...` |
| 14 | Linear scale | How anxious are you about launching? | No | Min 1 label: `Calm, just curious` · Max 10: `Not sleeping`. Help: `Optional. Helps me match the tone of your report.` |
| 15 | Checkbox | I confirm I am submitting only temporary test credentials (if any) and no sensitive production data — no personal passwords, admin credentials, API keys, database credentials, real customer data, health data, children's data, or payment information. | **Yes** |

**Tally conditional UI:** Click question → **⋮** or **Logic** → **Add condition** → “When [Which tier…] is [Full Package ($29)]”.

---

## 4. Thank-you screen

**Settings → Thank you page** (or after submit message):

```
Thanks — you're in.

We'll start your checkup within a few hours of this submission.

• Starter Package: report within 24 hours
• Full Package: report within 12 hours

Your responses are stored privately. Test account credentials are deleted within 24 hours of delivery.

Privacy policy: https://launchlook.app/privacy
Questions: hello@launchlook.app
```

Optional redirect URL: leave empty (Stripe already sent them to `/thanks`) **or** `https://launchlook.app/thanks` if you want a second landing.

---

## 5. Notifications (do this before going live)

**Settings → Notifications → Email notifications**

- Turn on: email to **hello@launchlook.app** on new submission
- Include: **all answers** in the email body

Submit a test yourself and confirm the email arrives.

---

## 6. Notion integration (when Customers DB exists)

1. **Integrations → Notion → Connect**
2. Select **Customers** database
3. Map fields:

| Tally field | Notion property |
|-------------|-----------------|
| What's your name? | Name |
| Email | Email |
| App URL | App URL |
| Which tier did you purchase? | Tier |
| (everything else) | Notes — or add columns later |

4. After each submit, check a new row appears.
5. Manually check **Intake Received** when you start the audit (or automate later).

**Payment Date** won’t come from Tally — set from Stripe when you see the payment (manual for week 1).

---

## 7. Publish and wire the site

1. **Publish** in Tally → copy link: `https://tally.so/r/________`
2. Open `landing/assets/config.js`:

```js
intakeFormUrl: "https://tally.so/r/YOUR_FORM_ID",
```

3. Commit + push (or send the URL to Cursor).
4. Test flow:
   - Open `https://launchlook.app/thanks`
   - Button should say **Complete intake form** and open Tally (not only mailto)
   - Submit test → email + Notion row

---

## 8. Quick test checklist

- [ ] Full Package path shows Q9–Q12; Starter hides them
- [ ] Q10–Q11 only when “Yes — I'll provide two test accounts”
- [ ] Checkbox Q15 blocks submit if unchecked
- [ ] hello@launchlook.app receives full answers
- [ ] Stripe $9 and $29 both land on `/thanks` first

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Thanks page still mailto | `intakeFormUrl` empty or not deployed — set in `config.js` and push |
| Conditionals don’t show | Tier option text must match exactly `Full Package ($29)` |
| URL question rejects staging | Use **Link** field; allow `http` and `https` |
| Notion row missing | Re-authorize integration; map required fields |

---

## After it's live

Update [`ROB-REMAINING-TODO.md`](ROB-REMAINING-TODO.md) — check off Tally + E2E sections.

Paste your Tally URL in chat to wire `config.js` automatically.
