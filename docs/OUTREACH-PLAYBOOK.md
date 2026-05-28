# LaunchLook — Outreach Playbook

**Last updated:** May 28, 2026
**Owner:** Rob
**Status:** Canonical reference for soft customer acquisition. Use this as your single source of truth for *where* to post, *what* to say, and *what not* to do.

This consolidates every forum/community recommendation and every ready-to-paste pitch wording generated across the LaunchLook planning sessions. Mine it; don't re-derive it.

---

## 0. Pre-outreach blockers — complete these before any promotion

> **Do not start broad outreach until all four are checked.** A founder clicking through to a site with zero social proof and no visible delivery SLA will bounce. These four items are the difference between wasted effort and a real conversion.

- [ ] **Get 3 real testimonials.** Offer 3–5 free or $5 discounted audits to founders in your network or in the Lovable Discord. Ask for one-sentence feedback after delivery (`ask-for-quote.txt`). Add the quotes to `landing/index.html` and `landing/webflow.html`. One genuine "Found 2 things I would have missed" is worth more than any copy change.
- [ ] **Add turnaround SLA to landing page.** Founders in a launch window need to know if you'll deliver in 24 hours or 2 weeks. Add "Reports delivered within 48 hours" (or same-day if you can commit) above the pricing grid. Without it, a time-pressured founder won't buy.
- [ ] **Record the Loom or remove it from the Pro card.** The Pro tier card says "Rob walks you through the report on video." If that Loom doesn't exist yet, either record it now (see §3.11 for the 60-second script) or remove the line from the Pro card until it does. Promising something undeliverable on a $99 product will cause the first refund.
- [ ] **Clear stale test rows from Notion.** The queue currently has `romado33@gmail.com` rows sitting "In Progress"/"Paid" since May 25–27, plus `tally-test@example.com` and `stripe-test@example.com` from live testing. Delete them so real orders don't get lost in the noise. Also verify the Windows Task Scheduler is running and processing the 7 pending free audits.

**Once all four are checked:** the funnel is genuinely ready. Go to §7 (Week-1 game plan) and execute.

**Related docs:**

- [`templates/forum-posts.md`](../templates/forum-posts.md) — raw forum post variants (1–6). This playbook reorganizes them by use case; that file is still the canonical source if you want to edit the wording in isolation.
- [`templates/cold-outreach-loom-script.md`](../templates/cold-outreach-loom-script.md) — 60-second Loom structure.
- [`templates/week-1-free-sample-playbook.md`](../templates/week-1-free-sample-playbook.md) — how to find 5 apps and deliver a free sample.
- [`templates/email/free-sample-outreach.txt`](../templates/email/free-sample-outreach.txt) — cold email template.
- [`docs/SHARE-AND-REVIEWS.md`](SHARE-AND-REVIEWS.md) — weekly rhythm + tracking.
- [`docs/ROB-REMAINING-TODO.md`](ROB-REMAINING-TODO.md) — what must be done before any outreach.

---

## 1. Outreach strategy overview

### The goal

> **30 targeted messages → 3 strangers pay $19.**

That's the only number that matters right now. Three paying strangers proves the wedge. Until you've hit it, every hour spent polishing the site is an hour stolen from outreach.

### The mode you are in: **soft acquisition, not broad promotion**

| Do this | Don't do this |
|---------|---------------|
| Direct DMs (10–30/week) | Run paid ads |
| Looms (3/week, Monday) | Build automation funnels |
| Discord replies in threads where people *asked* for feedback | Spam any channel with the same copy |
| Reddit comments on "feedback wanted" posts | Drop launchlook.app links as the first thing you say |
| Reply to founder posts on LinkedIn/Twitter | Cross-post the same paragraph in 10 places |
| Free 10-min checkups in showcase channels | Promise security audits, pentests, code review |

### Pacing recommendation (per week, ~30 min/day)

| Day | Activity | Volume |
|-----|----------|--------|
| Mon | Record 3 Looms for prospects you scouted last week. DM each with a link to the checklist. | 3 |
| Tue | Reply in 2–3 Lovable/Bolt Discord threads where someone shared a URL. Use variant #3 (3 specific findings). | 2–3 |
| Wed | One LinkedIn post — one finding pattern + checklist link, no pitch. | 1 |
| Thu | Scout next week's prospects (10 URLs into your Outreach Tracker). | — |
| Fri | Ask last week's customers for a quote ([`ask-for-quote.txt`](../templates/email/ask-for-quote.txt)). | — |

**Quality over volume.** 5 thoughtful Discord replies > 50 cold DMs. A single "this was useful" beats 100 unread emails.

### What NOT to do until you have ≥3 paying customers

- No ads (Google, Meta, X) — you don't have a CAC number yet.
- No automation — manual delivery teaches you what the future scanner should check.
- No Hacker News — wrong audience for $19/$49; they'll roast a non-technical product.
- No broad LinkedIn / X promotion — earn the follow first with one value post.
- No pre-buying domains, building dashboards, or "improving the funnel" before three strangers pay.

### Reality check: what proven from research

