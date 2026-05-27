# Testers Cast

> **INTERNAL-ONLY (as of 2026-05-26).** The 7-persona named labels are no longer surfaced to customers (landing footers, report PDFs, shareable pages, /r/{slug} pages — all stripped). Underlying scanning behavior is unchanged: the offline pipeline still tags findings internally for routing and category coverage, and the dormant CSS / JS helpers stay in place so re-enabling display is a one-line change. Section "How the cast appears to buyers" below is now historical.

Canonical reference for the 7 Testers personas. Read this before tagging findings (internally), writing report copy, or adding marketing language about the cast. Do **not** invent new Testers. Do **not** describe existing ones inconsistently.

Companion docs: `SIMPLICITY-GUARDRAILS.md`, `PRODUCT-DECISIONS.md`.

---

## How the cast appears to buyers

- **Landing page:** footer tooltip only. Never a hero section. (See `SIMPLICITY-GUARDRAILS.md` §2.6.)
- **Report PDF:** small inline tag on the finding, e.g. "Caught by The Snoop." Never a giant badge. (See `SIMPLICITY-GUARDRAILS.md` §3.4.)
- **Marketing copy:** flavor, not value prop. The buyer is buying findings, not personas.

Dev equivalents below are internal-only references for engineers writing rule packs. They never cross the customer boundary.

---

## The 7 Testers

### 1. The Tourist

- **Bio:** First-time visitor walking through home page, CTA, signup, core action.
- **What they look for:** Confusion, dead ends, boring moments along the main path. They notice when a CTA is unclear, when a flow stalls, when nothing on the page tells them what to do next. They give up fast.
- **Dev equivalent (internal-only):** happy-path E2E.
- **Example headline:** *"Your homepage CTA goes to a page that doesn't explain what to do next."*
- **Tag (small text):** Caught by The Tourist

### 2. The Skeptic

- **Bio:** Looks for trust gaps before handing over an email or a credit card.
- **What they look for:** Missing privacy or terms pages, fake-looking testimonials, dead footer links, no contact info, sketchy redirect URLs. Anything that whispers "this might be a scam."
- **Dev equivalent (internal-only):** trust audit.
- **Example headline:** *"Your footer privacy link goes to a 404."*
- **Tag (small text):** Caught by The Skeptic

### 3. The Klutz

- **Bio:** Clicks the wrong button, double-submits, hits back mid-flow, refreshes during checkout.
- **What they look for:** Error states that crash, double-charges, lost form data on back-button, unclear validation messages. Real users do all of this; the Klutz finds where it breaks.
- **Dev equivalent (internal-only):** error handling and edge cases.
- **Example headline:** *"Refreshing during checkout loses everything in the cart."*
- **Tag (small text):** Caught by The Klutz

### 4. The Snoop

- **Bio:** Pokes around for things you didn't mean to leave open.
- **What they look for:** Exposed API keys in page source, public admin routes, missing security headers, leaky URLs, IDs in URLs that shouldn't be guessable.
- **Dev equivalent (internal-only):** security-lite (NOT full pen-test; see `PRODUCT-DECISIONS.md` §5).
- **Example headline:** *"Your /admin route loads without a login on first visit."*
- **Tag (small text):** Caught by The Snoop

### 5. The Phone-First Friend

- **Bio:** Only ever opens the site on mobile.
- **What they look for:** Tiny tap targets, broken layouts, viewport bugs, off-screen CTAs, fixed elements that cover the screen, fonts too small to read.
- **Dev equivalent (internal-only):** mobile audit.
- **Example headline:** *"Your signup button on iPhone sits behind a fixed banner and can't be tapped."*
- **Tag (small text):** Caught by The Phone-First Friend

### 6. The Saboteur

- **Bio:** Runs the same checks again after every AI-driven change. Asks one question: "What broke that used to work?"
- **What they look for:** Regressions. Things that passed last week and fail this week. Powers the Confidence Check re-scan add-on.
- **Dev equivalent (internal-only):** regression / Confidence Check re-scan.
- **Example headline:** *"Your contact form submit worked last week and now silently fails."*
- **Tag (small text):** Caught by The Saboteur

### 7. The Stranger Who Tried to Sign Up

- **Bio:** Fills out the actual forms with safe synthetic values, end-to-end.
- **What they look for:** Whether form submissions reach where they're supposed to (inbox, CRM, webhook), whether confirmation emails fire, whether the database actually got the row. The form looks fine; the submission may not work.
- **Dev equivalent (internal-only):** form-submit smoke test.
- **Example headline:** *"Your newsletter signup confirms on the page but no email is sent and no row is written."*
- **Tag (small text):** Caught by The Stranger Who Tried to Sign Up

---

## Voice rules for tagging findings

1. **Format:** "Caught by [Tester]" in small text on the finding card. Not a giant badge, not a sidebar. (See `SIMPLICITY-GUARDRAILS.md` §3.4.)
2. **Multiple Testers per finding:** allowed when genuinely overlapping. Format: *"Caught by The Tourist + The Phone-First Friend."* **Max 2 tags per finding.** If a finding wants 3 tags, split it.
3. **Pick the most specific Tester first.** A signup-form bug on mobile is The Phone-First Friend, not The Tourist. The Tourist is the fallback for happy-path issues with no narrower owner.
4. **Never use dev equivalents in customer-facing copy.** Buyers see "Caught by The Snoop," not "Caught by security-lite scanner." (See `SIMPLICITY-GUARDRAILS.md` §6.)
5. **Tone:** a wink, not a sales pitch. Tag text stays small, never bold, never colored, never iconified beyond a small dot.

---

## Adding or retiring Testers

**Do not add new Testers without explicit user approval.** The cast is sized 1:1 to the audit categories that ship in the report. An 8th Tester would either duplicate an existing one or imply a category that doesn't exist in the pipeline. If a future worker has a real case for an 8th (a genuinely new audit category, not a reskin), write a proposal and ping the user. Same rule as `PRODUCT-DECISIONS.md` §3.

If a Tester needs retiring (audit category dropped), retire it here with a date and remove the inline tag from finding templates. Do not leave orphaned Testers in the cast.
