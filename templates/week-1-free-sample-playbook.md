# Week-1 free sample playbook

For your week-1 priority #4: "Audit 5 real apps, deliver one as a free sample."

The free sample is the most important test of the whole project. It tells you whether the wedge is real before you spend money or build anything else.

## The goal

Get **one real founder reaction** to the report format. Not a polite reaction. A genuine one — "this would have saved me from launching with a broken Stripe webhook" or "meh, I knew most of this already."

That single reaction tells you more than the strategy doc ever could.

## The 5 audits

Pick 5 apps from:

- Lovable Discord #show-and-tell (past 7 days)
- Bolt Discord #showcase
- Product Hunt this week (filter: AI tools)
- Reddit r/SideProject "new"

**Selection criteria:**

1. Live URL (not localhost / preview)
2. Founder is reachable (Twitter handle, Discord profile, contact email visible)
3. App looks like it's in pre-launch or just-launched phase (not a 6-month-old mature product)
4. NOT one of Lovable/Bolt's own showcase apps (those are too polished — you won't find much)
5. Variety: aim for 2 productivity tools, 1 marketplace-style, 1 social/community, 1 utility — gives you a representative sample of the audit work

Save URLs in your tracker spreadsheet before starting.

## The 30-minute audit (per app)

Use `templates/notion/report-quick-checkup.md` as the template. Duplicate it in Notion per audit. Fill in:

1. **Desktop pass** (5 min)
   - Load the homepage. Screenshot.
   - Click every visible button. Note what breaks.
   - Check `/privacy`, `/terms`, `/contact` URLs — note 404s.
   - Open DevTools → Console. Note errors.
   - Search visible text for placeholder patterns (see `findings_library/findings.json` placeholder regexes for the list).

2. **Mobile pass** (5 min)
   - DevTools → device toolbar → iPhone SE (375px)
   - Reload page. Screenshot.
   - Check for horizontal scroll, small text, tiny buttons.

3. **Signup pass** (10 min)
   - Sign up with `launchlooktest+{app_name}@gmail.com` (Gmail aliases work)
   - Wait for confirmation email. Note if it never arrives.
   - Log in. Screenshot dashboard.
   - Click every nav item. Note empty states.
   - Try to log out cleanly.

4. **Logged-out probe** (3 min)
   - In a new incognito window, try to visit `/dashboard`, `/admin`, `/settings`, `/account` directly
   - Note any that loaded data instead of redirecting to login

5. **Write up** (7 min)
   - 5–7 findings in the report
   - Each has: severity, visible label in quotes, plain-English why, fix prompt copy-pasted from `findings.json`
   - Substitute `{ACTUAL_NAME}`, `{ACTUAL_EMAIL}`, `{PAGE}` per finding
   - Add 1–2 new findings to the Findings Library if you spot something the seed 35 don't cover

Realistic time: **30–45 minutes** for the first audit, **20 minutes** by audit #5.

If you're at 60 minutes on audit #1, that's normal. If you're at 60 minutes on audit #5, the template is too heavy — strip it down.

## The free sample (pick 1 of 5)

After all 5 audits, pick the one whose founder seems most reachable AND whose report you're proudest of. Then:

1. Open `templates/email/free-sample-outreach.txt`
2. Substitute `{NAME}`, `{APP_NAME}`, `{PLATFORM}`, `{NOTION_REPORT_LINK}`
3. Send via:
   - Twitter DM (if their DMs are open)
   - Email (if their site shows a contact email)
   - Loom + DM (if you want to be especially personal — record a 60-second walkthrough of the top 3 findings)

## The three questions you actually want answered

Buried in the free-sample email, you ask three questions. These are the research questions. Pay attention to the answers more than the praise:

1. **"Was anything in here something you'd actually fix?"**
   - If yes → the audit findings are useful
   - If no → either you flagged trivial stuff OR they were going to fix it anyway → re-prioritize what counts as a "finding"

2. **"Was anything obvious or trivial?"**
   - This is the more important question. Vibe coders politely skip past trivial findings.
   - If they call out one as obvious, demote it in the Findings Library or remove it entirely.

3. **"Would you have paid $7 for it?"**
   - The actual signal. If yes (or even "yeah, probably"), the wedge is real.
   - If no, ask "what would have made it worth paying for?" Their answer is the v0.1 spec.

## How to handle each response

| Response | What to do |
|----------|------------|
| "Yes, would have paid" | Ask permission to use as a testimonial. Use them as case study #1. |
| "Maybe" or "Yes but only at $5" | The pitch is right but the price might be off. Note for the 60-day pricing review. |
| "No, but X was useful" | The wedge is partially right. Refocus the report around X. |
| "No, all of this is obvious" | The wedge is wrong for this audience. Try a different audience (less-experienced vibe coders, agencies, etc.). |
| Silence after 5 days | Don't follow up. Their non-response is also data. |

## What "success" looks like for the free sample

By Sunday evening:

- [ ] All 5 audits complete and in Notion
- [ ] Free sample sent to 1 founder
- [ ] Founder responded with at least one of the three questions answered
- [ ] You added at least 3 new findings to the Findings Library
- [ ] You wrote down at least 5 "things the future scanner should check" in the Crawler Wishlist
- [ ] You can answer: "did doing this work feel sustainable or already tedious?"

If the founder hasn't responded by Sunday, send the same free sample to a second founder Monday morning. You only need one real reaction.
