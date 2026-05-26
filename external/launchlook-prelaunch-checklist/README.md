# The Pre-Launch Checkup for Vibe-Coded Apps

**Try LaunchLook first:** [grab 3 free findings](https://launchlook.app/#hero) on your live URL — a real person reads your app and emails you the top 3 issues within 24 hours. No credit card.

This repo is the **community DIY extended checklist**: extra items, optional technical checks, and room to contribute. Same spirit as the LaunchLook checkup: what users notice before strangers show up.

Maintained by [LaunchLook](https://launchlook.app). Free to copy, fork, share.

The polished, in-app comprehensive checklist on launchlook.app is included with the Scale Up ($49) and Pro ($99) packages. This GitHub list is the public DIY companion.

---

## How to use this checklist

1. (Recommended) Drop your URL on [launchlook.app](https://launchlook.app/#hero) for 3 free findings from a real person.
2. Open your app in a normal browser (not the platform preview).
3. For each item below: mark pass, issue, or unsure.
4. Issues become your fix list. Unsure items are worth a paid second opinion.

This list focuses on what your *users* will notice, not deep security. For security scanning, [VAS](https://vibeappscanner.com) and [VibeEval](https://vibe-eval.com) are good complements.

---

## Extended: First impressions

- [ ] Homepage loads in under 3 seconds on a normal connection
- [ ] The small icon in the browser tab is custom (not the platform default)
- [ ] The hero headline tells a visitor what the app does within 5 seconds
- [ ] No lorem ipsum, bracket placeholders, or visible TODO notes
- [ ] No "Your Company Name" or "Acme Inc" placeholder text
- [ ] Your product name appears in the header/logo, not the platform default
- [ ] Default Lovable / Bolt / Base44 starter copy has been replaced
- [ ] The first call-to-action is clear about what happens when clicked

## Extended: Trust pages

- [ ] `/privacy` returns a real privacy policy page
- [ ] `/terms` returns Terms of Service
- [ ] A visible way to contact you (email, form, or contact page)
- [ ] Support email is real (not `support@example.com`)
- [ ] If you process payments, refund policy is stated somewhere
- [ ] If you collect emails, unsubscribe path exists
- [ ] Footer links to privacy/terms work (no 404)

## Extended: Functionality

- [ ] Every visible button does what its label suggests
- [ ] Internal links go somewhere that exists
- [ ] Signup creates an account; confirmation email arrives
- [ ] Login, logout, and password reset work
- [ ] Main workflow works end-to-end
- [ ] Test payment completes; success and cancel pages load sensibly

## Extended: Empty and error states

- [ ] New users see guidance on first visit (not a blank void)
- [ ] Empty lists show a helpful message and next step
- [ ] Form submit shows clear success or failure
- [ ] Offline or bad connection shows a message (try airplane mode briefly)
- [ ] Bad email/password inputs show helpful errors
- [ ] Custom "page not found" instead of a generic error

## Extended: Mobile

- [ ] Acceptable on a phone-sized screen (~375px wide)
- [ ] No horizontal scrolling
- [ ] Body text readable without zooming (roughly 16px or larger)
- [ ] Tap targets feel comfortable (not tiny buttons)
- [ ] Main workflow works on mobile, not only desktop

## Extended: Sharing and discovery

- [ ] Link preview in Slack/Twitter/LinkedIn looks intentional (title, description, image)
- [ ] Browser tab titles include your app name on key pages

## Extended: Permissions (two test accounts)

- [ ] User A cannot see User B's private data
- [ ] Signed-out visitors cannot open dashboard/settings and see real content
- [ ] Non-admin accounts cannot access admin-only areas

## Optional: Technical checks (developers or LaunchLook Scale Up / Pro)

Skip this block if you're not technical — or hire help.

- [ ] Link preview tags configured (Open Graph / social image)
- [ ] No obvious errors in browser developer tools on key pages
- [ ] Large images aren't slowing the first load
- [ ] Sensitive apps: expert review of database access rules (not covered by this checklist)

## Extended: Brand consistency

- [ ] One consistent word for your audience (customer vs user vs client — pick one)
- [ ] Button capitalization is consistent
- [ ] Product name spelled the same everywhere
- [ ] Support email matches everywhere it appears
- [ ] Visual style feels consistent page to page

## Gut check

- [ ] You'd be proud if a friend visited today
- [ ] You'd be okay if someone screenshotted the dashboard publicly
- [ ] You know the worst headline a critic could write — and you're fixing it

---

## What to do with the results

- **Fix before sharing:** data leaks, broken signup, missing privacy/terms, placeholders, dev tools on the live URL.
- **Fix soon:** mobile issues, weak previews, confusing empty states.
- **More than ~10 serious issues?** Slow down promotion until the top items are fixed.

---

## Want help running this?

Drop your URL on [launchlook.app](https://launchlook.app/#hero) and a real person will email you 3 free findings within 24 hours — no credit card.

For the full prioritized pass with paste-ready fix prompts:

- **Starter $19** — the 10 most important findings, ranked, with fix prompts, within 48h (usually 24)
- **Scale Up $49** — up to 30 findings + cross-user data check + Quick Start Guide + the polished comprehensive checklist as a token-gated companion, within 24h (usually 12)
- **Pro $99** — up to 40 findings + integrations review + Loom walkthrough + handoff doc + comprehensive checklist, within 24h (usually 12)

---

## Contributing

Found something this checklist missed? Open a PR or issue — especially platform-specific quirks (Lovable, Bolt, v0, Cursor).

## License

[CC BY 4.0](LICENSE). Attribution appreciated but not required.
