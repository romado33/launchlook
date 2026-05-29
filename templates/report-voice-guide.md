# LaunchLook — Report voice (non-technical founders)

Use this when writing **any** customer report. Paste-into-builder blocks can be technical (they go into Lovable/Bolt). **Everything else** is for a smart non-coder.

---

## Who you're writing for

- Built the app with Lovable, Bolt, v0, Cursor, etc.
- May not know: routes, APIs, RLS, console, metadata, endpoints, auth guards, CSP
- **Does** know: buttons, pages, sign-in, "it looks broken on my phone," Stripe, privacy page

---

## Rules

1. **Second person** — "you" and "your app," not "the application."
2. **Name what they see** — quote the **visible label** (`"Get started"`, `"Seed Sample Data"`), not `/dashboard` or `auth.uid()`.
3. **Short sentences.** One idea per sentence when possible.
4. **Say what users feel** — confused, don't trust it, think it's unfinished, can't complete signup.
5. **Paste-into-builder text is separate** — jargon belongs only inside the paste box, never in "What I saw" or "Why it matters."

---

## Say this → not that

| Avoid | Say instead |
|-------|-------------|
| Route, endpoint, URL path | Page, link, web address |
| Auth / authenticated | Signed in, logged in |
| Unauthenticated | Signed out, not logged in |
| RLS, query, Supabase | Who can see whose data / database rules |
| Console errors | Hidden errors in the browser (or skip — say "something failed to load") |
| Network request failed | Part of the page didn't load |
| Meta tags / OG | Link preview when you share on Slack, Twitter, iMessage |
| Favicon | Small icon in the browser tab |
| 404 | Page not found |
| Render / hydrate | Show up / load |
| Production / staging | Live link / test link |
| Cross-user data exposure | One user can see another user's {messages, bookings, files, etc.} |
| Pentest, CVE, compliance | *(don't use — out of scope)* |

---

## Severity labels (customer-facing)

| Label | Plain meaning |
|-------|----------------|
| 🔴 Critical | Fix before you share the link with real people |
| 🟠 High | Most visitors will notice on the first visit |
| 🟡 Medium | Matters once people actually use the app |
| ⚪ Low | Nice to fix; won't block a soft launch |

---

## Section checklist per finding

- [ ] **What I saw** — no code, no file paths unless the customer would recognize them (e.g. "/privacy" is OK)
- [ ] **Why it matters** — one real-world consequence
- [ ] **Paste into builder** — paste into {platform}; technical OK here
- [ ] Screenshot shows the same words you quoted

---

## Cross-user check (Full Package)

Write like a friend explaining what happened:

- "I signed in as your first test account and saw…"
- "Then I signed in as the second account and…"
- "Without signing in, I tried opening your dashboard page and…"

Never assume they know what "protected routes" means.

---

## Quick Start Guide (included on Starter + Full)

- Written for **their users**, not developers
- No "leverage," "seamless," "robust"
- Steps use button names and screen names from the real app
