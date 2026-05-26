# LaunchLook — Outreach Playbook

**Last updated:** May 25, 2026
**Owner:** Rob
**Status:** Canonical reference for soft customer acquisition. Use this as your single source of truth for *where* to post, *what* to say, and *what not* to do.

This consolidates every forum/community recommendation and every ready-to-paste pitch wording generated across the LaunchLook planning sessions. Mine it; don't re-derive it.

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
- No Hacker News — wrong audience for $19 / $49 (with $99 Pro for deeper); they'll roast a non-technical product.
- No broad LinkedIn / X promotion — earn the follow first with one value post.
- No pre-buying domains, building dashboards, or "improving the funnel" before three strangers pay.

### Reality check: what proven from research

- **Demand is real and self-initiated.** The Lovable Discord already builds free peer tools (Testers Helping Testers) and reaches for Claude + MCP. Nobody in those communities is currently selling a paid, structured, plain-English pre-launch pass. The wedge is open.
- **Competing positioning to avoid:** "AI scanner," "security audit," "QA platform," "peer testing." You are **the AI-drafted, founder-curated, fast-turnaround, fix-prompt-included once-over** (Starter within 48h, Full within 24h, Pro within 24h + 30-min Loom — usually faster).
- **Best wedge sentence:** *"A pre-launch pass — what a stranger would notice in the first 30 seconds, in plain English, with copy-paste fix prompts for your builder. $19 entry, $99 if you want the deep version with an integrations review and a 30-min Loom walkthrough."*

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
| 9 | **Twitter / X** | x.com | Search `built with lovable`, `lovable.app`, `v0.dev` (last 7 days) | **Variant #6** (single post). Earn the follow before pitching. |
| 10 | **LinkedIn** | linkedin.com | Build-in-public circles; one weekly post tied to a finding pattern | **Variant #4** (pure value, no offer). Builds long-term credibility. |

### Tier 3 — later / opportunistic

- **Base44 community** — small but builder-focused; check Discord or built-in showcase. Watch for live URLs.
- **v0 community** — Vercel-hosted; watch the v0.dev showcase and `r/nextjs`.
- **Cursor community** — Discord + cursor.com/forum. Less direct-fit (Cursor users are more technical), but free checklist link can land.
- **Product Hunt** — AI tools filter, this week's launches. Mostly useful for prospecting (find pre-launch founders to DM), not for posting.
- **Founder communities** (MicroConf, Tiny Seed, On Deck, Indie Worldwide) — Tier 3 unless you're already a member. Cold join doesn't work here.

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
I'm testing LaunchLook — a $19 pre-launch checkup for apps built with Lovable, Bolt, Replit, v0, Cursor, etc. You send your live URL, and I send back the 7 most important things a real first user would notice: broken buttons, placeholder text, trust gaps, mobile issues, confusing flows, plus paste-ready prompts to fix them in your builder. AI does the first draft, I review every finding before it goes out. ($49 Full goes up to 25 findings + cross-user data check; $99 Pro goes up to 40 + integrations review + a 30-min Loom walkthrough.) Looking for a few early users this week and will refund it if it's not useful.
```

Use it when: you want one paragraph that explains the offer, signals "early / honest," and includes the risk reversal (refund).

---

### 3.2 — Long-form forum post (Reddit, Indie Hackers, big Discord channels)

Use in `r/vibecoding`, `r/SideProject`, `r/lovable`, `r/Replit`, `r/nextjs`, Indie Hackers, or any forum that allows multi-paragraph posts. Lead with the free offer; soft-mention the paid product only at the end (or not at all on Reddit).

```
Offering free 10-minute pre-launch checkups this week — Lovable / Bolt / Base44 / v0 / Cursor

I'm a technical writer (15 years) who's been spending time looking at vibe-coded apps that are almost-but-not-quite ready to share with real users. There's a pattern: the app works fine for the founder, but a stranger opening the link spots three or four things in the first minute that the founder stopped seeing weeks ago.

Reply with your public URL (staging links are fine — just not localhost) and I'll send back 2–3 specific things in plain English. No security jargon, no pentest, no "you need to refactor your auth layer." Just the stuff a first-time visitor will notice — dead buttons, placeholder text, broken trust pages, mobile layout problems.

