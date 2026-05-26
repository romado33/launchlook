# Forum posts — ready to paste

Six variants for vibe-coding communities. Lead with the free offer; mention the paid product only at the end (or not at all in post #1). See [`SHARE-AND-REVIEWS.md`](../docs/SHARE-AND-REVIEWS.md) for cadence.

**Rules:**
- Never lead with "I built a thing."
- Personalize the first line whenever the platform allows it.
- Use "checkup" / "second pair of eyes" — never "audit" or "security."
- One soft mention of LaunchLook, max, and only at the end.

---

## 1. Long-form forum post (Reddit, Indie Hackers, big Discord channels)

Use this in r/vibecoding, r/SideProject, r/lovable, r/Replit, r/nextjs, Indie Hackers, or any forum that allows multi-paragraph posts.

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

## 2. Short Discord version (Lovable #show-and-tell, Bolt #showcase, etc.)

For chat-style forums where walls of text die. Keep it ≤ 5 lines.

```
Offering a free 10-min "would I send this link today?" pass on vibe-coded apps this week.

Drop your public URL (staging OK) and I'll reply with 2–3 specific things a first-time visitor would notice — dead buttons, placeholder copy, mobile layout, trust pages. Plain English, no security jargon.

Not a code review or pentest. Just URL only.
```

---

## 3. Reply when someone shares their app and asks for feedback

Use this in any "Show HN" / "Show-and-tell" / "Feedback wanted" thread.

```
Just clicked through {APP_NAME} like a first-time visitor (desktop + phone width). A few things I noticed:

1. {Specific thing #1 — what you saw, in plain English. Quote the exact button or text in quotes.}
2. {Specific thing #2}
3. {Specific thing #3 — keep it concrete and visual}

None of these are showstoppers, but they're the kind of stuff a stranger spots in the first 30 seconds. Happy to go deeper if useful — DM me your builder (Lovable / Bolt / v0 / etc.) and I can send copy-paste prompts to fix them.
```

**Substitution rules:**
- 3 findings max in the public reply
- Always use the exact visible label in quotes (`"Get Started"`, `"Your Company Name"`)
- Never name the bug as a technical term in public — say "the sign-up button doesn't go anywhere" not "the CTA's onClick handler is missing"

---

## 4. Pure value post (no offer — for top-of-funnel awareness)

Post once a week. Picks one finding from your library, shows the pattern, no link.

```
The most common thing I see on Lovable / Bolt apps that are about to launch:

The footer still says "Your Company Name" or "© 2024 Your Brand Inc."

Founders stop seeing it after week one. Strangers see it in three seconds and assume the app isn't finished. It signals "this is a prototype" even when the app underneath is fine.

The five-second fix: Ctrl+F your homepage source for "your company" — if it's there, swap it. Then check the footer, the page title, and the meta description tags. The builder usually fills the placeholder in one place and leaves it in three others.
```

Rotate the finding each week. Pull from `findings_library/findings.json` — FL-001, FL-006, FL-008, FL-020, FL-035 all make good single-post stories.

---

## 5. Soft pitch — only after you've delivered a free finding

Send by DM (never in the public thread). Wait until the founder has actually read and replied to your free notes.

```
Glad the {SPECIFIC_THING} catch was useful.

If you want the full version — ranked findings with screenshots, the fixes that actually matter, and copy-paste prompts you drop into {BUILDER} — that's what LaunchLook does ($19 Starter, $49 Scale Up, $99 Pro). Founder-reviewed, no scanner, no GitHub access. Within 48 hours, usually 24.

launchlook.app — and there's a free DIY checklist at launchlook.app/checklist if you want to keep going on your own. No pressure either way.
```

---

## 6. Twitter / X (single post)

Hook + offer + soft outro. No threads in the first one — earn the follow first.

```
Free this week: I'll do a 10-minute "would I send this link today?" pass on your vibe-coded app.

Reply or DM with your public URL. I'll send back 2–3 things a first-time visitor would actually notice — broken buttons, placeholder text, mobile layout, trust pages.

No security stuff, no code review, just the polish layer.
```

If it gets engagement, follow up with one of the findings as a quote-tweet a few days later: *"Did 6 of these this week — the #1 thing I caught was…"*

---

## What to do *after* posting

| Day | Action |
|-----|--------|
| Same day | Reply within 2 hours to every URL someone drops |
| +1 day | Send the free finding (DM or reply, depending on platform) |
| +2 days | If they said "this is useful," send variant #5 (soft pitch) |
| +5 days | If silence, don't follow up. Log the no-response in your tracker — that's data |

Track every interaction in `scripts/customers_track.py` or your spreadsheet. Even the silences.

---

## What never to say in forums

| Don't | Why |
|-------|-----|
| "Security audit" / "pentest" / "vulnerability scan" | Different product, you can't deliver it, and you'll get flagged |
| "AI-powered" | You're explicitly *not* — that's a selling point |
| "Notion report" | Confuses non-Notion users; say "shareable report" |
| "I built LaunchLook because…" | This makes the post about you. Make it about them. |
| Pricing in the first line | Lead with help, not a price tag |
| Linking launchlook.app in post #1 on Reddit | Half of subreddits auto-flag self-links; comments are safer |

---

## Tracking what works

Add a column to your customers tracker (or a simple notes file) with:
- Platform (Reddit / Discord / IH / Twitter)
- Variant used (1–6)
- URLs received
- Replies → free findings sent → DMs → conversions

After 4 weeks, drop the variants that produced zero replies. Keep the ones that did.
