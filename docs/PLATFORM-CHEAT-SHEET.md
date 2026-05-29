# Platform cheat sheet — auditing non-Lovable builders

**Owner:** Rob · **Status:** Active May 2026  
**Canonical tiers:** [`PRODUCT-DECISIONS.md`](PRODUCT-DECISIONS.md) §1 · **Fix-prompt voice:** `scripts/ai_audit/prompts/system.txt` (FIX PROMPT TONE BY BUILDER) · **Webflow SKU:** [`WEBFLOW-EXPANSION.md`](WEBFLOW-EXPANSION.md)

Rob’s day-to-day builder experience is **Lovable**. LaunchLook still audits **any live public URL** the same way (placeholders, CTAs, trust pages, mobile, lite URL checks). What changes is **fix-prompt dialect** and a few **intake questions** — not the core finding types.

---

## 1. What stays the same (every platform)

- First-visitor polish: placeholder copy, dead buttons, 404 legal pages, OG/meta gaps
- Workflow when test accounts exist: signup, forms, confirmation email
- Curated plain-English findings + paste-ready text for the buyer’s editor
- Pipeline: URL-first — no GitHub required (`PRODUCT-DECISIONS.md` §6 VibeDoctor line)

**~90% of findings** you see on Lovable appear on Bolt/v0/Replit/Cursor sites (often Vercel-hosted React).

---

## 2. Per-builder differences (fix prompts + buyer)

| Builder | Fix-prompt voice | Buyer notes | Watch for |
|---------|------------------|-------------|-----------|
| **Lovable** | Routes, visible copy, `import.meta.env.DEV` guards; light on file paths | Non-technical, no GitHub | Edit-with-Lovable badge, dev bypass on `/auth` |
| **Bolt** | Same as Lovable; **slightly more file-aware** if HTML evidenced paths | Similar to Lovable | Bolt branding on host; don’t invent `src/` paths |
| **v0** | Component-oriented (`SignIn.tsx`) **only if evidenced** | Slightly more dev-capable | `*.v0.dev` vs custom domain; preview ≠ prod |
| **Cursor** | Task-style: search `src/`, replace across app | Often has repo; may use VibeDoctor | Compete on **live workflow**, not CVE depth |
| **Replit** | Sequential: “first find homepage file, then…” | Mix of toys and real launches | Replit-hosted vs exported deploy |
| **Base44 / Other** | Generic Lovable shape (routes + copy) | Wix-adjacent audience | Don’t invent platform syntax |
| **Webflow** | Designer panels, **Publish**, breakpoints **991 / 767 / 478** | Freelancers, agencies | Forms, noindex, Designer≠live — see Webflow doc |

**Rule:** Never cite a file path you didn’t see in crawl/HTML. Lovable habit is routes-only; v0/Cursor allow paths with evidence.

---

## 3. Workflow differences (your manual pass)

| Step | Lovable | Others |
|------|---------|--------|
| Dev-only UI on production | Common (`import.meta.env.DEV`) | Same pattern, different prompt wording |
| Placeholder in 4 places | Builder fills one, forgets rest | **Same** — footer, title, meta, hero |
| Email confirmation | Often Supabase-shaped | Ask intake: magic link vs password; which test inbox |
| Mobile | Lovable typical widths | Webflow = fixed px; Next/v0 = verify with screenshots |
| Hosting badge | “Edit with Lovable” | Bolt/Replit equivalents — same finding type |
| Repo | Usually none | Cursor buyers may have GitHub — you still don’t need it |

**Intake:** Trust Tally **“Which platform built it?”** over guessing from domain.

**Staging:** Ask “Is this the URL strangers will hit on launch day?” — common on v0/Bolt previews.

---

## 4. Webflow (parallel SKU)

Not “Lovable with a different logo.”

- Run `--platform webflow` or set Platform in audit UI
- Spot-check: every fix prompt uses **Designer** language and **Publish** (ban `npm`, `src/`, Lovable phrasing)
- Extra categories: form email failure, noindex, JSON-LD, breakpoint breakage (`WEBFLOW-EXPANSION.md` §3)

You can audit Webflow URLs without owning Webflow; **sanity-check one prompt in Designer** before shipping, or note in delivery you validated voice only.

---

## 5. Outreach when you only know Lovable

Use **Variant #3.5** in [`OUTREACH-PLAYBOOK.md`](OUTREACH-PLAYBOOK.md):

> Free pre-launch checkups this week on **{PLATFORM}** apps so I can learn how your builder differs from Lovable.

Honest, sets expectations, builds the per-platform prompt library.

**Safe public line (X, Discord):**  
*“Built with {platform} — same pre-launch polish we see on Lovable: placeholder still in the live footer.”*

---

## 6. Pre-ship checklist (non-Lovable paid report)

1. YAML `customer.builder` matches Tally
2. Every `fix_prompt` opens with the right builder name and dialect (`system.txt`)
3. No Lovable-only assumptions (Supabase, `lovable.app` badge) unless true
4. Webflow: header says “LaunchLook for Webflow”, breakpoints in px
5. Manual workflow test notes which test account was used

---

## 7. Related docs

| Doc | Use |
|-----|-----|
| [`X-CONTENT-PLAYBOOK.md`](X-CONTENT-PLAYBOOK.md) | Posting findings; Lovable-heavy prospecting OK |
| [`OUTREACH-PLAYBOOK.md`](OUTREACH-PLAYBOOK.md) §2a | X launch-window searches |
| [`vs-vibedoctor.md`](../landing/vs-vibedoctor.md) | Repo scanners vs live URL |
| [`SITE-BUILDER-MARKET-RESEARCH.md`](SITE-BUILDER-MARKET-RESEARCH.md) | Why WordPress/Shopify aren’t expanded |
