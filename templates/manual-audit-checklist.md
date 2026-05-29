# LaunchLook — Fast manual audit (≈15 min)

High-impact checks that match what we sell. **Not** a security pentest or code review.

**Setup (1 min):** Public URL in Chrome (not builder preview). Notion template open. `findings_library/findings.json` or `python scripts/findings_lookup.py <keyword>`.

**Starter Package:** do sections 1–5 → write up to **7** findings.  
**Full Package:** add section 6 → up to **20** findings.

---

## 1. First impression scan (3 min) — placeholders & dev leftovers

Walk homepage + footer **without clicking yet**. Scan for:

- [ ] Lorem ipsum, `Your Company Name`, `[Insert …]`, Acme/Example (`FL-001`–`FL-004`, `FL-007`)
- [ ] Default builder hero (“Welcome to your new app”, etc.) (`FL-003`, `FL-035`)
- [ ] Placeholder emails `@example.com` / `@yourdomain.com` (`FL-006`)
- [ ] **Dev bypass**, Seed/Clear data, debug panels on live URL (`FL-036`)
- [ ] Product name in header (not platform default)

*Fast trick:* Ctrl+F mentally for `lorem`, `TODO`, `example`, `your company`, `acme`.

---

## 2. Trust & links (2 min)

- [ ] `/privacy` and `/terms` — not 404 (`FL-008`, `FL-009`)
- [ ] Footer has **support email** or `/contact` (`FL-010`)
- [ ] Click **2–3 footer/nav links** only — any 404? (`FL-012`)

*Skip:* crawling every link on the site (too slow for MVP).

---

## 3. One critical path (5 min) — broken functionality

From intake: *the main thing users do* (sign up, book, pay, create, submit).

- [ ] **Primary CTA** completes or shows clear error (`FL-038`, `FL-011`)
- [ ] **One main form** submit → success or visible failure (`FL-013`)
- [ ] DevTools **Console** on that page — errors tied to broken UI? (`FL-015`)
- [ ] DevTools **Network** — red failed calls on load/submit? (`FL-016`)

*Skip:* clicking every button on every page (unless Full Package and time left).

---

## 4. Mobile sanity (3 min)

DevTools → **375px** (iPhone SE), reload homepage + main path page:

- [ ] Horizontal scroll? (`FL-017`)
- [ ] Hero CTA still visible and tappable? (`FL-019`)

*Skip:* testing every breakpoint and device.

---

## 5. Auth quick probe (2 min) — only if app has login

- [ ] Sign up with fresh email → confirmation arrives? (`FL-022`)
- [ ] **Incognito** open `/dashboard`, `/settings`, `/admin` → must redirect/login, not data (`FL-020`)

*Skip:* password reset, OAuth providers, role matrices.

---

## 6. Full Package only (+10 min)

- [ ] **User A vs User B:** can either see the other’s private data? (`FL-021`) — use intake test accounts
- [ ] Second page in main flow (settings, list, profile) — repeat §3 lightly
- [ ] Paste URL in Slack — title/description/image OK? (`FL-023`–`FL-025`) — 1 min

---

## Write-up (5 min)

1. Verdict: 🟢 Ready / 🟡 Fix first / 🔴 Don’t ship  
2. Findings: **Critical → High → Medium** (screenshot each)  
3. Paste-into-builder text from library — substitute `{ACTUAL_NAME}`, `{PAGE}`, `{BUTTON_NAME}`  
4. **Starter:** add Quick Start Guide in Notion  

---

## Deliberately skip (out of scope / slow)

- Full-site link crawl, Lighthouse, pentest, RLS/API review  
- Every empty/loading/error state (only if obvious on main path)  
- Native iOS/Android apps  
- Multi-page help centers  

Recommend **VAS / VibeEval** when they need deep security.

---

## Severity cheat sheet (what to report first)

| Priority | Examples |
|----------|----------|
| **Critical** | Dev tools on prod, broken signup/pay/submit, auth bypass, cross-user data, placeholder contact email |
| **High** | Missing privacy/terms, placeholders, 404 nav links, mobile horizontal scroll, failed API calls on main flow |
| **Medium+** | Weak meta preview, no favicon, empty dashboard, generic 404 page — if time / Full Package |

CLI reminder: `python scripts/audit_checklist.py` (Starter) · `python scripts/audit_checklist.py --tier launch` (Full).
