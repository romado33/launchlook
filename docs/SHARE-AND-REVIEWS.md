# Share links & reviews — LaunchLook playbook

Quick ops guide for Rob. No Supabase required.

**Owner checklist:** [`ROB-REMAINING-TODO.md`](ROB-REMAINING-TODO.md) · **Tally intake:** [`TALLY-COPY-PASTE.md`](TALLY-COPY-PASTE.md)

## What to share publicly

| Asset | URL | When |
|-------|-----|------|
| Free 3-finding audit | https://launchlook.app/#hero | Discord, DMs, LinkedIn — lead with this (q4 lead magnet) |
| Community DIY checklist (GitHub) | https://github.com/{your-handle}/launchlook-prelaunch-checklist | When founders ask for a DIY artifact to share |
| Homepage | https://launchlook.app | After they're warm |
| Sample report | https://launchlook.app/sample | Skeptical buyers |

> Note: the in-app `/checklist` URL is the **paid Scale Up + Pro** deliverable (token-gated per q4). Don't lead with it; lead with the free 3-finding audit form on the homepage.

## Weekly rhythm (~30 min)

- **Mon:** 3 Looms → invite founders to drop their URL for the free 3-finding audit ([`cold-outreach-loom-script.md`](../templates/cold-outreach-loom-script.md))
- **Wed:** 1 LinkedIn post — one finding type + free-audit link
- **Fri:** Ask last week's customers for a quote ([`ask-for-quote.txt`](../templates/email/ask-for-quote.txt))

## After each delivery

1. Send [`delivery.txt`](../templates/email/delivery.txt) (includes quote ask + referral + free-audit share link)
2. Paste share block from [`share-snippets.txt`](../templates/email/share-snippets.txt) into Notion report footer if needed
3. Generate referral: `python scripts/referral_create.py --first-name … --email …`
4. Day 3: [`followup-d3.txt`](../templates/email/followup-d3.txt)
5. Day 7 (optional): [`followup-d7.txt`](../templates/email/followup-d7.txt)

## When you get a quote

Replace a homepage proof card in `landing/index.html` (Proof section) with real text — keep it short, name optional.

## Tracking (no Supabase)

- **Paid:** Stripe Dashboard → `python scripts/customers_track.py add ...` ([`CUSTOMER-TRACKING.md`](CUSTOMER-TRACKING.md))
- **Intake:** Tally + hello@launchlook.app inbox → `mark-intake`
- **Pipeline:** Notion **Customers** (mirror local tracker) · `customers_track.py stats` for milestone **10**
