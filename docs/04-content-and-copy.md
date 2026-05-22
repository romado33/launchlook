# LaunchLook — Content and Copy

All writing artifacts. Use this verbatim unless explicitly approved to change by Rob.

## Landing page copy

### Hero section

**Eyebrow**: LaunchLook

**Headline**:
One last look before you launch.

**Subheadline (supporting)**:
A friendly pre-launch checkup for your vibe-coded app.

**Body**:
Send us your app's URL. We'll spot what your users will notice, write you a fix list you can paste into Lovable, and draft a one-page guide your users can actually read.

**CTAs**:
- Primary button: `Get my checkup — $7`
- Secondary button: `See a sample report`

### What we check section

**Section heading**: What we check

Four columns:

**Polish problems**
Broken buttons, broken links, mobile layout breaks, missing trust pages. The stuff your users will notice in the first 30 seconds.

**Forgotten placeholders**
"Your Company Name" still in the footer. Lorem ipsum on the About page. The little leftovers from your AI builder that signal "unfinished."

**Sharing risks**
Can users see each other's data? Are protected pages actually protected? We check with two real test accounts.

**Quick Start Guide** *(Launch Pack and up)*
A one-page guide your users can actually read. Written in plain language, formatted for your app, ready to embed.

### Pricing section

**Section heading**: One scan. Three depths.

**Tier 1 — Quick Checkup ($7)**
- 5-7 findings
- Mobile + desktop check
- Plain-language explanations
- Copy-paste fix prompts
- 24-hour turnaround
- CTA: `Get my checkup — $7`

**Tier 2 — Launch Pack ($29)** *(most popular)*
- Everything in Quick Checkup, plus:
- Full findings (10-15)
- Cross-user data check (with two test accounts)
- AI-generated Quick Start Guide for your users
- 12-hour turnaround
- Shareable report link
- CTA: `Get the Launch Pack — $29`

**Tier 3 — Launch Pack + Polish ($59)**
- Everything in Launch Pack, plus:
- Follow-up verification scan after you apply fixes
- 7-day post-launch check-in
- Quick Start Guide touchups based on your feedback
- CTA: `Get Polish — $59`

### Why us section

**Section heading**: We're not a security scanner.

There are good security scanners out there. We complement them.

LaunchLook focuses on the stuff your users will actually notice — broken UI, leftover placeholders, missing pages, and the small inconsistencies that make an app feel unfinished. We also write you a one-page Quick Start Guide your users can actually read (in the Launch Pack and up).