- **Demand is real and self-initiated.** The Lovable Discord already builds free peer tools (Testers Helping Testers) and reaches for Claude + MCP. Nobody in those communities is currently selling a paid, structured, plain-English pre-launch pass. The wedge is open.
- **Competing positioning to avoid:** "raw AI scanner that dumps 100 findings," "security audit," "QA platform," "peer testing." You are **the AI-powered scan with founder-curated quality, fix-prompt-included once-over**.
- **Best wedge sentence:** *"A 10-minute pre-launch pass: AI scans every screen, I personally review every finding before it reaches you. Plain English, with copy-paste fix prompts for your builder."*

---

## 2. Target communities — ranked by priority

The order below is signal-to-effort for your first 5–10 customers. **Discord first** because it's the fastest feedback loop. **Reddit second** because it scales. **IH / LinkedIn last** because they're warmer but slower. **Hacker News: skip entirely** until you have 10 paying customers.

### Tier 1 — post / engage immediately

| # | Community | URL | Channels / subreddits | Why it fits | Recommended variant |
|---|-----------|-----|------------------------|-------------|---------------------|
| 1 | **Lovable Discord** | [lovable.dev/discord](https://lovable.dev/discord) | `#show-and-tell`, `#lovable-built-showcase`, `#feedback` | Highest concentration of your buyer; people literally post URLs asking for feedback | **Variant #3** (reply to existing thread with 3 findings) |
| 2 | **Bolt Discord** | bolt.new community | `#showcase` (or equivalent) | Same dynamic as Lovable, smaller community | Variant #3 or #2 (short Discord post) |
| 3 | **r/vibecoding** | reddit.com/r/vibecoding | — | Active, on-topic, audience is exactly you | **Variant #1** (long form) + Variant #3 when replying |
| 4 | **r/SideProject** | reddit.com/r/SideProject | sort by New, flair "Launch" | High volume of "feedback wanted" posts | Variant #3 (reply-only strategy) |

### Tier 2 — warm up before posting (lurk 3–7 days, then engage)

| # | Community | URL | Notes | Variant |
|---|-----------|-----|-------|---------|
| 5 | **r/lovable** | reddit.com/r/lovable | Smaller, friendlier, less moderation | Variant #1 |
| 6 | **Indie Hackers** | indiehackers.com | "Share your project" section; builders looking for feedback. Higher quality, slower. | Variant #1 |
| 7 | **r/Replit** | reddit.com/r/Replit | Replit-built apps are often "almost ready" | Variant #1 / #3 |
| 8 | **r/nextjs + r/webdev** | — | Catch v0 / Cursor users; less vibe-coded skew | Variant #1 |
| 9 | **Twitter / X** | x.com | Search `built with lovable`, `lovable.app`, `v0.dev` (last 7 days). **Monitor launch-window signals** (see §2a below). | **Variant #6** (single post). Earn the follow before pitching. |
| 10 | **LinkedIn** | linkedin.com | Build-in-public circles; one weekly post tied to a finding pattern | **Variant #4** (pure value, no offer). Builds long-term credibility. |

### Tier 3 — later / opportunistic

- **Base44 community** — small but builder-focused; check Discord or built-in showcase. Watch for live URLs.
- **v0 community** — Vercel-hosted; watch the v0.dev showcase and `r/nextjs`.
- **Cursor community** — Discord + cursor.com/forum. Less direct-fit (Cursor users are more technical), but the free 3-finding audit link can land.
- **Product Hunt** — AI tools filter, this week's launches. Mostly useful for prospecting (find pre-launch founders to DM), not for posting.
- **Founder communities** (MicroConf, Tiny Seed, On Deck, Indie Worldwide) — Tier 3 unless you're already a member. Cold join doesn't work here.

### §2a. Twitter/X real-time launch-window monitoring

This is the highest-intent channel when a founder is actively counting down to launch. The buying signal is the *moment* they post about launching — not a week before or a week after.

**Search queries to run daily (X Advanced Search → "Latest"):**

| Query | Signal |
|-------|--------|
| `"launching on Product Hunt"` | Direct purchase intent — they have a date |
| `"launching next week" (lovable OR bolt OR cursor OR v0)` | Urgency window open |
| `"built with lovable" (launching OR launch OR "going live")` | Platform-specific launch moment |
| `"just shipped" (lovable.app OR bolt.new OR v0.dev)` | Just-launched — ideal for free findings reply |
| `"vibe coded" (launching OR launch OR feedback)` | General vibe-coder pre-launch |
| `"built this with" (lovable OR cursor OR bolt) "feedback"` | Actively asking for review |

**What to do when you find a signal:**
1. Click the live URL. Spend 90 seconds. Find one real thing.
2. Reply publicly: *"Congrats on the upcoming launch — I noticed {ONE_SPECIFIC_THING} on {PAGE}. Happy to send 2–3 more things if useful."*
3. Do **not** link to launchlook.app in the first reply. Wait for the "yes please."
4. If they say yes, DM the free findings. Then follow Variant #3.7 two days later.

**Frequency:** 10 minutes/day. Set a recurring reminder. The signal is perishable — a founder who tweeted "launching next week" is no longer a hot prospect in two weeks.

### §2b. Wall of Launches — when and how to use it

The Wall of Launches (`launchlook.app/wall`) is hidden until you have 5 entries. Until then, don't reference it in outreach. Once you have 5:

- Add it to the nav (`landing/index.html` header nav)
- Reference it in delivery emails as social proof
- Add a "Get listed on the Wall of Launches" CTA to the thanks page

**Permission:** Yes, you need permission before listing anyone's app. The cleanest way is to add a checkbox to the Tally intake form: *"I'm happy for LaunchLook to list my app on the Wall of Launches after I ship."* Until that checkbox exists, ask individually via the delivery email referral block.

### How to work the Lovable Discord showcase efficiently

This is your #1 channel. Specific instructions:

1. Join via [lovable.dev/discord](https://lovable.dev/discord).
2. Open the showcase forum (usually `#show-and-tell` or `#lovable-built-showcase`). If channel names changed, look for the one whose description is "share what you built."
3. Filter for **recent posts** (last 7 days).
4. Open threads that include a **live URL** (`*.lovable.app`, custom domain, Vercel, Netlify).
5. Skip: screenshots-only posts, Figma mocks, "idea only — no link yet," Lovable staff/template showcases, threads with 50+ replies.
6. **Sweet spot prospects:** pre-launch or just-launched, reachable founder (Discord profile + optional Twitter), real flows (signup / book / pay / dashboard), not a portfolio piece.
7. **Star 10 URLs/week** in your Outreach Tracker. Reply to 2–3 of them with Variant #3 the same day. Save the rest as DM/Loom targets for next week.

### Signals an app is a good practice target (and a good prospect)

You'll see these constantly in showcase posts — they're literally what LaunchLook sells:

- `*.lovable.app` still shows the **"Edit with Lovable"** badge
- **"Hosted by …" / "Your Company Name" / "Lorem ipsum"** placeholders
- Missing `/privacy` or `/terms` (404s)
- **"Get Started"** / **"Quick Book"** buttons that go nowhere
- Dev bypass or seed-data UI still on the public URL

If you see two of those in 2 minutes, audit it.

---

## 3. Pitch / message wording library

Every pitch below is ready to paste. Bracketed `{TOKENS}` are personalization variables — replace before sending.

### 3.1 — The ChatGPT-suggested first-customer pitch (canonical opener)

This is the cleanest single-paragraph pitch. Use it in DMs, short forum replies, and as the body of cold emails.

```
I'm testing LaunchLook: a $19 pre-launch checkup for apps built with Lovable, Bolt, Replit, v0, Cursor, etc. You send your live URL. AI scans every screen and drafts findings, then I personally review and curate every one before it reaches you. You get back the things a real first user would notice: broken buttons, placeholder text, trust gaps, mobile issues, confusing flows, plus paste-ready prompts to fix them in your builder. I'm looking for a few early users this week and will refund it if it's not useful.
```

Use it when: you want one paragraph that explains the offer, signals "early / honest," and includes the risk reversal (refund).

---

### 3.2 — Long-form forum post (Reddit, Indie Hackers, big Discord channels)

Use in `r/vibecoding`, `r/SideProject`, `r/lovable`, `r/Replit`, `r/nextjs`, Indie Hackers, or any forum that allows multi-paragraph posts. Lead with the free offer; soft-mention the paid product only at the end (or not at all on Reddit).

```
Offering free 10-minute pre-launch checkups this week: Lovable / Bolt / Base44 / v0 / Cursor

I'm a technical writer (15 years) who's been spending time looking at vibe-coded apps that are almost-but-not-quite ready to share with real users. There's a pattern: the app works fine for the founder, but a stranger opening the link spots three or four things in the first minute that the founder stopped seeing weeks ago.

Reply with your public URL (staging links are fine, just not localhost) and I'll send back 2 to 3 specific things in plain English. AI helps me scan every screen at desktop and mobile sizes; I personally review every finding before sending it. No security jargon, no pentest, no "you need to refactor your auth layer." Just the stuff a first-time visitor will notice: dead buttons, placeholder text, broken trust pages, mobile layout problems.

What I'll look at (about 10 minutes per app):
- Does anything on the homepage scream "this is unfinished"?
- Do the main buttons / forms actually work?
- Does it look OK on a phone?
- Are /privacy, /terms, /contact real pages or 404s?

What I won't do: deep security, code review, anything that needs your repo.

I'll do as many as I can fit in this week. First come first served.

(If you want the long version with screenshots and copy-paste fix prompts for your builder, I do that as a paid service. Please don't pay for what I'm offering free here. Reply with your URL and let's start there.)
```

---

### 3.3 — Short Discord post (Lovable `#show-and-tell`, Bolt `#showcase`)

For chat-style channels where walls of text die. Keep it ≤ 5 lines.

```
Offering a free 10-min "would I send this link today?" pass on vibe-coded apps this week.

Drop your public URL (staging OK) and I'll reply with 2 to 3 specific things a first-time visitor would notice: dead buttons, placeholder copy, mobile layout, trust pages. AI helps me scan, but I personally review every finding before sending. Plain English, no security jargon.

Not a code review or pentest. URL only.
```

---

### 3.4 — Reply on someone else's "feedback wanted" thread (highest-converting variant)

Use in any "Show HN" / "Show-and-tell" / "Feedback wanted" thread. **Substitute your real findings before posting.**

```
Just ran {APP_NAME} through our pre-launch pass (AI scans every screen, I curate). A few things I noticed as a first-time visitor:

1. {Specific thing #1: what you saw, in plain English. Quote the exact button or text in quotes.}
2. {Specific thing #2}
3. {Specific thing #3: keep it concrete and visual}

None of these are showstoppers, but they're the kind of stuff a stranger spots in the first 30 seconds. Happy to go deeper if useful. DM me your builder (Lovable / Bolt / v0 / etc.) and I can send copy-paste prompts to fix them.
```

**Substitution rules:**
- 3 findings max in the public reply.
- Always use the exact visible label in quotes (`"Get Started"`, `"Your Company Name"`).
- Never name the bug in technical terms — say *"the sign-up button doesn't go anywhere"* not *"the CTA's onClick handler is missing"*.

---

### 3.5 — "Free audit for testers" offer (non-Lovable platforms)

Use this when you're trying to validate the wedge on Bolt / v0 / Cursor / Base44 / Replit. The framing is "I'm testing my format on your builder this week."

```
Quick offer for {PLATFORM} builders: I'm doing free pre-launch checkups this week, specifically on {PLATFORM} apps so I can learn how your builder differs from Lovable.

What you get: I'll spend 10 to 15 minutes on your live app. AI scans every screen at desktop and mobile, then I personally review and curate 2 to 3 specific things I'd want fixed before you share the link wider: placeholders, dead buttons, mobile layout, trust pages. Plain English, no security jargon.

What I'm getting: I'm building a paste-ready fix-prompt library for {PLATFORM}, so seeing real {PLATFORM} apps helps me get the prompts right.

Reply with your public URL (staging OK). First 3 in are guaranteed; I'll do as many more as I can fit.
```

---

### 3.6 — Pure value post (no offer, top-of-funnel)

Post once a week. Picks one finding pattern from your library, shows the pattern, no link. Use this on LinkedIn (Variant #4) and as the "warm up the community" play before any pitch.

```
The most common thing I see on Lovable / Bolt apps that are about to launch:

The footer still says "Your Company Name" or "© 2024 Your Brand Inc."

Founders stop seeing it after week one. Strangers see it in three seconds and assume the app isn't finished. It signals "this is a prototype" even when the app underneath is fine.

The five-second fix: Ctrl+F your homepage source for "your company" — if it's there, swap it. Then check the footer, the page title, and the meta description tags. The builder usually fills the placeholder in one place and leaves it in three others.
```

Rotate the finding each week. Pull from `findings_library/findings.json` — FL-001, FL-006, FL-008, FL-020, FL-035 all make good single-post stories.

---

### 3.7 — Soft pitch (DM-only, after delivering a free finding)

Send by DM, never in the public thread. Wait until the founder has actually read and replied to your free notes.

```
Glad the {SPECIFIC_THING} catch was useful.

If you want the full version, with ranked findings with screenshots, the fixes that actually matter, and copy-paste prompts you drop into {BUILDER}, that's what LaunchLook does ($19 Starter, $49 Scale Up, $99 Pro). AI scans every screen; I personally review and curate every finding before delivery. No GitHub access. 48-hour turnaround.

launchlook.app — or drop your URL on the home page for 3 free findings from a real person (24-hour turnaround, no credit card). No pressure either way.
```

---

### 3.8 — Twitter / X single post (Variant #6)

Hook + offer + soft outro. No threads in the first one — earn the follow first.

```
Free this week: I'll do a 10-minute "would I send this link today?" pass on your vibe-coded app.

Reply or DM with your public URL. AI scans every screen, I personally curate the findings, you get back 2 to 3 things a first-time visitor would actually notice: broken buttons, placeholder text, mobile layout, trust pages.

No security stuff, no code review, just the polish layer.
```

If it gets engagement, follow up days later with one of the findings as a quote-tweet: *"Did 6 of these this week — the #1 thing I caught was…"*

---

### 3.9 — LinkedIn build-in-public post

Use weekly. Tie to one finding, link the free 3-finding audit form (not the pricing page). Always disclose you're the founder.

```
After running a dozen pre-launch apps built with Lovable / Bolt / v0 through our pre-launch pass this month, the #1 polish issue isn't broken code. It's leftover placeholders.

"Your Company Name" in the footer. "Hosted by …" in the metadata. "Get Started" button that goes to /undefined. The builder fills these in once and forgets them in three other places.

Drop your live URL at launchlook.app and a real person will email you back 3 free findings within 24 hours. No credit card.

(Disclosure: I run LaunchLook, a $19 pre-launch checkup for vibe-coded apps. AI scans every screen, I personally review and curate every finding before delivery. The free 3-finding audit is a stripped-down version of the paid Starter.)
```

---

### 3.10 — Cold email (free sample outreach)

From [`templates/email/free-sample-outreach.txt`](../templates/email/free-sample-outreach.txt). Use after you've already done the free audit on someone's app — *send the report with the email*.

```
Subject: I noticed a few things about {APP_NAME} — no charge

Hi {NAME},

I'm Rob, I run LaunchLook: pre-launch checkups for vibe-coded web apps (Lovable, Bolt, v0, Cursor, and similar). Saw you launched {APP_NAME} on {PLATFORM}, looks promising.

I ran your app through our pre-launch pass (AI scans every screen, I curate the findings) as a sample. Here's what came back:

{NOTION_REPORT_LINK}

No charge — would love your honest feedback on whether this is useful. Even one-line answers help:

- Was anything in here something you'd actually fix?
- Was anything obvious or trivial?
- Would you have paid $19 for it?

Either way, thanks for letting me poke around. Good luck with the launch.

— Rob
hello@launchlook.app
```

**Tone notes:**
- Acknowledge it's unsolicited.
- Frame as "I was testing my format" so it doesn't feel like a sales pitch.
- The three questions at the end are the actual research goal — pay attention to the answers more than the praise.
- "Either way" removes pressure.

---

### 3.11 — Loom + DM combo (Mondays, ~3/week)

**60-second Loom structure:**

| Time | What you say / show |
|------|--------------------|
| 0:00–0:10 | Show their app in the browser. *"Hey [name], I ran [app name] through our pre-launch pass and clicked through the screenshots."* |
| 0:10–0:35 | Show 2 to 3 specific issues (dead button, placeholder text, missing privacy, dev tools visible). No jargon. |
| 0:35–0:50 | *"I run LaunchLook, a pre-launch checkup for vibe-coded apps. AI scans every screen, I personally curate the findings. Plain-English report plus copy-paste fix prompts for your builder."* |
| 0:50–1:00 | CTA: *"Starter Package is $19 if you want the full list. Link: launchlook.app"* |

**DM text to pair with the Loom:**

```
Hey [name] — I recorded a 60-sec walkthrough of [app] before you share it wider.
[LOOM LINK]

I flagged [issue 1] and [issue 2]. LaunchLook does a full pass for $19 (Starter Package) with fix prompts you paste into [Lovable/Bolt/etc].

Or drop your URL on launchlook.app for 3 free findings from a real person — 24-hour turnaround, no credit card.

No pressure — launchlook.app if useful.
```

**Loom rules:**
- Never use the word "security" as the lead. Use polish / placeholders / sharing risks.
- Never say "audit." Use "checkup" or "second pair of eyes."
- Lead with what you saw, not the tooling. "AI scans every screen, I curate" is the framing for when someone asks how it works, not the opener.
- Personalize the first line with something specific you saw.

---

### 3.12 — Direct DM to a founder who just launched

Short, specific, no link in the first message.

```
Hey {NAME}, saw you just shipped {APP_NAME} on {PLATFORM}. Congrats.

I do quick pre-launch checkups for vibe-coded apps (AI scans, founder curates, no code access, just the live URL). I clicked through yours for a minute and noticed {ONE_SPECIFIC_THING}. Happy to send a quick free pass with 2 to 3 more if that's useful, just say the word.
```

If they reply "sure," send the free findings via DM. Then use **Variant #3.7 (soft pitch)** 24 hours after they've read it.

---

## 4. Tracking & measurement

### Referral flywheel

Every delivery email now includes a **$10 off a future audit** referral credit offer. This kicks in passively once you have paying customers — no outreach needed. Track referral conversions in the Outreach Tracker with a "Referral source" column. After you have 3–5 customers, add a "Referred by" Notion property so you can close the loop manually.

### What to track

Your existing scripts handle the customer side. For outreach, use either:

- **Notion "Outreach Tracker" database** (recommended, schema in `templates/notion/outreach-db.csv`)
- **A spreadsheet** with these columns:

| Column | Example |
|--------|---------|
| Date | 2026-05-26 |
| Prospect (name / handle) | @sarah_lovable |
| App URL | https://sarah-app.lovable.app |
| Channel | Lovable Discord / r/SideProject / LinkedIn DM |
| Variant used | #3 (reply) / #11 (Loom+DM) / #10 (cold email) |
| Sent (Y/N + date) | Y 2026-05-26 |
| Reply (Y/N + date + summary) | Y 2026-05-27 "useful, will fix #2" |
| Free findings sent | Y 2026-05-27 |
| Soft pitch sent (date) | 2026-05-28 |
| Converted ($19 / $49 / $99 / no) | $19 |
| Notes | Wants to retest in 2 weeks |

### Metrics to watch (week-by-week)

| Metric | Healthy | Watch out |
|--------|---------|-----------|
| Replies per 10 messages | ≥ 2 | < 1 → pitch is wrong |
| "This was useful" per 10 free passes | ≥ 4 | < 2 → findings aren't landing |
| Conversion (paying) per 10 "useful" replies | ≥ 1 | 0 across 30 free passes → price or trust issue |
| Time per message | ≤ 15 min | > 30 min → tighten the workflow |

### When to revisit the playbook

- **After 4 weeks of outreach:** drop the variants that produced zero replies. Keep the rest. Reread `docs/02-strategy-and-context.md` decision tree:
  - **8+ paying customers?** Wedge is real. Begin light automation. Consider adding a launch discount code or bundle offer to accelerate momentum.
  - **3–7 paying customers?** Wedge is unclear. Iterate the pitch. Run another 30 outreach attempts.
  - **0–2 paying customers?** The pitch, audience, or product is wrong. Don't build more. Investigate the funnel.

---

## 5. Common objections & responses

Real ones surfaced in the Lovable Discord research thread and review feedback.

| Objection | Response |
|-----------|----------|
| *"Isn't this just an AI scanner? I can use Claude / MCP / VibeDoctor."* | "Honest answer: AI does the first pass. It scans every screen, finds patterns, drafts findings. Then I personally review and curate every finding before it reaches you. That's the part raw AI scanners skip. AI scanners are noisy and speak in `SEC-001` jargon; the founder review rejects the false positives, edits anything that reads off, and adds the human judgment AI tools miss. You get scanner-speed delivery with human-curated quality." |
| *"How is this different from PageLens AI?"* | Point them to the canonical comparison: [`launchlook.app/vs-pagelens`](https://launchlook.app/vs-pagelens). Short answer: PageLens is built for SEO marketers who want recurring dashboards; LaunchLook is built for vibe coders shipping with Lovable / Cursor / Bolt who want a one-off pre-launch checkup with paste-ready fix prompts and a real founder reviewing every finding. Both are real tools; they solve different problems. Do **not** trash PageLens in the conversation, let the comparison page (with its built-in "Honest trade-offs" section) do the heavy lifting. Stay neutral per `SIMPLICITY-GUARDRAILS.md` §6 (brand voice). |
| *"Is the AI part going to fill my report with hallucinated issues?"* | "That's exactly why the founder review exists. I look at every AI-drafted finding against the actual screenshots before sending. If a finding isn't grounded in real evidence, it doesn't ship. Most reports end with fewer findings than the AI initially drafted; that's the curation working." |
| *"I already know my app has issues — I don't need someone to tell me."* | "Probably true for the bugs you already see. The point is the ones you **stopped seeing** weeks ago — every founder has them. If you want, send the URL and I'll do a free 10-min pass; if it's all stuff you already knew, no harm done." |
| *"$19 seems steep for something automated."* | "It's AI-drafted, founder-curated. AI gives me scanner-speed; the founder review is what keeps the bar high. That's why it's $19 instead of free (a real human reads every finding) and $19 instead of $99 (the AI carries the volume work). Rather you buy Starter now and Scale Up closer to launch, than pay once for something generic." |
| *"Will this catch the scary security stuff?"* | "Not deep security (no pentest, no code review). I do catch obvious visible risks though — dev bypasses, exposed test controls, broken auth screens, and (Full Package only) one user seeing another user's data via cross-account checks." |
| *"Why should I trust you?"* | "Two ways: drop your URL on [launchlook.app](https://launchlook.app/#hero) for a free 3-finding audit — that's a stripped-down sample of what a paid checkup looks like. Or read the [sample report](https://launchlook.app/sample) and decide if the output is worth $19. And there's a 7-day full refund if it isn't." |
| *"Do I need to give you my GitHub / repo access?"* | "Never. Just the live URL. If your Full Package run needs to check cross-user data, you give me two temporary test accounts via the intake form. No code, no repo, no admin." |
| *"My app is built with v0 / Cursor / Base44, not Lovable. Do you do those?"* | "Yes. The fix prompts are tailored per builder — Lovable, Bolt, v0, Cursor, Base44, Replit, and a generic one for everything else. The findings are the same; the prompt syntax differs." |
| *"Will the report tell me anything I can't get for free?"* | "The free 3-finding audit gives you the top 3 a real person would flag. What you can't get for free: the full ranked list (10 to 40 items) with paste-ready prompts, plus (Starter+) a one-page Quick Start Guide you can hand to your users. No competitor includes that last one." |
| Silence / no reply after 5 days | Don't follow up. Log the no-response. That's data. |

---

## 6. Posting rules & etiquette cheat sheet

### Always

- ✅ **Personalize the first line.** Mention something specific you saw or something the prospect said.
- ✅ **Vary the wording per community.** Same offer; different framing per channel.
- ✅ **Engage in threads before posting your own.** 3 helpful comments → then 1 post.
- ✅ **Lead with real free value.** A 10-min free pass or the free 3-finding audit link (`launchlook.app/#hero`), never the pricing page.
- ✅ **Disclose your role honestly.** "I run LaunchLook" — never "a friend of mine runs..."
- ✅ **Reply within 2 hours** to anyone who drops a URL.
- ✅ **Use the exact visible label in quotes** when describing a finding (`"Get Started"`, not "the CTA").

### Never

| Don't | Why |
|-------|-----|
| Post the same copy in 5 places | Looks spammy. Mods talk. You get flagged. |
| Say "security audit" / "pentest" / "vulnerability scan" | Different product, you can't deliver it, you'll get flagged in security-aware subs |
| Say "AI-powered" without "founder-curated" | The trust premium is the human review. Always pair the two: "AI scans, I personally curate." Never bare "AI-powered." |
| Say "Notion report" | Confuses non-Notion users; say "shareable report" |
| Open with *"I built LaunchLook because…"* | Makes the post about you. Make it about them. |
| Put pricing in the first line | Lead with help, not a price tag |
| Drop `launchlook.app` in post #1 on Reddit | Most subs auto-flag self-links. Mention in comments only. |
| Pitch on someone else's launch thread | Their moment. Help, don't sell. Soft-pitch in a follow-up DM. |
| Spam Testers Helping Testers' launch thread | Community antibodies. Complement THT, don't compete in-thread. |
| Cross-post the exact same paragraph | Vary per platform. Mods cross-reference. |
| Follow up more than once after silence | Don't. Their non-response is data. Log and move on. |

### What to do *after* posting

| When | Action |
|------|--------|
| Same day | Reply within 2 hours to every URL someone drops |
| +1 day | Send the free finding (DM or reply, depending on platform) |
| +2 days | If they said "this is useful," send Variant #3.7 (soft pitch) |
| +5 days | If silence, don't follow up. Log the no-response. |

---

## 7. Week-1 game plan (if you started today)

Pulled from the conversation; this is the version that has the best evidence behind it.

1. **Tonight or tomorrow:** Pick 2 Lovable Discord posts where someone asked for feedback. Click through their apps, write Variant #3.4 with 3 real findings each. Send. **Don't pitch.**
2. **Tomorrow:** Post Variant #3.2 (long-form) in `r/vibecoding`. Reply within 2 hours to every URL someone drops.
3. **Day 2:** Send the free findings via DM (same day = reply; day +1 = free finding; day +2 = soft pitch if they said "useful").
4. **Day 3–5:** Same playbook in Bolt Discord + r/SideProject.
5. **Track every interaction** — even silences — in `scripts/customers_track.py` or your Outreach Tracker. After 4 weeks, drop the variants that produced zero replies.

**The single highest-leverage thing** is being the person who shows up and replies with real findings when someone posts their app — not the person who runs a top-of-funnel campaign. **Variant #3.4 is your best weapon. The other variants are scaffolding.**

---

## 7b. Webflow community outreach (LaunchLook for Webflow SKU)

LaunchLook for Webflow is a parallel SKU at `launchlook.app/webflow`. Same $19 / $49 / $99 pricing, same fulfillment infrastructure, different audience and different language. Webflow customers don't live in `r/vibecoding` or the Lovable Discord — they live in Webflow-specific communities and most have never heard the phrase "vibe-coded."

### When to run this playbook

Run a Webflow-flavored outreach burst when you want to:
- validate whether the post-Nov-2024 form-failure pain shows up in real Webflow conversations
- prove the $899 price-gap thesis (people don't want to spend $899+ on Codeable for a pre-launch QA)
- diversify the funnel beyond AI-builder communities, which can feel saturated to repeat posters

Skip this playbook entirely until §1–4 of `ROB-REMAINING-TODO.md` are green for the vibe-coder SKU — the Webflow page is bonus surface, not the wedge.

### Target communities (priority order)

| # | Community | URL | Notes |
|---|-----------|-----|-------|
| 1 | **Webflow Forum** | [forum.webflow.com](https://forum.webflow.com) | Highest-signal channel. Look for threads tagged `forms`, `seo`, `cms`, `bug`. People post live URLs asking for help all day. |
| 2 | **r/Webflow** | [reddit.com/r/Webflow](https://www.reddit.com/r/Webflow/) | ~30k subscribers, active "Site critique" and "Help" flairs. Reply-only strategy works well here. |
| 3 | **Webflow Community Slack/Discord** | (invite via Webflow newsletter) | Smaller, friendlier. `#showcase` and `#help` are the sweet spots. |
| 4 | **Webflow Experts directory** | [webflow.com/experts](https://webflow.com/experts) | Cold-DM target. Many Experts get more handoff QA requests than they can take. They are not your competitor (they're full-build); you can be their pre-launch QA partner. |
| 5 | **Codeable freelancers** | [codeable.io](https://codeable.io) | Same logic as Webflow Experts — they ship sites and offload QA. |
| 6 | **Twitter/X #NoCode / #Webflow** | x.com search | Daily volume of "I just shipped my Webflow site" posts. Reply with a specific finding from a 30-second skim. |
| 7 | **Webflow Showcase** | [webflow.com/discover/popular](https://webflow.com/discover/popular) | Prospect-finding source, not posting venue. Save URLs into the Outreach Tracker. |
| 8 | **Memberstack / Wized / Finsweet communities** | each has their own Slack/Discord | Webflow-adjacent power-user channels. Approach as a quiet helper, not a vendor. |

### Three ready-to-paste Webflow pitches

**Webflow pitch #1 — Reply on a Webflow Forum thread where someone posted a URL**

```
Just clicked through your site. Three things a first-time visitor would notice before anything else:

1. {Specific thing #1: name the page and the exact element / copy}
2. {Specific thing #2: ideally tie it to a Webflow-specific failure mode — form silently failing, accidental noindex, mobile breakpoint overflow at 991/767/478}
3. {Specific thing #3}

I do a paid pre-launch checkup that catches the stuff Webflow Designer doesn't warn you about (forms silently failing since the Nov 2024 change, accidental noindex, missing JSON-LD, Designer-to-live mismatches). $19 to start, sits in the price gap below the $899 Codeable / Webflow Experts floor. URL only, no Workspace access needed: launchlook.app/webflow

Either way, those three are worth fixing before you push wider.
```

**Webflow pitch #2 — Short post in r/Webflow or Webflow Discord `#showcase`**

```
Pre-launch checkup for Webflow sites: $19 / $49 / $99.

What we catch that Webflow Designer doesn't warn you about: forms silently failing since the Nov 2024 update (most sites we audit have at least one), accidental noindex blocking Google, missing JSON-LD schema, Designer-to-live mismatches, mobile breakpoint breakage at 991 / 767 / 478.

URL only — no Workspace or Editor access. AI scans every page; a founder personally curates every finding before delivery. Sits below the $899 Webflow Experts / Codeable floor on purpose.

launchlook.app/webflow — drop your live URL if you want me to take a look.
```

**Webflow pitch #3 — Cold DM to a Webflow Expert or Codeable freelancer**

```
Hey {NAME} — saw you do full Webflow builds on {EXPERTS_OR_CODEABLE}. Quick question: do you ever wish you could hand off the pre-launch QA pass (broken forms, accidental noindex, schema gaps, mobile breakpoints) so you can stay on the build side?

I run LaunchLook for Webflow — a $19 / $49 / $99 pre-launch checkup. Designed to slot in as the layer between "Designer says it's done" and "client says it's done." URL only, 24-hour turnaround, white-label-friendly PDF on the $99 tier so you can pass it through to the client without our branding in the body.

If that sounds useful as a partnership (or even just a referral kickback), worth a quick chat. launchlook.app/webflow for the public version.
```

### Webflow-specific tracking columns

If you're keeping the Outreach Tracker in Notion (`templates/notion/outreach-db.csv`), add three columns for Webflow runs:

| Column | Example |
|--------|---------|
| Platform | Webflow |
| Webflow finding category | Form-fail / noindex / schema / breakpoint / mismatch |
| Codeable-Expert tier? | Yes / No (for partner-track prospects) |

Keep Webflow outreach separated in the tracker so you can compare reply rates to the vibe-coder funnel and decide whether to invest further in Webflow communities.

### Webflow-specific posting rules (in addition to the global rules in §6)

- **Never call Webflow a "no-code" tool dismissively.** Webflow's professional community treats "no-code" as a stigma. Say "Webflow site" or "Designer-built site." `#NoCode` is fine as a hashtag on Twitter/X for reach, but don't lead with it in long-form posts.
- **Never say "we audit your Webflow account."** Lead with "URL only, no Workspace access required." This is the single biggest trust premium over Codeable's audit format.
- **Always name the Nov 2024 form change when it's relevant.** It's the most specific, verifiable, recent pain point. People in `forum.webflow.com` know exactly what you mean.
- **Avoid pitching on someone else's "I just shipped!" launch thread in the public reply.** Reply with one helpful observation, then DM the soft pitch.
- **Don't compete with Codeable directly.** Position as the layer below — pre-launch QA, not a full audit. Codeable Experts can become referral partners if you treat them as such (see Webflow pitch #3).

---

## 8. Quick reference

| Item | Value |
|------|-------|
| Primary goal | 30 messages → 3 paying ($19) strangers |
| Site to share warm | https://launchlook.app/#hero (free 3-finding audit), then https://launchlook.app |
| Sample report (for skeptics) | https://launchlook.app/sample |
| Support / sending email | hello@launchlook.app |
| Tiers | Starter **$19** · Scale Up **$49** · Pro **$99** |
| Intake form | https://tally.so/r/QKOX1A |
| #1 channel | Lovable Discord `#show-and-tell` |
| #1 variant | #3.4 (reply with 3 specific findings) |
| Twitter monitoring queries | See §2a — run daily, 10 min |
| Forbidden words | "security audit," "pentest," "raw AI scanner," "Notion report" |
| Approved words | "checkup," "second pair of eyes," "polish layer," "what a first-time visitor would notice," "AI-drafted founder-curated" |
| Loom day | Monday (3/week) |
| LinkedIn day | Wednesday (1/week) |
| Quote-ask day | Friday |
| Wall of Launches | Hidden until 5 entries; need opt-in permission per app (see §2b) |
| Referral credit | $10 off next audit — in every delivery email automatically |
| Outreach tracker | Notion DB (schema: `templates/notion/outreach-db.csv`) |
| Customer tracker | `python scripts/customers_track.py stats` |
| Queue heartbeat | `python scripts/queue_heartbeat.py --dry-run` |
| Cadence rules | Same day reply → +1 day free finding → +2 days soft pitch → +5 days drop |

---

*This is the canonical outreach playbook. When variants get updated in `templates/forum-posts.md`, sync them back into Section 3 here so this stays your single reference.*