What I'll look at (about 10 minutes per app):
- Does anything on the homepage scream "this is unfinished"?
- Do the main buttons / forms actually work?
- Does it look OK on a phone?
- Are /privacy, /terms, /contact real pages or 404s?

What I won't do: deep security, code review, anything that needs your repo.

I'll do as many as I can fit in this week. First come first served.

(If you want the long version with screenshots and copy-paste fix prompts for your builder, I do that as a paid service — but please don't pay for what I'm offering free here. Reply with your URL and let's start there.)
```

---

### 3.3 — Short Discord post (Lovable `#show-and-tell`, Bolt `#showcase`)

For chat-style channels where walls of text die. Keep it ≤ 5 lines.

```
Offering a free 10-min "would I send this link today?" pass on vibe-coded apps this week.

Drop your public URL (staging OK) and I'll reply with 2–3 specific things a first-time visitor would notice — dead buttons, placeholder copy, mobile layout, trust pages. Plain English, no security jargon.

Not a code review or pentest. Just URL only.
```

---

### 3.4 — Reply on someone else's "feedback wanted" thread (highest-converting variant)

Use in any "Show HN" / "Show-and-tell" / "Feedback wanted" thread. **Substitute your real findings before posting.**

```
Just clicked through {APP_NAME} like a first-time visitor (desktop + phone width). A few things I noticed:

1. {Specific thing #1 — what you saw, in plain English. Quote the exact button or text in quotes.}
2. {Specific thing #2}
3. {Specific thing #3 — keep it concrete and visual}

None of these are showstoppers, but they're the kind of stuff a stranger spots in the first 30 seconds. Happy to go deeper if useful — DM me your builder (Lovable / Bolt / v0 / etc.) and I can send copy-paste prompts to fix them.
```

**Substitution rules:**
- 3 findings max in the public reply.
- Always use the exact visible label in quotes (`"Get Started"`, `"Your Company Name"`).
- Never name the bug in technical terms — say *"the sign-up button doesn't go anywhere"* not *"the CTA's onClick handler is missing"*.

---

### 3.5 — "Free audit for testers" offer (non-Lovable platforms)

Use this when you're trying to validate the wedge on Bolt / v0 / Cursor / Base44 / Replit. The framing is "I'm testing my format on your builder this week."

```
Quick offer for {PLATFORM} builders — I'm doing free pre-launch checkups this week, specifically on {PLATFORM} apps so I can learn how your builder differs from Lovable.

What you get: I'll spend 10–15 minutes clicking through your live app like a first-time visitor (desktop + mobile). Reply with 2–3 specific things I'd want fixed before you share the link wider — placeholders, dead buttons, mobile layout, trust pages. Plain English, no security jargon.

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

If you want the full version — that's what LaunchLook does. $19 Starter is priority triage: the top 7 things you need to fix, ranked by impact, with copy-paste prompts you drop into {BUILDER}. $49 Full is a comprehensive audit: up to 25 findings across every category, plus a cross-user data check with two test accounts, plus a Quick Start Guide PDF for your users. $99 Pro adds an integrations review (Stripe / auth / email / analytics setup) and a 30-min Loom walkthrough where I walk you through the report on camera — for founders going to investor demos or paid traffic. AI drafts, I review every finding before delivery. No scanner, no GitHub access. Within 48h on Starter (usually 24), within 24h on Full and Pro (usually 12).

launchlook.app — and there's a free DIY checklist at launchlook.app/checklist if you want to keep going on your own. No pressure either way.
```

---

### 3.8 — Twitter / X single post (Variant #6)

Hook + offer + soft outro. No threads in the first one — earn the follow first.

```
Free this week: I'll do a 10-minute "would I send this link today?" pass on your vibe-coded app.

Reply or DM with your public URL. I'll send back 2–3 things a first-time visitor would actually notice — broken buttons, placeholder text, mobile layout, trust pages.

No security stuff, no code review, just the polish layer.
```

If it gets engagement, follow up days later with one of the findings as a quote-tweet: *"Did 6 of these this week — the #1 thing I caught was…"*

---

### 3.9 — LinkedIn build-in-public post

Use weekly. Tie to one finding, link the checklist (not the homepage). Always disclose you're the founder.

```
After clicking through a dozen pre-launch apps built with Lovable / Bolt / v0 this month, the #1 polish issue isn't broken code — it's leftover placeholders.

"Your Company Name" in the footer. "Hosted by …" in the metadata. "Get Started" button that goes to /undefined. The builder fills these in once and forgets them in three other places.

I made a 20-minute checklist of the most common ones — free, no email required: launchlook.app/checklist

(Disclosure: I run LaunchLook, a $19 pre-launch checkup for vibe-coded apps — with $49 and $99 deeper tiers. The checklist is the free DIY version of what I do manually.)
```

---

### 3.10 — Cold email (free sample outreach)

From [`templates/email/free-sample-outreach.txt`](../templates/email/free-sample-outreach.txt). Use after you've already done the free audit on someone's app — *send the report with the email*.

```
Subject: I noticed a few things about {APP_NAME} — no charge

Hi {NAME},

I'm Rob — I run LaunchLook, pre-launch checkups for vibe-coded web apps (Lovable, Bolt, v0, Cursor, and similar). Saw you launched {APP_NAME} on {PLATFORM} — looks promising.

I was testing my report format and ran it on your app as a sample. Here's what I found:

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
| 0:00–0:10 | Show their app in the browser. *"Hey [name], I clicked through [app name] like a first-time visitor."* |
| 0:10–0:35 | Show 2–3 specific issues (dead button, placeholder text, missing privacy, dev tools visible). No jargon. |
| 0:35–0:50 | *"I run LaunchLook — a pre-launch checkup for vibe-coded apps. Plain-English report + copy-paste fix prompts for your builder."* |
| 0:50–1:00 | CTA: *"Starter Package is $19 if you want the full list (top 7 fixes). Full $49 covers the cross-user data check; Pro $99 adds an integrations review and a 30-min Loom walkthrough. Link: launchlook.app"* |

**DM text to pair with the Loom:**

```
Hey [name] — I recorded a 60-sec walkthrough of [app] before you share it wider.
[LOOM LINK]

I flagged [issue 1] and [issue 2]. LaunchLook does a full pass starting at $19 (Starter — top 7 fixes) with paste-ready prompts for [Lovable/Bolt/etc]; $49 Full and $99 Pro go deeper if you're closer to launch.

Free checklist (~20 min): launchlook.app/checklist

No pressure — launchlook.app if useful.
```

**Loom rules:**
- Never use the word "security" as the lead. Use polish / placeholders / sharing risks.
- Never say "audit." Use "checkup" or "second pair of eyes."
- Personalize the first line with something specific you saw.

---

### 3.12 — Direct DM to a founder who just launched

Short, specific, no link in the first message.

```
Hey {NAME} — saw you just shipped {APP_NAME} on {PLATFORM}. Congrats.

I do quick pre-launch checkups for vibe-coded apps (no code access, just the live URL). I clicked through yours for a minute and noticed {ONE_SPECIFIC_THING}. Happy to send a quick free pass with 2–3 more if that's useful — just say the word.
```

If they reply "sure," send the free findings via DM. Then use **Variant #3.7 (soft pitch)** 24 hours after they've read it.

---

## 4. Tracking & measurement

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
  - **8+ paying customers?** Wedge is real. Begin light automation. Consider raising entry tier from $19 to $24, or push more buyers up to $49 / $99.
  - **3–7 paying customers?** Wedge is unclear. Iterate the pitch. Run another 30 outreach attempts.
  - **0–2 paying customers?** The pitch, audience, or product is wrong. Don't build more. Investigate the funnel.

---

## 5. Common objections & responses

Real ones surfaced in the Lovable Discord research thread and review feedback.

| Objection | Response |
|-----------|----------|
| *"Isn't this just an AI scanner? I can use Claude / MCP / VibeDoctor."* | "Those help builders test from the inside. LaunchLook checks what a **cold visitor** sees in the first 30 seconds — placeholders, dead CTAs, dev tools left on prod, broken trust pages. AI scanners are noisy and speak in `SEC-001` jargon; I send you 5–7 things that actually matter, in plain English, with paste-ready fix prompts." |
| *"I already know my app has issues — I don't need someone to tell me."* | "Probably true for the bugs you already see. The point is the ones you **stopped seeing** weeks ago — every founder has them. If you want, send the URL and I'll do a free 10-min pass; if it's all stuff you already knew, no harm done." |
| *"$19 is too cheap to be any good. / $19 is too expensive for something automated."* | "It's a manual human pass with AI doing the first draft, not a scanner — that's why it's $19 instead of free. And $19 entry instead of $200 because I'm just one human, no team, and I'd rather you buy Starter now and Full ($49) or Pro ($99) closer to launch than buy a single $200 audit and never come back." |
| *"Will this catch the scary security stuff?"* | "Not deep security (no pentest, no code review). I do catch obvious visible risks though — dev bypasses, exposed test controls, broken auth screens, and (Full Package only) one user seeing another user's data via cross-account checks." |
| *"Why should I trust you?"* | "Two ways: read the [free checklist](https://launchlook.app/checklist) — that's the DIY version of what I do. Or read the [sample report](https://launchlook.app/sample) and decide if the output is worth $19. And there's a 7-day full refund if it isn't." |
| *"Do I need to give you my GitHub / repo access?"* | "Never. Just the live URL. If your Full Package run needs to check cross-user data, you give me two temporary test accounts via the intake form. No code, no repo, no admin." |
| *"My app is built with v0 / Cursor / Base44, not Lovable. Do you do those?"* | "Yes. The fix prompts are tailored per builder — Lovable, Bolt, v0, Cursor, Base44, Replit, and a generic one for everything else. The findings are the same; the prompt syntax differs." |
| *"Will the report tell me anything I can't get for free?"* | "Free checklist gets you the DIY pass. What you can't get for free: a curated, ranked list written in plain English with paste-ready fix prompts — top 7 things on Starter ($19, priority triage), up to 25 on Full ($49, comprehensive audit), up to 40 on Pro ($99, deep audit). Full and Pro add a cross-user data check and a one-page Quick Start Guide PDF you can hand to your users. Pro additionally reviews your operational integrations (Stripe / auth / email / analytics) and includes a 30-minute Loom walkthrough where I go through the report on camera. No competitor includes that combination." |
| Silence / no reply after 5 days | Don't follow up. Log the no-response. That's data. |

---

## 6. Posting rules & etiquette cheat sheet

### Always

- ✅ **Personalize the first line.** Mention something specific you saw or something the prospect said.
- ✅ **Vary the wording per community.** Same offer; different framing per channel.
- ✅ **Engage in threads before posting your own.** 3 helpful comments → then 1 post.
- ✅ **Lead with real free value.** A 10-min free pass or the checklist link, never the pricing page.
- ✅ **Disclose your role honestly.** "I run LaunchLook" — never "a friend of mine runs..."
- ✅ **Reply within 2 hours** to anyone who drops a URL.
- ✅ **Use the exact visible label in quotes** when describing a finding (`"Get Started"`, not "the CTA").

### Never

| Don't | Why |
|-------|-----|
| Post the same copy in 5 places | Looks spammy. Mods talk. You get flagged. |
| Say "security audit" / "pentest" / "vulnerability scan" | Different product, you can't deliver it, you'll get flagged in security-aware subs |
| Say "AI-powered" | You're explicitly *not* — that's the selling point |
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

## 8. Quick reference

| Item | Value |
|------|-------|
| Primary goal | 30 messages → 3 paying ($19+) strangers |
| Site to share warm | https://launchlook.app/checklist (free), then https://launchlook.app |
| Sample report (for skeptics) | https://launchlook.app/sample |
| Support email | hello@launchlook.app |
| #1 channel | Lovable Discord `#show-and-tell` |
| #1 variant | #3.4 (reply with 3 specific findings) |
| Forbidden words | "security audit," "pentest," "AI scanner," "Notion report" |
| Approved words | "checkup," "second pair of eyes," "polish layer," "what a first-time visitor would notice" |
| Loom day | Monday (3/week) |
| LinkedIn day | Wednesday (1/week) |
| Quote-ask day | Friday |
| Outreach tracker | Notion DB (schema: `templates/notion/outreach-db.csv`) |
| Customer tracker | `python scripts/customers_track.py stats` |
| Cadence rules | Same day reply → +1 day free finding → +2 days soft pitch → +5 days drop |

---

*This is the canonical outreach playbook. When variants get updated in `templates/forum-posts.md`, sync them back into Section 3 here so this stays your single reference.*