If you want a deep security audit, we recommend [VAS](https://vibeappscanner.com). We focus on what visitors will see, not what hackers will probe.

### FAQ section

**Q: How long does the checkup take?**
A: Quick Checkup is 24 hours. Launch Pack is 12 hours. Launch Pack + Polish runs the same with an additional 48 hours for the follow-up scan after you apply fixes.

**Q: What do you need from me?**
A: Your app's URL, a one-line description of what it does, and (for Launch Pack and up) two test accounts so we can check if users can see each other's data.

**Q: Is this safe to run on a live app?**
A: Yes. We only read your app — we never submit forms, click destructive buttons, or modify any data. Think of us as a careful visitor.

**Q: I'm not technical. Will I understand the report?**
A: That's the whole point. Every finding is explained in plain language. Every fix comes with a copy-paste prompt you can drop into Lovable, Bolt, Base44, or Replit.

**Q: What if my app isn't built with one of those tools?**
A: We work with any web app. The fix prompts are designed for AI builders, but the findings themselves apply to any app.

**Q: Do you store my app's data?**
A: We keep screenshots and notes from the audit for 30 days, then delete them. We don't store any user data from your app beyond what appears in screenshots.

**Q: Can I get a refund?**
A: If you're not happy with the report, email us within 7 days. We'll refund you, no questions asked.

**Q: Can I run this on a private/staging URL?**
A: Yes, if it's accessible from the internet. Local URLs (localhost) won't work, but staging URLs on services like Vercel, Netlify, or Lovable's preview URLs do.

### Footer

- Email: hello@launchlook.app
- Free checklist: /checklist
- Privacy: /privacy
- Terms: /terms
- GitHub: link to launchlook-prelaunch-checklist repo

---

## Intake form fields

**Page heading**: Tell us about your app

1. **What's your name?** (text, required)
2. **Email** (email, required — matches Stripe purchase email)
3. **App URL** (text, required, validated as URL)
4. **What does your app do?** (1-sentence text, required, 200 char max)
5. **Who's your main user?** (1-2 sentences text, required)
6. **What's the main thing they do in your app?** (1-2 sentences, required)
7. **Which platform built it?** (radio: Lovable / Bolt / Base44 / Replit / v0 / Other)
8. **Can we use test accounts? (Launch Pack and up)** (yes / no — if yes, conditional fields below)
9. **Test account 1 email + password** (only if "yes" above, conditional)
10. **Test account 2 email + password** (only if "yes" above, conditional)
11. **Your support email** (for the Quick Start Guide, Launch Pack and up, conditional on tier)
12. **Anything specific to check?** (textarea, optional)
13. **How anxious are you about launching, 1-10?** (number 1-10, optional) *Tone-matching signal for the report.*

---

## Cold outreach Loom script

This is a template. Adapt to each prospect. Keep under 90 seconds.

```
Hey [name], I'm Rob — I run a small thing called LaunchLook that does pre-launch checkups for vibe-coded apps.

I saw you launched [app name] on [Lovable / Bolt / etc.] — looks really cool. I poked at it for about 10 minutes and wanted to send you a couple of things I noticed that you might want to fix before sharing it more widely.

[Walk through 2-3 specific findings, with screen-share. Be friendly. Specifically point to the actual broken/placeholder thing.]

So those are the three things I'd flag. There's probably a few more small ones — if you want, I do a full checkup for $7 with a fix list you can paste into [their platform]. Link in the message I sent.

Either way, good luck with the launch — looks like a solid start.
```

Notes:
- Always say something genuinely positive about the app.
- Never imply the founder is incompetent.
- Never use the word "security" — that's not your wedge.
- End with "either way, good luck" — removes pressure.

---

## Email templates

### Welcome / receipt email (auto-sent on Stripe purchase)

**Subject**: Got it — checkup for [app name] coming in [N] hours

```
Hi [name],

Thanks for trusting LaunchLook with [app name]. I'll have your checkup ready in [24 hours / 12 hours / 12 hours] from now.

To get started, please fill out the short intake form here:
[INTAKE FORM LINK]

It takes about 3 minutes. The more context you give me, the more useful the report will be.

Talk soon,
Rob
hello@launchlook.app
```

### Delivery email

**Subject**: Your LaunchLook checkup is ready

```
Hi [name],

Your checkup for [app name] is ready. Here's the link:

[NOTION REPORT LINK]

A few notes:
- The findings are ranked by severity. Start at the top.
- Every finding has a copy-paste fix prompt for [their platform]. Just paste them in and let your builder fix it.
- If you're at the Launch Pack tier or above, the Quick Start Guide is in the second half of the report.
- The report is yours to share. Feel free to forward the link to teammates or freelancers.

If anything isn't clear, just reply to this email. I'll respond within a few hours.

Good luck with the launch.

— Rob
```

### Day-3 follow-up email (auto-sent)

**Subject**: Quick question about your checkup

```
Hi [name],

Hope the checkup was useful. Two quick things:

1. If you've had a chance to apply any of the fixes, I'd love to know how it went. Even one-word answers help me make these reports better.

2. If you know anyone else building with Lovable, Bolt, or similar tools who's about to launch — feel free to forward them your referral code: [REFERRAL_CODE]. They get $5 off their checkup, and so do you on your next one.

Either way, thanks for trying this out.

— Rob
```

### Day-7 post-launch check-in (Launch Pack + Polish only)

**Subject**: How did the launch go?

```
Hi [name],

How did the launch of [app name] go? I'd love to hear what happened.

If you got user feedback you want me to look at, or if anything unexpected came up, just reply. I'll spot-check whatever's most useful to you (this is included in your Polish tier).

— Rob
```

---

## Customer tracker (Notion database schema)

| Column | Type | Notes |
|--------|------|-------|
| Name | Title | Customer first name |
| Email | Email | Matches Stripe purchase email |
| App URL | URL | The app being checked |
| Tier | Select | Quick Checkup / Launch Pack / Polish |
| Payment Date | Date | When Stripe purchase landed |
| Intake Received | Checkbox | Whether they filled the form |
| Delivery Due | Date | Payment date + tier turnaround |
| Delivered | Checkbox | When report sent |
| Follow-up Sent | Checkbox | Day-3 follow-up automation |
| Feedback Received | Text | Customer's response |
| Useful Rating | Select | Very useful / Useful / Mixed / Not useful / No response |
| Referral Code | Text | Their unique code |
| Referrals | Number | How many times their code was used |
| Notes | Text | Anything else |

---

## Outreach tracker (Notion database schema)

| Column | Type | Notes |
|--------|------|-------|
| Prospect | Title | Founder name or handle |
| App URL | URL | Their app |
| Channel | Select | Lovable Discord / Bolt Discord / Twitter / Reddit / Product Hunt / Other |
| Date Sent | Date | When Loom or DM was sent |
| Loom URL | URL | The Loom recording (if applicable) |
| Opened | Checkbox | Did they open it? (Loom shows this) |
| Replied | Checkbox | Any response? |
| Paid | Checkbox | Converted to customer |
| Notes | Text | Any context |

---

## Free public checklist (full text)

> A free, comprehensive checklist for anyone about to share their Lovable / Bolt / Base44 / Replit app with real users.
>
> Go through this list before you launch. Fix what you can. The stuff you can't fix yourself, hire help for — but don't ship without checking.
>
> *Maintained by [LaunchLook](https://launchlook.app). Free to copy, fork, share.*

### How to use this checklist

1. Open your app in a normal browser (not the platform's preview).
2. Work through each section in order.
3. For each item: mark ✅ Pass, ⚠️ Issue, or ❓ Unsure.
4. The "Issue" items are your fix list. The "Unsure" items need a second opinion.

This list focuses on what your *users* will notice, not deep security. For deep security scans, tools like [VAS](https://vibeappscanner.com) and [VibeEval](https://vibe-eval.com) are good complements to this.

### Section 1: First impressions (5 minutes)

- [ ] Homepage loads in under 3 seconds on a normal connection
- [ ] The page title in the browser tab is meaningful (not "My App" or platform default)
- [ ] The favicon is custom, not the platform default
- [ ] The hero headline tells a visitor what the app actually does within 5 seconds of reading
- [ ] There are no `Lorem ipsum`, `[insert text here]`, or `TODO` comments visible
- [ ] There's no "Your Company Name" or "Acme Inc" placeholder text anywhere
- [ ] Your actual product name appears in the header/logo, not the platform's default
- [ ] Any default Lovable / Bolt / Base44 copy has been replaced with your own
- [ ] The first call-to-action button is clear about what happens when clicked

### Section 2: Trust pages (3 minutes)

- [ ] `/privacy` returns a real privacy policy page
- [ ] `/terms` returns Terms of Service
- [ ] There's a visible way to contact you (email, form, or `/contact` page)
- [ ] Your support email is a real address you check (not `support@example.com`)
- [ ] If you process payments, you have a refund policy somewhere
- [ ] If you collect emails, you have a clear unsubscribe path
- [ ] Footer links to privacy/terms work and don't 404

### Section 3: Functionality (15 minutes)

- [ ] Every visible button does what its label suggests when clicked
- [ ] Every internal link goes somewhere that exists (no 404s)
- [ ] The signup form actually creates an account
- [ ] The signup confirmation email actually arrives (check spam too)
- [ ] Email links in the confirmation actually work
- [ ] You can log in successfully after signing up
- [ ] You can log out and the session actually ends
- [ ] You can reset your password if you forget it
- [ ] The main user workflow (the thing your app is for) actually works end-to-end
- [ ] Any payment flow you have completes successfully with a test card
- [ ] Stripe / payment provider success page actually loads after payment
- [ ] Stripe / payment provider cancel page actually loads if you cancel

### Section 4: Empty and error states (10 minutes)

- [ ] When a brand-new user signs up, the dashboard shows clear guidance about what to do
- [ ] When a user has zero items / posts / tasks / whatever, there's a helpful empty state with a clear CTA
- [ ] When you submit a form, you get clear feedback about success or failure
- [ ] When the network fails (try airplane mode), the app shows a clear error message instead of silently breaking
- [ ] Invalid inputs (wrong email format, weak password) show clear validation messages
- [ ] You can't accidentally submit the same form twice with a double-click
- [ ] Trying to access a URL that doesn't exist shows a custom 404, not a broken page

### Section 5: Mobile (10 minutes)

- [ ] The site looks acceptable on a 375px wide viewport (iPhone SE)
- [ ] There's no horizontal scrolling on mobile
- [ ] Body text is at least 16px and readable without zooming
- [ ] Buttons are at least 44×44 pixels (easy to tap)
- [ ] Forms are usable on mobile — fields don't get cut off, keyboard doesn't cover the submit button
- [ ] Images aren't oversized (causing slow loads)
- [ ] The main user workflow can be completed on mobile, not just desktop

### Section 6: Sharing and discovery (5 minutes)

- [ ] When you paste your URL into Twitter/X, LinkedIn, or Slack, the preview card looks intentional (right title, description, image)
- [ ] Open Graph meta tags are set (`og:title`, `og:description`, `og:image`)
- [ ] Each page has a meaningful `<title>` tag with your app name
- [ ] The meta description describes your actual app, not the platform default

### Section 7: Permissions (10 minutes, requires two test accounts)

- [ ] Sign up two test accounts. Sign in as User A. Note what you can see.
- [ ] Sign in as User B. Verify you CAN'T see any of User A's data.
- [ ] Specifically: User A's email, name, content, or any other identifiers should never appear on User B's screen
- [ ] If you have admin features, verify a non-admin account can't access `/admin` routes
- [ ] Log out completely. Try to visit `/dashboard`, `/settings`, `/admin` directly. You should be redirected to login, not see data.
- [ ] If you have API endpoints, verify they require authentication
- [ ] If you store sensitive data (medical, financial, personal), have an expert verify your row-level security policies

### Section 8: Performance (5 minutes)

- [ ] Open Chrome DevTools → Lighthouse → run a Performance audit. Aim for a Performance score above 70.
- [ ] No single image is over 1MB
- [ ] The page has no console errors when loaded
- [ ] The Network tab shows no failed requests (4xx or 5xx status codes)
- [ ] First Contentful Paint is under 1.8 seconds

### Section 9: Brand consistency (5 minutes)

- [ ] You use one term consistently for your users (pick: "customer," "client," "user," "member," etc. — don't mix)
- [ ] Button capitalization is consistent (all sentence case OR all title case, not mixed)
- [ ] Your product name is spelled identically everywhere
- [ ] Your support email is the same address in every place it appears
- [ ] The visual style (colors, fonts, spacing) feels consistent page to page

### Section 10: The "would I share this?" gut check (3 minutes)

- [ ] If a friend visited your homepage, would you be proud or embarrassed?
- [ ] If someone screenshotted your dashboard and posted it on Twitter, would you be okay with that?
- [ ] If a journalist reviewed your app today, what's the worst thing they'd say?
- [ ] If a competitor saw it, would they think you knew what you were doing?

If any of those answers are bad, fix the underlying issues before launching.

### What to do with the results

- Count your ⚠️ Issues. If you have more than 10, don't launch yet.
- Critical issues (data leaks, broken signup, missing privacy policy) must be fixed before launch.
- High-severity issues (placeholders visible, broken buttons, missing trust pages) should be fixed within 24 hours of launching if not before.
- Medium and low issues can be fixed in the first 2 weeks.

### Want help running this?

This checklist is free to use yourself. If you'd rather have someone else run it for you and hand you back a fix list with copy-paste prompts for your AI builder, that's what [LaunchLook](https://launchlook.app) does. $7 for a Quick Checkup, $29 for a Launch Pack that includes a Quick Start Guide for your users.

### License

This checklist is free to use, copy, fork, and republish. Attribution appreciated but not required.

---

## Voice and tone reminders

When writing anything for LaunchLook, ask:

- Would a non-technical founder understand this immediately?
- Did I use any marketing words? (leverage, seamless, robust, cutting-edge, innovative, streamline — strike them)
- Am I in second person, active voice?
- Is the sentence under 20 words?
- Could this feel condescending? (Adjust if yes.)
- Did I reference the actual UI element by its visible label?

Words that are banned everywhere in product copy:
- leverage / leveraging
- seamless / seamlessly
- robust
- cutting-edge
- innovative / innovate
- streamline / streamlined
- powerful
- elevate
- empower
- unlock (as in "unlock potential")
- supercharge
- revolutionize
- transform (as a sales verb)
- best-in-class
- world-class
