# Shareable Report Workflow

q22 ships a hosted public URL for every delivered audit. Customers
choose whether to make it visible. The page pairs with the q17 Verified
badge (which links to it once the customer opts in) and optionally
exposes the q18 Handoff Report download for Pro tier customers.

> **TL;DR.** Every audit gets a private URL at
> `launchlook.app/r/{slug}`. Default is private. Customer replies
> "share" to the delivery email; Rob runs one CLI to flip it public.
> No content of any kind reaches the public surface until that flip
> happens, and no customer-specific URL, email, or screenshot ever
> reaches the public surface even after.

## 1. URL pattern

```
launchlook.app/r/jane-sparkle-marketplace
launchlook.app/r/alex-bauer-studio
launchlook.app/r/mira-tessera-boards
```

The slug is the same one `scripts/generate_verified_badge.py` uses
(`first_name + app_name`, slugified). One slug per customer, identical
across the verify page, the badge filenames, and the shareable URL.

## 2. What ships at delivery time

When `scripts/deliver_report.py` runs for a customer, it now also
writes two files into the landing site:

```
landing/data/reports/{slug}.json    # data the public page reads
landing/r/{slug}.html               # per-customer HTML with baked-in OG tags
```

The HTML page has the social-share meta tags (Open Graph + Twitter
Card) baked in **at generation time** so Reddit, Twitter, and LinkedIn
preview correctly without waiting on client-side fetch (their scrapers
don't run JS). The body content itself is rendered client-side from
the JSON by `landing/assets/r.js`, which respects the `is_public` flag
in the JSON.

If the JSON already exists from a prior delivery, the publish state
(`is_public`, `handoff_report.shared`, `share_history`) is preserved so
re-running `deliver_report.py` doesn't silently flip a live audit back
to private.

A catch-all fallback page at `landing/r.html` reads `?slug=` from the
query string and is served by the `/r/:slug` rewrite in `vercel.json`
when no per-customer HTML exists.

## 3. The opt-in flow

By default, every delivered report is **private**. The customer opts
in by:

1. After delivery, the customer receives the report PDF + the URL
   `https://launchlook.app/r/{slug}` in the delivery email. The email
   line reads: "This page is private until you switch it on. Want to
   share publicly? Reply with 'share' and we'll make it public."
2. The customer replies "share" (or "unshare").
3. Rob runs:

   ```bash
   python scripts/share_report.py --slug jane-sparkle-marketplace --public
   python scripts/share_report.py --slug jane-sparkle-marketplace --private
   python scripts/share_report.py --slug jane-sparkle-marketplace --status
   ```

   The script flips `is_public` in the JSON, appends a row to
   `share_history`, and (when run inside the git repo) auto-commits the
   change so the deployed `launchlook.app` rebuilds on the next push.

   Pass `--no-commit` to skip the auto-commit. The JSON write still
   happens; the working tree is left dirty so an operator can review the
   diff before committing manually. Use this when smoke-testing the
   pipeline, piloting from a notebook, or batching several flips into a
   single commit. Default behavior (no flag) is unchanged from
   production: every flip auto-commits.

This is **explicit opt-in**, not opt-out, per
`docs/SIMPLICITY-GUARDRAILS.md` section 3 and section 5. We never
share a customer's URL or audit without their permission.

## 4. Privacy guarantees + sanitization rules

The JSON the public page reads goes through
`scripts/sanitize_for_public.py` before it's written. The sanitizer:

* Drops every `customer.*` field except `first_name`, `app_name`,
  `tier`, `builder`, `platform`. Email, `app_url`, `notion_row_id`,
  `internal_notes`, `last_name`, and `url_redacted` are all stripped.
* Drops every finding key except `title`, `severity`, `category`,
  `tag`, `what_we_saw`, `why_it_matters`, `fix_prompt`. So
  `screenshot_path`, `screenshot_caption`, `fingerprint`, internal
  notes — none ever reach the public file.
* Scrubs the customer's domain out of every kept text field. Both
  `https://customer-host` and bare `customer-host` get replaced with
  the phrase "your site".
* Strips obvious raw email addresses with the placeholder
  `[email redacted]`.
* Replaces common site paths in finding text with generic phrases.
  `/auth` becomes "the sign-in page"; `/privacy` becomes "the privacy
  page"; same for `/login`, `/signin`, `/admin`, `/checkout`,
  `/pricing`, `/terms`. (See `GENERIC_PATH_REPLACEMENTS` in
  `scripts/sanitize_for_public.py`.)
* Never copies any screenshot file to the public surface. Screenshots
  may contain real PII; they stay on disk in the customer's
  `output/reports/{slug}/` directory.

The unit tests in `tests/test_sanitize_for_public.py` enforce this
end-to-end. The integration test in `tests/test_share_report.py`
verifies the three committed example customers produce JSON + HTML
files with zero customer-URL leakage.

## 5. Pairing with the q17 Verified badge

Each public report page renders a `LaunchLook Verified` banner at the
top, derived from the same audit date and tier the report itself
carries. The banner reads:

> ✓ LaunchLook Verified — Starter audit completed May 26, 2026. Valid
> through June 25, 2026.

```
+----------------+      +-----------------+      +---------------------+
|  Embed badge   |  →   |  /verify?slug=  |  →   |  /r/{slug}          |
|  on site       |      |  signed JSON    |      |  public report page |
+----------------+      +-----------------+      +---------------------+
        |                                              ▲
        |        (visual / SEO loop on public flip)    |
        +----------------------------------------------+
```

The badge on the customer's site footer continues to link to
`/verify?slug=...`, which is the canonical verification endpoint. The
report page surfaces the same verification line so visitors who land
via the badge see the audit they're standing on top of, and visitors
who land via a Reddit / Twitter share see the verification claim
without having to click out.

When the report is private, the verification page still works
(`/verify?slug=...` is governed by the q17 badge JSON in
`landing/data/verified/{slug}.json`, not the q22 report JSON). The
private state of `/r/{slug}` only affects whether the report content
is rendered.

## 6. Handoff Report download (Pro tier only)

Pro tier customers get the Handoff Report bundled at delivery
(`docs/HANDOFF-REPORT-WORKFLOW.md`). They can choose, independently,
whether to expose the Handoff PDF on the public report page:

```bash
python scripts/share_report.py --slug mira-tessera-boards --share-handoff
python scripts/share_report.py --slug mira-tessera-boards --hide-handoff
```

When shared, the page renders a "Download the Handoff Report (PDF)"
button linking to `landing/data/handoff/{slug}.pdf`. Rob copies the
generated `output/reports/{slug}/handoff-report.pdf` into that
location at the time he flips `--share-handoff` on (one-time copy;
the file is small and the directory is committed). Starter / Scale Up
customers don't see this toggle unless they bought the $99 Handoff
add-on.

## 7. Daily flow (operator-facing)

```
1. Customer pays / replies to intake.
2. Rob runs the existing pipeline:
     python scripts/deliver_report.py --customer customers/<slug>.yaml
   This now also writes landing/r/{slug}.html + landing/data/reports/{slug}.json
   (default is_public: false).
3. Rob includes "Your report URL (private): https://launchlook.app/r/{slug}"
   in the delivery email. The email line includes the share/unshare invite.
4. Customer replies 'share' or 'unshare'. Rob runs:
     python scripts/share_report.py --slug {slug} --public
     # or --private
   The script auto-commits the JSON change. Push to deploy.
5. (Pro tier only.) Customer asks to share the Handoff Report:
     python scripts/share_report.py --slug {slug} --share-handoff
   Rob then copies the generated Handoff PDF into
   landing/data/handoff/{slug}.pdf and commits.
```

Per-customer styling is locked. We do not let customers customize the
page (no custom CSS, no logo swaps, no branding overrides). The page
is LaunchLook's marketing surface. See
`docs/SIMPLICITY-GUARDRAILS.md` section 2 and section 6 (no per-buyer
branding swaps, plain LaunchLook header / footer).

## 8. Social share metadata

The OG / Twitter Card meta tags are generated by
`scripts/deliver_report.py::_build_share_metadata` and baked into the
per-customer HTML at delivery time. Shape:

```html
<meta property="og:title"       content="LaunchLook audit for Sparkle Marketplace">
<meta property="og:description" content="Pre-launch audit. Verdict: Needs fixes before launch. 7 findings across trust, broken CTAs, mobile layout, and more.">
<meta property="og:image"       content="https://launchlook.app/images/og.png">
<meta property="og:url"         content="https://launchlook.app/r/jane-sparkle-marketplace">
<meta property="og:type"        content="article">
<meta name="twitter:card"       content="summary_large_image">
<meta name="twitter:title"      ...>
<meta name="twitter:description" ...>
<meta name="twitter:image"      ...>
```

The phrasing rules are locked the same as everywhere else: no
"comprehensive", no "AI-powered", no "next-generation"; verdict label
up front so a Reddit / Twitter scroller can decide whether to click.

## 9. Files this feature touches

```
scripts/share_report.py             # toggle CLI (public / private / handoff share)
scripts/sanitize_for_public.py      # PII strip helpers used at delivery + toggle
scripts/deliver_report.py           # _generate_shareable_page() helper
templates/r/shareable.html.j2       # per-customer HTML template (meta tags baked in)
landing/r.html                      # catch-all fallback page
landing/r/{slug}.html               # one per customer
landing/assets/r.js                 # client-side renderer
landing/assets/site.css             # persona pill + severity sidebar styles
landing/data/reports/{slug}.json    # one per customer, default is_public: false
landing/vercel.json                 # /r/:slug rewrite
vercel.json                         # /r/:slug rewrite (root)
tests/test_sanitize_for_public.py
tests/test_share_report.py
```
