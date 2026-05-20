# The Pre-Launch Checkup for Vibe-Coded Apps

A free, comprehensive checklist for anyone about to share their Lovable / Bolt / Base44 / Replit app with real users.

Go through this list before you launch. Fix what you can. The stuff you can't fix yourself, hire help for — but don't ship without checking.

Maintained by [Onceover](https://onceover.app). Free to copy, fork, share.

---

## How to use this checklist

1. Open your app in a normal browser (not the platform's preview).
2. Work through each section in order.
3. For each item: mark ✅ Pass, ⚠️ Issue, or ❓ Unsure.
4. The "Issue" items are your fix list. The "Unsure" items need a second opinion.

This list focuses on what your *users* will notice, not deep security. For deep security scans, tools like [VAS](https://vibeappscanner.com) and [VibeEval](https://vibe-eval.com) are good complements to this.

---

## Section 1: First impressions (5 minutes)

- [ ] Homepage loads in under 3 seconds on a normal connection
- [ ] The page title in the browser tab is meaningful (not "My App" or platform default)
- [ ] The favicon is custom, not the platform default
- [ ] The hero headline tells a visitor what the app actually does within 5 seconds of reading
- [ ] There are no `Lorem ipsum`, `[insert text here]`, or `TODO` comments visible
- [ ] There's no "Your Company Name" or "Acme Inc" placeholder text anywhere
- [ ] Your actual product name appears in the header/logo, not the platform's default
- [ ] Any default Lovable / Bolt / Base44 copy has been replaced with your own
- [ ] The first call-to-action button is clear about what happens when clicked

## Section 2: Trust pages (3 minutes)

- [ ] `/privacy` returns a real privacy policy page
- [ ] `/terms` returns Terms of Service
- [ ] There's a visible way to contact you (email, form, or `/contact` page)
- [ ] Your support email is a real address you check (not `support@example.com`)
- [ ] If you process payments, you have a refund policy somewhere
- [ ] If you collect emails, you have a clear unsubscribe path
- [ ] Footer links to privacy/terms work and don't 404

## Section 3: Functionality (15 minutes)

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

## Section 4: Empty and error states (10 minutes)

- [ ] When a brand-new user signs up, the dashboard shows clear guidance about what to do
- [ ] When a user has zero items / posts / tasks / whatever, there's a helpful empty state with a clear CTA
- [ ] When you submit a form, you get clear feedback about success or failure
- [ ] When the network fails (try airplane mode), the app shows a clear error message instead of silently breaking
- [ ] Invalid inputs (wrong email format, weak password) show clear validation messages
- [ ] You can't accidentally submit the same form twice with a double-click
- [ ] Trying to access a URL that doesn't exist shows a custom 404, not a broken page

## Section 5: Mobile (10 minutes)

- [ ] The site looks acceptable on a 375px wide viewport (iPhone SE)
- [ ] There's no horizontal scrolling on mobile
- [ ] Body text is at least 16px and readable without zooming
- [ ] Buttons are at least 44×44 pixels (easy to tap)
- [ ] Forms are usable on mobile — fields don't get cut off, keyboard doesn't cover the submit button
- [ ] Images aren't oversized (causing slow loads)
- [ ] The main user workflow can be completed on mobile, not just desktop

## Section 6: Sharing and discovery (5 minutes)

- [ ] When you paste your URL into Twitter/X, LinkedIn, or Slack, the preview card looks intentional (right title, description, image)
- [ ] Open Graph meta tags are set (`og:title`, `og:description`, `og:image`)
- [ ] Each page has a meaningful `<title>` tag with your app name
- [ ] The meta description describes your actual app, not the platform default

## Section 7: Permissions (10 minutes, requires two test accounts)

- [ ] Sign up two test accounts. Sign in as User A. Note what you can see.
- [ ] Sign in as User B. Verify you CAN'T see any of User A's data.
- [ ] Specifically: User A's email, name, content, or any other identifiers should never appear on User B's screen
- [ ] If you have admin features, verify a non-admin account can't access `/admin` routes
- [ ] Log out completely. Try to visit `/dashboard`, `/settings`, `/admin` directly. You should be redirected to login, not see data.
- [ ] If you have API endpoints, verify they require authentication
- [ ] If you store sensitive data (medical, financial, personal), have an expert verify your row-level security policies

## Section 8: Performance (5 minutes)

- [ ] Open Chrome DevTools → Lighthouse → run a Performance audit. Aim for a Performance score above 70.
- [ ] No single image is over 1MB
- [ ] The page has no console errors when loaded
- [ ] The Network tab shows no failed requests (4xx or 5xx status codes)
- [ ] First Contentful Paint is under 1.8 seconds

## Section 9: Brand consistency (5 minutes)

- [ ] You use one term consistently for your users (pick: "customer," "client," "user," "member," etc. — don't mix)
- [ ] Button capitalization is consistent (all sentence case OR all title case, not mixed)
- [ ] Your product name is spelled identically everywhere
- [ ] Your support email is the same address in every place it appears
- [ ] The visual style (colors, fonts, spacing) feels consistent page to page

## Section 10: The "would I share this?" gut check (3 minutes)

- [ ] If a friend visited your homepage, would you be proud or embarrassed?
- [ ] If someone screenshotted your dashboard and posted it on Twitter, would you be okay with that?
- [ ] If a journalist reviewed your app today, what's the worst thing they'd say?
- [ ] If a competitor saw it, would they think you knew what you were doing?

If any of those answers are bad, fix the underlying issues before launching.

---

## What to do with the results

- Count your ⚠️ Issues. If you have more than 10, don't launch yet.
- **Critical** issues (data leaks, broken signup, missing privacy policy) must be fixed before launch.
- **High-severity** issues (placeholders visible, broken buttons, missing trust pages) should be fixed within 24 hours of launching if not before.
- **Medium and low** issues can be fixed in the first 2 weeks.

---

## Want help running this?

This checklist is free to use yourself. If you'd rather have someone else run it for you and hand you back a fix list with copy-paste prompts for your AI builder, that's what [Onceover](https://onceover.app) does. $7 for a Quick Checkup, $29 for a Launch Pack that includes a Quick Start Guide for your users.

---

## Contributing

Found something this checklist missed? Open a PR or an issue. Real-world findings from real launches are exactly what makes this list better.

Especially welcome:
- Issues you ran into that aren't covered here
- Platform-specific quirks (Lovable / Bolt / Base44 / Replit / v0)
- Better wording for any of the existing items

## License

[CC BY 4.0](LICENSE). Free to use, copy, fork, and republish — attribution appreciated but not required.
