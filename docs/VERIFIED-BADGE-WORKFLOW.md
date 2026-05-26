# LaunchLook Verified Badge — Workflow

q17 ships a small "LaunchLook Verified" badge customers can drop on their
site footer. The badge links back to a public verification page on
launchlook.app, expires on a tier-dependent window, and renews via a $9
Stripe Payment Link.

This doc captures the **manual operator flow** Rob runs after each
delivery. The pieces are intentionally small so a single contractor can
ship them; see `docs/SIMPLICITY-GUARDRAILS.md` §2.1 / §3 / §5 for the
discipline rules this feature is bound by.

---

## 1. Tier validity windows (canonical)

| Tier              | Price  | Badge valid |
| ----------------- | ------ | ----------- |
| Starter Package   | $19    | 30 days     |
| Scale Up Package* | $49    | 90 days     |
| Pro Package       | $99    | 180 days    |
| Re-verification   | $9     | same window |

\* The codebase still uses "Full Package" in some places (legacy from the
pre-price-bump rename). The badge generator treats both labels as
equivalent — both map to 90 days.

After expiry the customer can either:

1. Buy a `$9` re-verification (we re-run the same checks and reissue),
   **or**
2. Upgrade their tier (a fresh audit re-issues the badge automatically).

The `$9` re-verify only applies to customers who **already had a badge**.
The script enforces this — see §3.

---

## 2. Generating a badge (post-delivery)

After a customer's report is delivered, Rob runs:

```bash
python scripts/generate_verified_badge.py \
  --customer customers/jane-sparkle.yaml
```

This writes:

```
landing/images/badges/{slug}/light.svg     # for light-background sites
landing/images/badges/{slug}/dark.svg      # for dark-background sites
landing/images/badges/{slug}/light.png     # PIL fallback (best-effort)
landing/images/badges/{slug}/dark.png      # PIL fallback (best-effort)
landing/data/verified/{slug}.json          # the verify.json record
```

The badge is intentionally small, monochrome, and understated (per
SIMPLICITY-GUARDRAILS §2.1). The SVG embeds the verified date as
"Verified · {Month YYYY}" and the customer slug in the link target.

The `verify.json` is what `/api/verify` reads:

```json
{
  "customer_slug": "jane-sparkle",
  "verified_at": "2026-05-26",
  "tier": "Scale Up Package",
  "expires_at": "2026-08-24",
  "issued_by": "LaunchLook",
  "checksum": "sha256:..."
}
```

The checksum is deterministic over the customer slug + tier + verified
date, so a regenerated badge with the same inputs produces the same JSON
byte-for-byte (useful for diffing).

The delivery email + report PDF will reference these URLs via the
embed snippet (see §5).

---

## 3. Re-verification (`$9` upsell)

When a customer's badge has expired they get a `$9 re-check` CTA on
`/verify?slug=...`. The CTA points at a Stripe Payment Link that **must
carry `metadata.product=reverify`** so `api/stripe-webhook.py` routes it
to `handle_reverify_purchase`. The handler:

1. Writes a `queued` row into the Notion Confidence Checks DB (shared
   queue with q6 Saboteur re-scans).
2. Sends a confirmation email asking Rob to verify the slug if needed.

Rob then runs:

```bash
python scripts/generate_verified_badge.py \
  --customer customers/jane-sparkle.yaml \
  --re-verify
```

The `--re-verify` flag is a guardrail: the script refuses to run if
`landing/data/verified/{slug}.json` does not already exist. This
enforces the "no prior badge = no `$9 re-verify`" rule at the operator
step — a misfired `$9` charge surfaces immediately so Rob can refund
and redirect to an upgrade tier.

The script reuses the original tier (from the existing `verify.json`)
unless `--tier` is passed explicitly, and stamps a fresh `verified_at`
+ `expires_at`. The output paths are identical, so the customer's
embed snippet keeps working with no change on their end.

---

## 4. Verification API

`GET /api/verify?slug=jane-sparkle` returns one of:

```json
{
  "valid": true,
  "customer_slug": "jane-sparkle",
  "tier": "Scale Up Package",
  "verified_at": "2026-05-26",
  "expires_at": "2026-08-24",
  "issued_by": "LaunchLook",
  "days_remaining": 89,
  "customer_url": "https://launchlook.app/verify?slug=jane-sparkle"
}
```

```json
{
  "valid": false,
  "reason": "expired",
  "customer_slug": "jane-sparkle",
  "tier": "Scale Up Package",
  "verified_at": "2026-02-26",
  "expires_at": "2026-05-26",
  "expired_on": "2026-05-26",
  "days_since_expiry": 1
}
```

```json
{
  "valid": false,
  "reason": "unknown_slug",
  "customer_slug": "not-a-real-customer",
  "hint": "We do not have a record of that badge. ..."
}
```

The endpoint also enforces a per-IP rate limit of **10 requests/minute**
(in-memory, best-effort; sufficient for the spam-prevention use case
without needing Redis/D1 yet). Hitting the limit returns `429` with
`retry_after_seconds`.

`landing/verify.html` + `landing/assets/verify.js` consume this endpoint
and render plain-English copy per SIMPLICITY-GUARDRAILS §3 — no
"certificate" / "issued by Authority" language, no over-promising.

---

## 5. Embed snippet (light variant)

The delivery email + report PDF include a "Get your LaunchLook Verified
badge" section with this snippet:

```html
<a href="https://launchlook.app/verify?slug=jane-sparkle" target="_blank" rel="noopener">
  <img src="https://launchlook.app/images/badges/jane-sparkle/light.svg" alt="LaunchLook Verified" height="48">
</a>
```

For Webflow customers, the snippet ships with plain-English
instructions: "Open Webflow Designer, drag an Embed element into your
footer, paste this code, save." This is the Webflow-specific guidance
required by SIMPLICITY-GUARDRAILS §3 (sound like a person, not a docs
team).

The dark-variant URL (`/images/badges/{slug}/dark.svg`) is mentioned in
the same section but not pasted inline (one snippet keeps it pasteable
in one shot; one URL is enough cognitive load for a tired solo dev
shipping at midnight).

---

## 6. Scope language

The badge is **not a certification**. The scope page at
`/verify-scope` spells this out, in plain English, in 3-4 short
paragraphs. Per SIMPLICITY-GUARDRAILS §3 / §5:

- "Reviewed for visible launch issues. Not a security certification."
- "What it means: we ran our checkup on this site within the last
  [window]."
- "What it doesn't mean: not a security audit, not WCAG-AA certified,
  not a guarantee against future regressions."

Grep guard: `rg "certified|certification|guarantee|guaranteed"
landing/verify-scope.html` should return zero matches. This is checked
by `tests/test_verified_badge.py`.

---

## 7. Pricing-card surface

Each tier card on `landing/index.html` and `landing/webflow.html` carries
a small line — single line, no badge image, no "NEW" tag — per
SIMPLICITY-GUARDRAILS §2:

- Starter card → "Includes LaunchLook Verified badge, valid 30 days*"
- Scale Up card → "Includes LaunchLook Verified badge, valid 90 days*"
- Pro card → "Includes LaunchLook Verified badge, valid 180 days*"

The `*` is a single shared footnote below the grid that links to
`/verify-scope` with the line "Reviewed for visible launch issues. Not a
security certification."

---

## 8. What's manual today / future state

- **Manual**: Rob runs `generate_verified_badge.py` after each delivery
  and pastes the URLs into the customer email. We could automate this in
  `deliver_report.py` once the badge generator stabilises and we
  confirm we like the visual.
- **Manual**: `$9 re-verify` Stripe Payment Link is not created yet.
  When created, paste the link into `landing/assets/config.js`
  (`stripe.reverify`) and Vercel env. See `docs/ROB-REMAINING-TODO.md`.
- **Future state**: `verify.json` lives in the repo today
  (`landing/data/verified/{slug}.json`). Once we have >25-50 customers,
  move this to Notion or a D1 / Postgres table so we can issue fresh
  badges without a deploy.
