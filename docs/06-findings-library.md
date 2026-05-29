# LaunchLook — Findings Library

This is the master reference of every issue type LaunchLook checks for. Used by Rob during manual audits and by the eventual scanner to look up detection patterns and fix prompts.

**Customer-facing text:** Use the **Customer explanation** field (and your report's "What I saw" / "Why it matters") in **plain English** for non-technical founders. Jargon belongs in paste-into-builder blocks only. See `templates/report-voice-guide.md`.

Stored as: Notion database `Findings Library` with one entry per finding. This document is the source of truth; sync from here to Notion (or vice versa) — but Notion is what Rob uses day-to-day.

## Schema

Each finding has:
- **Finding name** (short title)
- **Category** (Placeholders / Trust pages / Broken functionality / Mobile / Authentication / Sharing / UX / Performance / Brand)
- **Severity** (Critical / High / Medium / Low)
- **Detection method** (manual or regex/code pattern)
- **Customer explanation** (plain-English, with `{variables}` for per-customer substitution)
- **Fix prompt — Lovable**
- **Fix prompt — Bolt**
- **Fix prompt — Generic** (catch-all)
- **Notes** (any context, edge cases, false positive risks)

## Variables used across findings

- `{ACTUAL_NAME}` — customer's product name from intake form
- `{ACTUAL_EMAIL}` — customer's support email
- `{ONE_LINE_DESCRIPTION}` — what the app does
- `{PAGE}` — specific page name where issue appears
- `{BUTTON_NAME}` — actual visible button label
- `{FORM_NAME}` — actual form label
- `{LIST}` — array of items (broken links, errors, etc.)
- `{N}` — count
- `{PREFERRED_TERM}` — chosen terminology after consultation

## Category distribution (seed library)

| Category | # Findings | IDs |
|----------|-----------|-----|
| Placeholders & forgotten content | 7 | FL-001 to FL-007 |
| Trust pages & legal | 3 | FL-008 to FL-010 |
| Broken functionality | 6 | FL-011 to FL-016 |
| Mobile & responsive | 3 | FL-017 to FL-019 |
| Authentication & permissions | 3 | FL-020 to FL-022 |
| Sharing & meta | 3 | FL-023 to FL-025 |
| User experience | 4 | FL-026 to FL-029 |
| Performance & polish | 6 | FL-030 to FL-035 |

---

## Category: Placeholders & forgotten content

### FL-001 — Generic "Your Company Name" left in headers/footers
- **Severity**: High
- **Detection**: Search visible text for `/your\s+(company|business|brand)\s+name/i`
- **Customer explanation**: Your site still shows "Your Company Name" instead of your actual product name. This is one of the first things visitors notice — it signals "this isn't finished."
- **Fix prompt (Lovable)**: "On every page, find any instance of 'Your Company Name' or similar placeholder text in headers, footers, navigation, and metadata. Replace with the actual product name: {ACTUAL_NAME}. Don't change any code structure or styling — only the visible text."
- **Fix prompt (Bolt)**: "Search the entire codebase for placeholder text like 'Your Company Name' and replace with '{ACTUAL_NAME}'. Update headers, footers, page titles, and meta tags. Preserve all other code."
- **Fix prompt (Generic)**: "Find any instance of 'Your Company Name' or similar placeholder text and replace with the actual product name: {ACTUAL_NAME}. Check headers, footers, navigation, and metadata."

### FL-002 — Lorem ipsum still visible
- **Severity**: High
- **Detection**: `/lorem\s+ipsum|consectetur\s+adipiscing/i`
- **Customer explanation**: There's lorem ipsum placeholder text still showing on your site. Visitors will recognize it immediately.
- **Fix prompt (Generic)**: "Find any lorem ipsum or placeholder paragraph text on the site and replace it with real content. The content should be about: {ONE_LINE_DESCRIPTION}. Keep paragraphs roughly the same length as the placeholders."

### FL-003 — Default platform copy (Lovable starter text)
- **Severity**: High
- **Detection**: Look for known Lovable starter phrases like "Your AI-powered web application," "Welcome to your new app," "Get started by editing"
- **Customer explanation**: Some of Lovable's default starter copy is still on your homepage. Visitors who've seen other Lovable apps will recognize it.
- **Fix prompt (Lovable)**: "Replace any default Lovable starter copy on the homepage with content specific to my app. My app is {ONE_LINE_DESCRIPTION}. Write a real hero headline, subheadline, and CTA. Keep the visual layout the same."

### FL-004 — "[Insert X here]" brackets
- **Severity**: High
- **Detection**: `/\[insert\s+\w+|\[your\s+\w+|\[add\s+\w+/i`
- **Customer explanation**: There are template instructions like "[Insert tagline here]" still visible on the page. These are meant to be replaced before launch.
- **Fix prompt (Generic)**: "Find any text in square brackets that looks like a template instruction (e.g., '[Insert tagline]', '[Your value prop]'). Replace each with actual content based on the surrounding context."

### FL-005 — TODO/FIXME comments rendered to users
- **Severity**: Medium
- **Detection**: Visible "TODO" or "FIXME" in rendered text (not just code comments)
- **Customer explanation**: Internal developer notes ("TODO: add real description") are showing up on the live site as actual user-facing text.
- **Fix prompt (Generic)**: "Find any visible 'TODO' or 'FIXME' text on the live site and replace with the real content the note was asking for. Use the surrounding context to figure out what should be there."

### FL-006 — Placeholder email addresses
- **Severity**: Critical
- **Detection**: `/(support|hello|info|contact)@(example|yourdomain|domain|test)\.com/i`
- **Customer explanation**: Your contact/support email is still a placeholder like `support@example.com`. Visitors who try to reach you will bounce.
- **Fix prompt (Generic)**: "Find every instance of placeholder email addresses (anything @example.com, @yourdomain.com, @test.com) and replace with the real support email: {ACTUAL_EMAIL}. Check footer, contact page, mailto: links, and any 'help' or 'support' sections."

### FL-007 — "Acme Inc" / "Example Corp" default company
- **Severity**: High
- **Detection**: `/acme|example\s+(corp|inc|company|llc)/i` in visible text
- **Customer explanation**: References to "Acme Inc" or "Example Corp" are still showing up. These are default placeholder company names.
- **Fix prompt (Generic)**: "Replace any references to 'Acme', 'Example Corp', or similar placeholder company names with the actual product name: {ACTUAL_NAME}."
- **Notes**: "Acme" can be a legitimate brand name — verify before flagging.

---

## Category: Trust pages & legal

### FL-008 — Missing /privacy page
- **Severity**: High (Critical if collecting any user data)
- **Detection**: Try `GET /privacy`, `/privacy-policy` — returns 404
- **Customer explanation**: Your site has no privacy policy page. Most users — and almost certainly the App Store, payment processors, and ad platforms — expect one.
- **Fix prompt (Generic)**: "Add a /privacy route with a basic privacy policy page. Include sections for: what data we collect, how we use it, how we share it (or don't), data retention, user rights, and contact info. Use {ACTUAL_EMAIL} for the contact section. Link to it from the footer."

### FL-009 — Missing /terms page
- **Severity**: High
- **Detection**: 404 on `/terms`, `/terms-of-service`, `/tos`
- **Customer explanation**: Your site has no Terms of Service. Users have nothing to agree to, and payment processors usually require one.
- **Fix prompt (Generic)**: "Add a /terms route with basic Terms of Service. Include sections for: acceptance of terms, service description, user obligations, prohibited uses, termination, disclaimers, and contact info. Link from the footer."

### FL-010 — Missing /contact or contact info
- **Severity**: Medium
- **Detection**: No visible contact email, no /contact page, no contact form
- **Customer explanation**: Visitors can't easily find how to contact you. This hurts trust and conversion.
- **Fix prompt (Generic)**: "Add a visible way for users to contact me. Either add a /contact page with an email address ({ACTUAL_EMAIL}) and optional contact form, or put a clear support email in the footer of every page."

---

## Category: Broken functionality

### FL-011 — Buttons that do nothing on click
- **Severity**: Critical
- **Detection**: Click each visible button, observe DOM/navigation
- **Customer explanation**: The "{BUTTON_NAME}" button doesn't do anything when clicked. Users will think the site is broken.
- **Fix prompt (Generic)**: "The {BUTTON_NAME} button on {PAGE} is not working — it appears clickable but does nothing when clicked. Investigate why and fix it so it performs its intended action: {EXPECTED_BEHAVIOR}. Don't change the button's appearance."

### FL-012 — Broken internal links (404s)
- **Severity**: High
- **Detection**: Crawl all `<a href>` values, check status codes
- **Customer explanation**: Some internal links lead to "page not found" errors. Specifically: {LIST_OF_BROKEN_LINKS}.
- **Fix prompt (Generic)**: "Fix these broken internal links: {LIST}. For each link, either point it to the correct page if it exists, or create the missing page, or remove the link entirely if no longer needed."

### FL-013 — Forms that don't submit
- **Severity**: Critical
- **Detection**: Fill out form with test data, click submit, observe network tab and DOM
- **Customer explanation**: The {FORM_NAME} form doesn't actually submit. Users fill it out, click submit, and nothing happens.
- **Fix prompt (Generic)**: "The {FORM_NAME} form on {PAGE} doesn't work — when users fill it out and click submit, nothing happens. Fix the form so submissions are saved or sent properly. {SPECIFIC_BEHAVIOR_NEEDED}."

### FL-014 — Forms submit with no confirmation
- **Severity**: Medium
- **Detection**: Submit form, observe whether user receives any confirmation
- **Customer explanation**: When users submit the {FORM_NAME} form, they don't get any confirmation that it worked. They'll wonder if it submitted at all.
- **Fix prompt (Generic)**: "After the {FORM_NAME} form submits, show a clear success message or redirect to a confirmation page. The user needs to know their submission worked."

### FL-015 — Console errors on page load
- **Severity**: Medium (Higher if functional features depend on the failing code)
- **Detection**: Open DevTools, load page, capture all console errors
- **Customer explanation**: Your browser shows {N} errors when the page loads. Some of these might be causing features to fail.
- **Fix prompt (Generic)**: "These JavaScript errors appear in the console when {PAGE} loads: {ERROR_LIST}. Investigate each and fix the underlying cause. Don't suppress errors — fix them."

### FL-016 — Failed network requests (4xx/5xx)
- **Severity**: High
- **Detection**: Open Network tab, load page, filter for non-2xx responses
- **Customer explanation**: When the page loads, some background requests are failing: {REQUEST_LIST}. Features depending on these requests will be broken.
- **Fix prompt (Generic)**: "These network requests are failing on {PAGE}: {LIST_WITH_STATUS_CODES}. Investigate each and fix the underlying issue — wrong URL, missing endpoint, auth failure, etc."

---

## Category: Mobile & responsive

### FL-017 — Mobile layout overflow / horizontal scroll
- **Severity**: High
- **Detection**: Open in 375px viewport, look for `document.body.scrollWidth > window.innerWidth`
- **Customer explanation**: On mobile, your page scrolls sideways because something is wider than the screen. This makes the site feel broken on phones.
- **Fix prompt (Generic)**: "On mobile devices, {PAGE} has horizontal scrolling — something is wider than the viewport. Find what's overflowing (often a wide image, table, or container with fixed width) and make it responsive. Don't break the desktop layout."

### FL-018 — Text too small on mobile
- **Severity**: Medium
- **Detection**: Body text rendering under ~14px on mobile
- **Customer explanation**: Body text on mobile is too small to read comfortably (currently {SIZE}px). Most apps use at least 16px for body text on mobile.
- **Fix prompt (Generic)**: "On mobile, increase the body text to at least 16px. Currently it's rendering at {SIZE}px which is hard to read on phones."

### FL-019 — Tap targets too small
- **Severity**: Medium
- **Detection**: Buttons/links smaller than 44×44px on mobile
- **Customer explanation**: Some buttons are too small to tap easily on mobile (under 44×44 pixels). Apple and Google both recommend 44px as a minimum.
- **Fix prompt (Generic)**: "On mobile, increase tap target sizes for {LIST_OF_ELEMENTS} to at least 44×44 pixels. Either add padding or increase the button size directly."

---

## Category: Authentication & permissions

### FL-020 — Logged-out access to protected pages
- **Severity**: Critical
- **Detection**: Try `GET /dashboard`, `/admin`, `/settings` etc. without auth
- **Customer explanation**: Users who aren't logged in can access {PROTECTED_ROUTES}. This may expose data they shouldn't see.
- **Fix prompt (Lovable)**: "These routes load content even when no user is signed in: {LIST}. Add authentication checks so that visiting these routes while logged out redirects to /login or shows an empty/error state. Use Supabase auth state to verify."
- **Fix prompt (Bolt)**: "Add auth guards to these routes: {LIST}. Verify the user has an active session before rendering content. Redirect unauthenticated users to /login."

### FL-021 — Cross-user data visible
- **Severity**: Critical
- **Detection**: Sign in as User A, then as User B, compare what each can see
- **Customer explanation**: User A can see User B's data (specifically: {EXAMPLE}). This means anyone who signs up can see other users' information.
- **Fix prompt (Lovable)**: "User A can see User B's {DATA_TYPE} on the {PAGE} page. This means Supabase queries aren't filtering by user. Add row-level security policies on the {TABLE_NAME} table that restrict reads to `auth.uid() = user_id`. Also update the query in the page component to filter by current user."

### FL-022 — Signup confirmation email never arrives
- **Severity**: Critical
- **Detection**: Sign up with fresh email, wait 5+ minutes
- **Customer explanation**: When new users sign up, the confirmation email never arrives. They can't complete signup.
- **Fix prompt (Generic)**: "When users sign up, they should receive a confirmation email but none arrives. Check the email provider configuration (Resend, SendGrid, or Supabase's built-in email), verify the sender domain is set up, and ensure the signup flow actually triggers the email send."

---

## Category: Sharing & meta

### FL-023 — Default meta description (platform default)
- **Severity**: Medium
- **Detection**: Check `<meta name="description">` against known platform defaults
- **Customer explanation**: When your link is shared on social media, it shows the platform's default description instead of one about your actual app.
- **Fix prompt (Generic)**: "Update the meta description to describe my actual app: {ONE_LINE_DESCRIPTION}. Also set Open Graph tags (og:title, og:description, og:image) so the link previews well when shared on Twitter, LinkedIn, Slack, etc."

### FL-024 — No favicon (showing default platform icon)
- **Severity**: Medium
- **Detection**: Check `<link rel="icon">` — verify it's custom, not platform default
- **Customer explanation**: Your site uses the default browser icon (or the platform's). It should have your own favicon so users recognize tabs.
- **Fix prompt (Generic)**: "Add a custom favicon. I'll provide an image (or generate a simple one based on the app name '{ACTUAL_NAME}'). Update the <link rel='icon'> tag and add the necessary icon files."

### FL-025 — Page title is generic ("My App" or platform default)
- **Severity**: Medium
- **Detection**: Check `<title>` tag and per-page title overrides
- **Customer explanation**: Your page titles in browser tabs are generic. Users won't see your app name in their tab list.
- **Fix prompt (Generic)**: "Update page titles so each page has a meaningful title with the app name. Format: 'Page Name | {ACTUAL_NAME}'. Update both the default <title> and any per-page overrides."

---

## Category: User experience

### FL-026 — No empty states (blank dashboards for new users)
- **Severity**: Medium
- **Detection**: Sign in with brand-new account, observe dashboard/main pages
- **Customer explanation**: When a new user signs in for the first time, the dashboard is completely empty with no instructions. They won't know what to do.
- **Fix prompt (Generic)**: "When a user has no {ITEMS} yet, the {PAGE} page shows nothing. Add a friendly empty state with: an icon or illustration, a short message ('No {items} yet'), and a clear CTA button to create the first one."

### FL-027 — No loading states
- **Severity**: Low
- **Detection**: Slow network throttle in DevTools, observe page during data fetch
- **Customer explanation**: While data is loading, the page shows nothing — users see a blank screen and may think it's broken.
- **Fix prompt (Generic)**: "Add loading states (skeleton screens, spinners, or 'Loading...' text) to {LIST_OF_PAGES} so users see something is happening while data loads."

### FL-028 — Error states swallow errors silently
- **Severity**: Medium
- **Detection**: Force errors (disconnect network, submit invalid data) and observe UI
- **Customer explanation**: When something goes wrong, users get no feedback — the action just silently fails.
- **Fix prompt (Generic)**: "When operations fail (network errors, validation errors, server errors), show users a clear error message instead of failing silently. Use a toast notification or inline error text. Be specific about what went wrong when possible."

### FL-029 — No "back" or navigation context
- **Severity**: Low
- **Detection**: Navigate deep into the app, observe whether back/breadcrumb is clear
- **Customer explanation**: When users navigate deep into the app, there's no clear way back to where they came from.
- **Fix prompt (Generic)**: "Add either a back button or breadcrumb navigation on deeper pages so users can navigate back to where they were."

---

## Category: Performance & polish

### FL-030 — Massive unoptimized images
- **Severity**: Medium
- **Detection**: Check Network tab for >1MB images
- **Customer explanation**: Some images on your site are very large (e.g., {SIZE}MB) and slow down page loads.
- **Fix prompt (Generic)**: "These images are oversized: {LIST_WITH_SIZES}. Compress them and use modern formats (WebP). Aim for under 200KB per image for hero/featured images and under 50KB for thumbnails."

### FL-031 — Render-blocking resources
- **Severity**: Low
- **Detection**: Lighthouse / WebPageTest
- **Customer explanation**: Some scripts and stylesheets are blocking the page from rendering quickly. Users see a blank page for longer than necessary.
- **Fix prompt (Generic)**: "Defer non-critical JavaScript with the `defer` or `async` attributes. Inline critical CSS for above-the-fold content. The goal is for users to see content within 1.5 seconds on a typical connection."

### FL-032 — No 404 page
- **Severity**: Low
- **Detection**: Visit `/nonexistent-route-12345`
- **Customer explanation**: When users hit a URL that doesn't exist, they get a generic browser error instead of a friendly 404 page.
- **Fix prompt (Generic)**: "Add a custom 404 page that shows when users visit URLs that don't exist. Include: a clear 'Page not found' message, a link back to home, and optionally a search or sitemap. Style it consistently with the rest of the site."

### FL-033 — Inconsistent terminology (customer/client/user)
- **Severity**: Medium
- **Detection**: Manual scan for multiple terms referring to the same entity
- **Customer explanation**: Your app uses "customer," "client," and "user" interchangeably to refer to the same thing. Pick one and use it consistently — it makes the app feel more thought-through.
- **Fix prompt (Generic)**: "The app uses 'customer,' 'client,' and 'user' to refer to the same role. Pick {PREFERRED_TERM} and replace the others everywhere in the UI. Don't change database table or column names — only user-facing labels."

### FL-034 — Capitalization inconsistency on UI labels
- **Severity**: Low
- **Detection**: Manual scan of buttons, headers, nav items
- **Customer explanation**: Buttons and labels use inconsistent capitalization — some use Title Case, some use sentence case, some are ALL CAPS.
- **Fix prompt (Generic)**: "Standardize capitalization across all UI elements. Use sentence case for buttons ('Save changes', not 'Save Changes' or 'SAVE CHANGES') and title case for page headings. Apply this consistently throughout the app."

### FL-035 — Default Lovable / Bolt / Base44 branding still showing
- **Severity**: High
- **Detection**: Search for "Built with Lovable" or platform branding
- **Customer explanation**: Your site still shows "Built with Lovable" or similar platform branding. If you're on a paid plan, you can remove this.
- **Fix prompt (Lovable)**: "Remove the 'Built with Lovable' badge from the site. This is in the project settings under branding. (Note: requires a paid Lovable plan.)"

---

## How to add new findings

After every manual audit, ask: "Is there a finding here that doesn't yet exist in the library?" If yes, add it before sending the report. The library should grow ~2-5 entries per audit in the first 30 customers.

Format for adding:
1. Open the Findings Library Notion database
2. New entry → fill in all fields per schema
3. ID auto-generates as FL-036, FL-037, etc.
4. Tag with `added: YYYY-MM-DD` and `first_seen_customer: <name>`

## How to revise existing findings

When fix prompts work well or poorly with real customers, edit them. Track edit history in the Notes field.

Patterns to revise:
- Customer pushed back on the explanation → rewrite to be clearer
- Customer's AI builder didn't apply the fix correctly → rewrite the prompt
- Same finding appearing under multiple categories → consolidate

## Severity calibration

- **Critical**: Will cause real harm if not fixed before launch. Data leaks, broken signup, missing trust pages required by payment processors.
- **High**: Visible to most users on first visit. Looks unfinished or broken. Placeholder text in headers, broken main CTAs, obvious mobile issues.
- **Medium**: Visible to engaged users or in specific flows. Empty states missing, inconsistent terminology, performance issues.
- **Low**: Polish-level. Visible only on close inspection. Capitalization, minor copy issues, optional features.

Default to one severity higher when in doubt — vibe coders tend to under-react to mid-severity issues that real users will notice.

## False positive management

Some patterns will fire on intentional content:
- "Coming soon" can be a real feature gate, not a placeholder
- "Example" can be in legitimate product copy (e.g., "for example, you could...")
- "Acme" might be a real product name

For each finding, the Notes field should document known false positive risks. Manual audits screen these. The future scanner flags but doesn't auto-include — Rob makes the call.

## Maintenance schedule

- **Per audit**: add 1-3 new findings if observed
- **Monthly**: review entries with low usage; either improve or retire
- **Quarterly**: review category distribution; ensure no category is unhealthy (too sparse or too crowded)

## Future: export to JSON for scanner

When BL-15 (scanner → Notion ingestion) ships, the Findings Library will be exported to `findings_library/findings.json` for use by the scanner's lookup logic.

```json
{
  "findings": [
    {
      "id": "FL-001",
      "name": "Generic 'Your Company Name' left in headers/footers",
      "category": "Placeholders",
      "severity": "High",
      "detection": {
        "type": "regex",
        "pattern": "your\\s+(company|business|brand)\\s+name",
        "flags": "i"
      },
      "explanation": "Your site still shows \"Your Company Name\" instead of your actual product name. This is one of the first things visitors notice — it signals \"this isn't finished.\"",
      "fix_prompts": {
        "lovable": "On every page, find any instance of 'Your Company Name'...",
        "bolt": "Search the entire codebase for placeholder text...",
        "generic": "Find any instance of 'Your Company Name'..."
      }
    }
  ]
}
```
