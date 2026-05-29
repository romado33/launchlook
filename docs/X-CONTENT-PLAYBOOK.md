# X (Twitter) content playbook — LaunchLook

**Owner:** Rob · **Status:** Active May 2026  
**Companion:** [`OUTREACH-PLAYBOOK.md`](OUTREACH-PLAYBOOK.md) §2a (launch-window search), §3.8 (free-offer post) · [`PLATFORM-CHEAT-SHEET.md`](PLATFORM-CHEAT-SHEET.md)

Use this when running an X account that posts real findings (screenshots) from LaunchLook audits. Goal: education + launch-window help, not dunking on founders.

---

## 1. Account positioning

**Bio (example):** Pre-launch checkups on vibe-coded apps (Lovable, Bolt, v0, Webflow). Public URL only. I post one real “first visitor” issue per day — broken flows, placeholders, mobile.

**Pinned post:** 3-slide or short video — placeholder footer, dead CTA, mobile overlap — plus “DM your public URL for **2 free findings** (human-reviewed).”

**Disclosure:** ~1 in 3 posts: *“I built LaunchLook — this is what our pass surfaces.”*

**Do not:**
- Roast founders for engagement
- Post full reports, login screens, or PII (blur emails/names)
- Frame every post as “competitors missed it” (reads petty)
- Link `launchlook.app` in every reply (bio + DM after engagement)

**Do:**
- One finding per post, one screenshot, plain English
- Tie posts to launch moments (PH, “just shipped,” beta)
- Offer free **2 findings** in DMs when someone engages (canonical free tier — see `PRODUCT-DECISIONS.md` §1)

---

## 2. Post formats

| Format | Share | Notes |
|--------|-------|--------|
| Single finding | ~80% | Screenshot + “what happened” + “why before PH” |
| Pattern roundup | Weekly | “4 Lovable apps this week had the same footer placeholder” — no names without permission |
| Before/after | When founder fixes | Ask permission in delivery email |
| Poll + screenshot | Occasional | “Would you send this link today?” — curious tone |
| Free offer | Monthly | Variant #6 in `OUTREACH-PLAYBOOK.md` §3.8 — use **2 free findings** |

**Single-post template:**

```
Founder shipped {APP} ({PLATFORM}).

First-visitor issue: {ONE LINE}.

{SCREENSHOT}

Would you send this link to a stranger today?
```

**Comparison posts (max 1 per 10 posts):** Same public URL — show PageLens (or another scanner) surfaced SEO/perf vs LaunchLook surfaced workflow/mobile/trust. Close with canonical line: *“PageLens is a scanner. LaunchLook is a scanner with judgment.”* (`PRODUCT-DECISIONS.md` §6). Do not @ competitors.

---

## 3. What to scan (starter sources)

Rob’s hands-on builder experience is **Lovable-first**; URL audits work on any platform. See [`PLATFORM-CHEAT-SHEET.md`](PLATFORM-CHEAT-SHEET.md) for prompt/voice differences.

### Tier A — start here

| Source | Why |
|--------|-----|
| X search §2a (`OUTREACH-PLAYBOOK`) | `"just shipped" lovable.app`, `"launching on Product Hunt"`, `"built with lovable"` + feedback |
| Lovable Discord showcase | `#show-and-tell` — live URLs, pre-launch founders |
| Product Hunt — AI tools, this week | Launch-window polish |
| `launchlook.app/sample` | Controlled screenshot for pinned post |
| Indie Hackers “share your project” | Public URLs, feedback-seeking |

**Sweet-spot signals** (two in 90 seconds → audit): Edit-with-Lovable badge, placeholder footer, dead Get Started, missing `/privacy`, mobile CTA off-screen.

### Tier B — after ~10 posts

- Webflow “Made in Webflow” launches (Designer-specific findings — spot-check fix prompts)
- Bolt / v0 showcase posts with live links
- Named indie tools — **DM founder first** before naming on X

### Tier C — skip for now

- Login-only apps without test accounts
- Enterprise / regulated industries
- Random big-brand sites (no founder audience)

---

## 4. Weekly rhythm

| Day | ~time | Action |
|-----|-------|--------|
| Daily | 10 min | X Advanced Search §2a — reply with **one** public observation; no link in first reply |
| Mon | 30 min | Audit 3 URLs from Discord or PH → queue 3 posts |
| Tue–Thu | 15 min/day | Publish 1 finding post |
| Fri | 15 min | Free-offer post (2 findings) |
| Sat (optional) | 20 min | 1 comparison or pattern post |

Track: replies → DMs → free audits → paid (Notion Outreach Tracker). Likes are vanity.

---

## 5. Ethics & ops

- **Public marketing URLs only** unless founder supplied test logins (Scale Up/Pro lane — not X teasers).
- **Naming apps:** Prefer “a Lovable-built SaaS landing” until permission.
- **Shareable reports:** `/r/{slug}` is private by default; screenshots are safer than linking reports without opt-in (`landing/faq.html`).
- **CTA:** Bio link + DM; push **Scale Up $49** in DMs when they’re PH-bound, not Starter price wars.

---

## 6. Pricing & competitive framing on X

Do **not** argue “we’re cheaper than PageLens.” Argue **different job:**

- PageLens / fast scanners → speed, scores, crawl
- LaunchLook → signup, email, mobile, founder-reviewed, paste-into-builder fixes

Canonical pricing: hold **$19 / $49 / $99**; free hook is **$0, 2 findings** (`PRODUCT-DECISIONS.md` §7). Revisit Starter → $9 only with conversion data — not because intel doc says so (`COMPETITIVE-INTEL.md` §4.4, updated May 2026).

---

## 7. First two weeks checklist

- [ ] Bio + pin + disclosure habit
- [ ] 5× single-finding posts (Lovable URLs from Discord/X)
- [ ] 1× pattern post (no app names)
- [ ] 1× free-offer post (2 findings)
- [ ] 10 min/day on §2a replies (no pitch in first reply)
- [ ] Optional: 1 comparison post after rhythm feels natural
