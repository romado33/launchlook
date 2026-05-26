# Handoff Report -- workflow

## What it is

The Handoff Report is a separate deliverable that sits on top of the main
audit report. It's formatted for the developer the customer hires next.

Shape:

- A plain-text Markdown file (canonical -- the customer can paste it into
  Slack, Notion, GitHub Issues, an email, anywhere).
- A polished PDF that mirrors the Markdown (for buyers who want a single
  file they can hand off).

It re-uses the same findings, verdict, and passed checks that the main
report already produced. Nothing is re-audited. The work in a Handoff
Report is the framing, ordering, and persona narrative -- not new
findings.

Sections:

1. One-paragraph context -- plain English, sets up the site, builder,
   customer, and audit date.
2. Verdict at a glance -- the same standardized labels the main report
   uses ("Ready to share", "Safe for friends/family testing", "Needs
   fixes before launch", "Do not invite real users yet").
3. What's working -- the passed checks, in plain English bullets.
4. What needs fixing -- findings grouped into three buckets: must fix
   before launch, should fix soon, polish for later. Each finding shows
   the persona who caught it, what we saw, why it matters, and a
   copy-paste fix prompt the developer can drop straight into Cursor or
   Lovable.
5. Recommended order -- a short numbered list that reads like a real
   developer prioritized the fixes (not an algorithm).
6. What we'd flag in a code review -- Pro tier only; 3 to 5
   architecture or integration concerns that aren't surface findings.
7. Toolchain and access notes -- what the customer is using (builder,
   platform, deploy target, integrations) so the developer knows what
   they're walking into.
8. What we DIDN'T look at -- honest scope statement. We didn't audit
   the database schema, billing at scale, codebase performance under
   load, or security against motivated attackers. We say so. We say to
   get a real pentest before processing real payments.

The persona infrastructure (q5+q13) is reused for the "caught by"
attribution. The Pro-only code-review section is gated inside the
templates by `tier == "Pro Package"`, and the calling pipeline only
generates `code_review_notes` when the same condition holds, so neither
the LLM cost nor the template renders the section when it isn't paid
for.

## Who it's for

The customer is forwarding this to one of:

- A Webflow Expert they hired off the marketplace.
- A Codeable freelancer.
- A Cursor pair they're working with.
- An agency that just landed the contract.
- Their internal developer who joined mid-launch.

Either way, the developer has never seen this site before. The Handoff
Report saves them an hour of re-discovery and saves the customer a
price quote that bills for that hour.

## How it differs from the main report

Main report:

- Written for the founder. Plain English. Soft persona narrative.
  Emphasizes the verdict and the fix prompts the founder would paste
  into their builder.

Handoff Report:

- Written for the developer the founder hands off to. Same plain
  English, same persona attribution, but the order, framing, and the
  optional code-review section are tuned for someone who will read
  every section and act on it.

The two reports share the underlying findings and verdict. They differ
in audience-facing framing. We do NOT re-run the audit when generating
the Handoff Report; we re-use the same YAML payload.

## Pricing (per `PRODUCT-DECISIONS.md` section 8)

- Pro tier (`$99`): Handoff Report is included free with the main
  delivery.
- Starter and Scale Up: Handoff Report is available as a `$49` add-on
  (dropped from $99 on 2026-05-26 — see `docs/PRODUCT-DECISIONS.md` §9
  for the upsell-ladder math). Customer purchases it via the dedicated
  Stripe Payment Link (metadata `product=handoff_report`).
- Free tier: not eligible.

Discrimination at the webhook layer is metadata-first. The new $49
price point collides with the Scale Up Package SKU; the older $99
price collided with the Pro Package SKU. Both collisions are why we
never route by amount alone. See
`api/stripe-webhook.py::is_handoff_report_session` and the sibling
pattern around `is_confidence_check_session` (q6) and
`is_reverify_session` (q17).

## Operational flow for Rob

The Handoff Report is one more deliverable. The daily loop is:

1. Customer pays. Stripe webhook fires.
   - Pro tier: the main `process_checkout_session` path stamps a Notion
     row noting the tier as Pro Package.
   - Starter / Scale Up + add-on: `handle_handoff_report_purchase`
     stamps a Notion row noting the add-on against the customer's email
     and amount.
2. Rob already has the main audit YAML (the regular audit generated it
   when the customer paid for Starter / Scale Up). Rob now runs:

       python scripts/deliver_report.py \
           --customer customers/<slug>.yaml \
           --handoff-report \
           --tier-override "Starter+Handoff"   # or "Scale Up+Handoff"

   For Pro, no `--tier-override` is required:

       python scripts/deliver_report.py \
           --customer customers/<slug>.yaml \
           --handoff-report

   The CLI writes `handoff_report.md` and `handoff_report.pdf` into the
   customer's output directory under `out/<slug>/`.

3. Rob skims the draft. Plain-English Markdown is the canonical
   surface. Edits happen in the Markdown, not the PDF. If anything
   changes, regenerate the PDF only from the Markdown source by
   running the same command again.

4. Rob sends both files to the customer (typically attached to the
   delivery email). The customer forwards them to the developer they
   hired.

## LLM pieces

Three short LLM calls produce narrative text. Schemas live in
`scripts/ai_audit/llm_client.py::HANDOFF_TEXT_SCHEMA`. The pipeline
entry point is `scripts/ai_audit/pipeline.py::run_handoff_report`.

Prompts live in `scripts/ai_audit/prompts/`:

- `handoff_context_paragraph.txt` -- one paragraph, sets the developer
  up with site / builder / customer / audit date / shape.
- `handoff_recommended_order.txt` -- numbered list of fixes in the
  order an experienced developer would land them.
- `handoff_code_review_notes.txt` -- Pro tier only; 3 to 5
  architecture or integration concerns that go beyond the surface
  findings.

Voice rules per `SIMPLICITY-GUARDRAILS.md` section 3 and section 6:
plain English; no corporate vocabulary ("comprehensive deliverable",
"stakeholder summary", "executive overview"); honest scope statements;
"recommended order" sounds like a person prioritized it, not an
algorithm; no em-dashes (use colons or two sentences); persona tags
stay subtle.

## Verification before each delivery

- Open the Markdown and skim it. Every finding should have a "caught
  by" persona tag (q5+q13 infrastructure).
- Confirm the "Recommended order" reads like a person prioritized it.
  Edit the Markdown if it sounds like an algorithm.
- Confirm the "What we DIDN'T look at" section is present and honest.
  We never quietly drop this section.
- For Pro tier, confirm the code-review section actually has 3 to 5
  items. For Starter / Scale Up + add-on, confirm the section is
  omitted.

## Punted (q18 scope)

- ~~The Stripe Payment Link for the Handoff Report add-on has to be
  created in the Stripe dashboard and pasted into the Vercel env.~~
  **Done 2026-05-26.** `plink_1TbNP9BxCiPye3m0c5A1DNfq` (URL
  `https://buy.stripe.com/3cIdR864B3nu7Rx4Gk3cc06`) is wired into
  `landing/assets/config.js` `stripe.handoff`. $49 USD,
  `metadata.product=handoff_report`.
- The Plausible goal `HandoffReportAddOn` has to be added in the
  Plausible dashboard so the existing `plausible-event-name` attribute
  fires.
- The post-purchase email template for the add-on (just a confirmation
  noting "your Handoff Report is being generated") is shared with the
  main delivery email path -- not a dedicated template. If volume picks
  up we'll split it out.
