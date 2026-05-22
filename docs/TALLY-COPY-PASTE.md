# LaunchLook — Tally intake form (complete copy-paste)

**Use this file only.** Open [tally.so](https://tally.so), create a form, and paste each block below in order.

**When published:** copy `https://tally.so/r/________` → `landing/assets/config.js` → `intakeFormUrl` → commit/push (or send URL to Cursor).

**Step-by-step checklist (checkboxes):** [`TALLY-INTAKE-SETUP.md`](TALLY-INTAKE-SETUP.md)  
**Owner todo list:** [`ROB-REMAINING-TODO.md`](ROB-REMAINING-TODO.md)

---

## Form settings (before questions)

| Setting | Value |
|---------|--------|
| Form title | `LaunchLook — Post-purchase intake` |
| Layout | Single page |
| Login required | Off |
| Language | English |

---

## Block 0 — Text (not a question)

**Tally block type:** Text / Statement (no input)

**Paste exactly:**

```
Please read before submitting

• Only submit temporary test accounts. Do not submit personal passwords, admin credentials, API keys, database credentials, real customer data, health data, children's data, or payment information.

• For Full Package ($29) only: create temporary test accounts (not real users). Submit credentials here only — not by email.

• We delete test credentials within 24 hours of delivery. Rotate or delete test accounts after your report arrives.
```

---

## Question 1 — Short text · Required

**Question label:**

```
What's your name?
```

**Placeholder:**

```
First name is fine
```

**Description / help:** *(leave empty or omit)*

---

## Question 2 — Email · Required

**Question label:**

```
Email
```

**Description / help:**

```
Match the email you used at checkout if you can — makes things easier.
```

---

## Question 3 — Link (URL) · Required

**Question label:**

```
App URL
```

**Description / help:**

```
The live URL. Staging URLs work too if they're publicly reachable.
```

**Validation:** URL format enabled (allow `http` and `https` if Tally offers the option).

---

## Question 4 — Short text · Required

**Question label:**

```
What does your app do?
```

**Description / help:**

```
One sentence. Plain language.
```

**Placeholder:**

```
A shared to-do list for small teams.
```

**Max length:** 200 characters (if Tally allows).

---

## Question 5 — Long text · Required

**Question label:**

```
Who's your main user?
```

**Description / help:**

```
1–2 sentences. Who's going to use this? What do they do?
```

---

## Question 6 — Long text · Required

**Question label:**

```
What's the main thing they do in your app?
```

**Description / help:**

```
The one thing your app is for. The main workflow.
```

---

## Question 7 — Multiple choice (single select) · Required

**Question label:**

```
Which platform built it?
```

**Options** *(one option per line in Tally):*

```
Lovable
Bolt
Base44
Replit
v0
Other
```

---

## Question 8 — Multiple choice (single select) · Required

**Question label:**

```
Which tier did you purchase?
```

**Description / help:**

```
We'll match against Stripe — this confirms what you expect.
```

**Options** *(must match exactly — logic depends on this text):*

```
Starter Package ($9)
Full Package ($29)
```

---

## Question 9 — Multiple choice (single select) · Required when visible

**Question label:**

```
Can we use test accounts?
```

**Description / help:**

```
The cross-user check needs two signed-in sessions. We can sign up fresh test accounts ourselves if you prefer — we delete them after the audit.
```

**Options:**

```
Yes — I'll provide two test accounts
I'll create test accounts using my own signup flow — you provision them
No — skip the cross-user check
```

**Logic:** Show this question **only when** Question 8 **is** `Full Package ($29)`  
**Required:** Yes when visible

---

## Question 10 — Long text · Required when visible

**Question label:**

```
Test account 1 — email and password
```

**Description / help:**

```
We'll only use these for the audit. Credentials are deleted within 24 hours of delivery.
```

**Placeholder:**

```
Email: ... / Password: ...
```

**Logic:** Show **only when** Question 9 **is** `Yes — I'll provide two test accounts`  
**Required:** Yes when visible

---

## Question 11 — Long text · Required when visible

**Question label:**

```
Test account 2 — email and password
```

**Description / help:**

```
We'll only use these for the audit. Credentials are deleted within 24 hours of delivery.
```

**Placeholder:**

```
Email: ... / Password: ...
```

**Logic:** Same as Question 10  
**Required:** Yes when visible

---

## Question 12 — Email · Required when visible

**Question label:**

```
Your support email (for the Quick Start Guide)
```

**Description / help:**

```
We'll put this in your one-page user guide so people know how to reach you.
```

**Logic:** Show **only when** Question 8 **is** `Full Package ($29)`  
**Required:** Yes when visible

---

## Question 13 — Long text · Optional

**Question label:**

```
Anything specific you want us to check?
```

**Description / help:**

```
Anything broken you're worried about? Optional.
```

**Placeholder:**

```
I'm not sure the booking page works on mobile...
```

**Required:** No

---

## Question 14 — Linear scale · Optional

**Question label:**

```
How anxious are you about launching?
```

**Description / help:**

```
Optional. Helps me match the tone of your report.
```

**Scale:** Minimum `1` · Maximum `10`

**Label for 1:**

```
Calm, just curious
```

**Label for 10:**

```
Not sleeping
```

**Required:** No

---

## Question 15 — Checkbox · Required (place just above Submit)

**Checkbox label** *(single required checkbox):*

```
I confirm I am submitting only temporary test credentials (if any) and no sensitive production data — no personal passwords, admin credentials, API keys, database credentials, real customer data, health data, children's data, or payment information.
```

**Required:** Yes

---

## Thank-you page (after submit)

**Settings → Thank you page** — paste:

```
Thanks — you're in.

We'll start your checkup within a few hours of this submission.

• Starter Package: report within 24 hours
• Full Package: report within 12 hours

Your responses are stored privately. Test account credentials are deleted within 24 hours of delivery.

Privacy policy: https://launchlook.app/privacy
Questions: hello@launchlook.app
```

**Optional redirect after submit:** `https://launchlook.app/thanks`  
*(Or leave empty — Stripe already sends buyers to `/thanks` first.)*

---

## Email notifications

**Settings → Notifications → Email notifications**

| Setting | Value |
|---------|--------|
| Send email on submission | On |
| To | `hello@launchlook.app` |
| Include | All answers in the email body |

Submit a test yourself and confirm the email arrives in your inbox.

---

## Notion integration (optional for day 1)

1. **Integrations → Notion → Connect**
2. Database: **Customers** in workspace **LaunchLook Ops**
3. Map fields:

| Tally question | Notion property |
|----------------|-----------------|
| What's your name? | Name |
| Email | Email |
| App URL | App URL |
| Which tier did you purchase? | Tier |
| Everything else | Notes *(until you add columns)* |

4. Test submit → confirm a new row appears.
5. Set **Payment Date** manually from Stripe (Tally does not send payment date).

**Customers DB columns:** see [`templates/notion/README.md`](../templates/notion/README.md) or import [`templates/notion/customers-db.csv`](../templates/notion/customers-db.csv).

---

## Conditional logic cheat sheet

| Question | Show when |
|----------|-----------|
| 9, 12 | Q8 **is** `Full Package ($29)` |
| 10, 11 | Q8 **is** Full **and** Q9 **is** `Yes — I'll provide two test accounts` |

**How to set in Tally:** Open question → **Logic** (or ⋮) → **Add condition**.

If conditionals never appear, the tier option text does not match exactly — re-copy from Question 8 above.

---

## Wire the live site

1. **Publish** in Tally.
2. Copy URL: `https://tally.so/r/________________`
3. Edit `landing/assets/config.js`:

```js
intakeFormUrl: "https://tally.so/r/YOUR_FORM_ID",
```

4. Commit and push to `romado33/launchlook` → Vercel redeploys.
5. Test: `https://launchlook.app/thanks` → button **Complete intake form** opens Tally (not mailto only).

---

## Optional: Tally “Create with AI” prompt

If you use Tally’s AI form builder, paste this once, then verify option text and add Block 0 (security text) + Question 15 (checkbox) manually:

```
Create a single-page English form titled "LaunchLook — Post-purchase intake".

Fields in order:
1. Short text required "What's your name?" placeholder "First name is fine"
2. Email required "Email" help "Match the email you used at checkout if you can — makes things easier."
3. URL required "App URL" help "The live URL. Staging URLs work too if they're publicly reachable."
4. Short text required max 200 "What does your app do?" help "One sentence. Plain language." placeholder "A shared to-do list for small teams."
5. Long text required "Who's your main user?" help "1-2 sentences. Who's going to use this? What do they do?"
6. Long text required "What's the main thing they do in your app?" help "The one thing your app is for. The main workflow."
7. Single choice required "Which platform built it?" options: Lovable, Bolt, Base44, Replit, v0, Other
8. Single choice required "Which tier did you purchase?" options exactly "Starter Package ($9)" and "Full Package ($29)" help "We'll match against Stripe — this confirms what you expect."
9. Single choice "Can we use test accounts?" options "Yes — I'll provide two test accounts", "I'll create test accounts using my own signup flow — you provision them", "No — skip the cross-user check" — show only if tier is Full Package ($29)
10. Long text "Test account 1 — email and password" show only if Q9 is Yes — I'll provide two test accounts
11. Long text "Test account 2 — email and password" same condition as 10
12. Email "Your support email (for the Quick Start Guide)" show only if Full Package ($29)
13. Long text optional "Anything specific you want us to check?"
14. Scale 1-10 optional "How anxious are you about launching?" labels 1 "Calm, just curious" and 10 "Not sleeping"
15. Required checkbox "I confirm I am submitting only temporary test credentials (if any) and no sensitive production data — no personal passwords, admin credentials, API keys, database credentials, real customer data, health data, children's data, or payment information."

Thank you message: Thanks — you're in. Starter 24h Full 12h. Credentials deleted within 24h. Privacy https://launchlook.app/privacy Questions hello@launchlook.app
```

---

## Test before outreach

- [ ] Starter path: Q9–Q12 hidden
- [ ] Full path: Q9–Q12 visible
- [ ] Q10–Q11 only when “Yes — I'll provide two test accounts”
- [ ] Q15 blocks submit if unchecked
- [ ] `hello@launchlook.app` receives full answers
- [ ] Stripe $9 and $29 success URLs → `https://launchlook.app/thanks`
- [ ] `/thanks` opens Tally after `intakeFormUrl` is set

---

## Stripe (set in dashboard, not Tally)

| Payment Link | Success URL | Cancel URL (if offered) |
|--------------|-------------|-------------------------|
| Starter $9 | `https://launchlook.app/thanks` | `https://launchlook.app/#pricing` |
| Full $29 | `https://launchlook.app/thanks` | `https://launchlook.app/#pricing` |

---

*Technical reference (field IDs, BL-07):* [`templates/intake-form-spec.md`](../templates/intake-form-spec.md)
