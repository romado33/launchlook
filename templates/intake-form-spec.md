# Intake form spec (BL-07)

Tally.so configuration for the post-purchase intake form. Tally is free, no-code, supports conditional logic, and posts results to Notion natively.

## Where it lives

- Form URL: `https://tally.so/r/{form_id}`
- Linked from each Stripe Payment Link's `success_url`
- Also linked from the welcome email (template: `templates/email/welcome.txt`)

## Security notice (show at top of form)

Paste as a **Statement** or **Text** block before questions:

> **Please read before submitting**
> - Do not send your personal password, production admin logins, API keys, Stripe keys, or Supabase service keys.
> - For Launch ($29) only: create **temporary test accounts** (not real users). Submit credentials here only — not by email.
> - Do not submit apps with real customer health, financial, or children's data unless you have permission.
> - We delete test credentials within 24 hours of delivery. Rotate or delete test accounts after your report arrives.

## Form behavior

- Single page, 13 questions
- Mobile-friendly (Tally is by default)
- Required vs. optional clearly marked
- Conditional fields (test accounts) only appear for Launch ($29) tier
- Submit → thank-you screen → optional redirect to `https://launchlook.app/thanks`
- Tally → Notion integration writes each submission as a new row in the `Customers` database

## Fields (paste this into Tally's question editor)

### 1. What's your name?
- Type: Short answer
- Required: yes
- Placeholder: "First name is fine"

### 2. Email
- Type: Email
- Required: yes
- Help text: "Match the email you used at checkout if you can — makes things easier."

### 3. App URL
- Type: URL
- Required: yes
- Help text: "The live URL. Staging URLs work too if they're publicly reachable."
- Validation: must start with `https://` or `http://`

### 4. What does your app do?
- Type: Short answer (max 200 chars)
- Required: yes
- Help text: "One sentence. Plain language."
- Placeholder: "A shared to-do list for small teams."

### 5. Who's your main user?
- Type: Long answer
- Required: yes
- Help text: "1–2 sentences. Who's going to use this? What do they do?"

### 6. What's the main thing they do in your app?
- Type: Long answer
- Required: yes
- Help text: "The one thing your app is for. The main workflow."

### 7. Which platform built it?
- Type: Multiple choice (single select)
- Required: yes
- Options:
  - Lovable
  - Bolt
  - Base44
  - Replit
  - v0
  - Other (please specify in notes)

### 8. Which tier did you purchase?
- Type: Multiple choice (single select)
- Required: yes
- Options:
  - Starter ($9)
  - Launch ($29)
- Help text: "We know — we'll match against Stripe, but this confirms what you expect."

### 9. Can we use test accounts? *(Launch only)*
- Type: Multiple choice (single select)
- Required: yes (conditional on Q8 being Launch)
- Show only if: Q8 = "Launch ($29)"
- Options:
  - Yes — I'll provide two test accounts
  - I'll create test accounts using my own signup flow — you provision them
  - No — skip the cross-user check
- Help text: "The cross-user data check needs two real signed-in sessions. If you'd rather we just sign up two fresh accounts ourselves, that's fine — we'll delete them after."

### 10. Test account 1 email + password *(conditional)*
- Type: Long answer
- Required: yes if Q9 = "Yes — I'll provide two test accounts"
- Show only if: Q9 = "Yes — I'll provide two test accounts"
- Help text: "We'll only use these for the audit. We never store credentials beyond the scan."
- Placeholder: "Email: ... / Password: ..."

### 11. Test account 2 email + password *(conditional)*
- Type: Long answer
- Required: yes if Q9 = "Yes — I'll provide two test accounts"
- Show only if: Q9 = "Yes — I'll provide two test accounts"

### 12. Your support email *(Launch only)*
- Type: Email
- Required: yes (conditional)
- Show only if: Q8 = "Launch ($29)"
- Help text: "We'll reference this in your Quick Start Guide so users know how to reach you."

### 13. Anything specific to check?
- Type: Long answer
- Required: no
- Help text: "Anything broken you're worried about? Any flow you're unsure of? Optional."
- Placeholder: "I'm not sure the booking page works on mobile..."

### 14. How anxious are you about launching, 1–10?
- Type: Linear scale 1–10
- Required: no
- Labels: 1 = "Calm, just curious" → 10 = "Not sleeping"
- Help text: "Optional. Helps me match the tone of the report. Higher numbers get a warmer, more reassuring write-up."

## Notion integration

After form is built:

1. In Tally form settings → **Integrations** → **Notion**
2. Connect Tally's Notion integration to the `LaunchLook Ops` workspace
3. Map each Tally field to the matching column in the `Customers` database
4. Test by submitting the form yourself — verify a row appears in Notion

## Email notifications

In Tally form settings → **Notifications**:

- Email **hello@launchlook.app** on every submission
- Include all answers in the email body so Rob can start auditing without opening the form

## Privacy / data retention

Add this line to the thank-you screen:

> Your responses are stored privately in LaunchLook's internal workspace. Test account credentials are deleted within 24 hours of the audit. See [our privacy policy](https://launchlook.app/privacy) for details.

## Future automation (not MVP)

When BL-13 ships, a script will:
1. Read new Customers rows where `Intake Received` = true
2. Calculate `Delivery Due` = `Payment Date` + tier turnaround
3. Send the welcome email if not already sent
4. Notify Rob via email when delivery deadline is < 6 hours away
