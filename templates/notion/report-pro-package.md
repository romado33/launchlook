# LaunchLook — Pro Package checkup for {APP_NAME}

> **Tier:** Pro Package ($99) · **Delivered:** {DATE} · **By:** Rob at LaunchLook  
> **Also emailed:** Main Report PDF · Quick Start Guide PDF · Pre-Launch Checklist PDF · Handoff Report PDF  
> **Scheduled separately:** 30-minute Loom walkthrough (email to book)

**Audience:** Non-technical founder. Plain English in **What I saw** / **Why it matters**; technical detail only in **Paste into builder** boxes. See `templates/report-voice-guide.md`.

**What we tested:** Desktop + phone width, visitor workflows (forms, signup, confirmation emails), two test accounts for data isolation, and a surface-level review of how {STRIPE / AUTH / EMAIL / ANALYTICS} are wired from what we can see without repo access.

---

## Summary

**Overall verdict:** {🟢 Ready to share / 🟡 Needs a few fixes first / 🔴 Don't ship yet}

{2–3 sentences. Lead with what's working. Name the top 1–2 risks in plain language.}

This report has **up to 40 findings** (this report shows **{N}**), a **Quick Start Guide** for your users, a **Handoff Report** (emailed as its own PDF), and notes from the **integrations review** below. Your **Loom walkthrough** is booked separately — we'll walk through the report together on video.

---

## How to read this report

| Part | What's in it |
|------|----------------|
| **Part 1** | Findings (severity-sorted) |
| **Part 2** | Two-account isolation check |
| **Part 3** | Integrations review (Stripe, auth, email, analytics) |
| **Part 4** | Quick Start Guide for your users |
| **Part 5** | Loom walkthrough + Handoff Report pointers |

| | Plain English |
|---|----------------|
| 🔴 Critical | Fix before sharing the link |
| 🟠 High | Obvious on a first visit |
| 🟡 Medium | Fix once people are using it |
| ⚪ Low | Polish |

---

# Part 1 — Findings

## 🔴 Critical — fix before you share the link

### Finding 1 — {short title}

**What I saw**  
{Quote visible UI. Desktop + phone screenshots when they differ.}

> 📸 [Screenshot — desktop]  
> 📸 [Screenshot — phone, if different]

**Why it matters**  
{User/trust impact.}

**Paste into {PLATFORM} to fix this**

```
{paste-ready prompt}
```

---

(repeat through Critical → High → Medium → Low; up to **40** findings for Pro)

---

# Part 2 — Two-account check (Pro Package)

You provided two temporary test accounts. I signed in as each and checked whether **User A could see User B's data**, plus what happens **without signing in**.

### As test account 1

{Plain language observations.}

### As test account 2

{Plain language observations.}

### Without signing in

{Private-window behavior on dashboard / settings / billing URLs.}

{if clean: "Each account only saw its own data, and protected pages asked me to sign in."}

---

# Part 3 — Integrations review (Pro Package)

From your intake answers and what’s visible on the live app (not a full security audit of third-party dashboards).

| Integration | What you told us | What I checked | Status |
|-------------|------------------|----------------|--------|
| **Payments (Stripe)** | {e.g. Live mode / test mode / not sure} | {Checkout reachable? Success/cancel URLs? Obvious test keys in page source?} | {🟢 OK / 🟡 Fix soon / 🔴 Blocker} |
| **Auth** | {e.g. Supabase / Clerk / custom} | {Signup, login, logout, password reset paths} | {status} |
| **Email** | {e.g. Resend / SendGrid / built-in} | {Did confirmation / welcome emails arrive from our workflow tests?} | {status} |
| **Analytics** | {e.g. GA / Plausible / none} | {Tag present on key pages? Obvious double-load or missing on thank-you page?} | {status} |

### Integration notes (plain English)

{2–5 short paragraphs: biggest misconfigurations, what breaks at launch, what to fix before paid traffic. No secret keys in this section — if you need to rotate a key, say "rotate in your provider dashboard" only.}

---

# Part 4 — Quick Start Guide for your users

> 📄 **Quick Start Guide PDF** — attached to your delivery email (includes deep links where applicable)  
> 📝 **Notion copy** (optional duplicate below)

---

{Paste edited QSG — end-user language, not engineer speak}

---

# Part 5 — Loom walkthrough + Handoff Report

## Loom walkthrough

> **Status:** {📅 Scheduled for DATE / ⏳ Email sent to book / ✅ Recorded — link below}

{Loom URL when ready, or: "Reply to your delivery email with two times that work and we'll record a 30-minute walkthrough of this report."}

We'll cover: your top 🔴/🟠 findings, the two-account check, and anything confusing in the integrations table.

## Handoff Report (separate PDF)

The **Handoff Report** is formatted for your repo / AI builder: stack summary, env vars checklist, file map, and "what to fix first" — so you or a contractor can onboard without re-reading every finding.

> 📄 **Handoff Report PDF** — attached to your delivery email  
> 🔗 **Optional share link** — reply **share** if you want a public `launchlook.app/r/{slug}` page

{Optional: 2–3 bullet summary of what the Handoff emphasizes for this customer.}

---

## What's next

1. **Today** — 🔴 Critical  
2. **Before promote** — 🟠 High + integrations marked 🔴  
3. **Publish** — Quick Start Guide somewhere users can find it  
4. **Watch** — Loom when scheduled  
5. **Build** — use Handoff Report + paste-into-builder fix text in your AI builder  

**Fix Check:** Reply **recheck** after you ship fixes — included once on Pro within 14 days, or $19 standalone.

---

## Share LaunchLook (optional)

**Free audit:** https://launchlook.app/#hero · **Referral:** **{REFERRAL_CODE}** ($5 off you + friend)

---

*LaunchLook · hello@launchlook.app*
