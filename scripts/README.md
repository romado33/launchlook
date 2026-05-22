# Scripts

Operational scripts for LaunchLook. All written for Python 3.11+. None are required for the first audits — manual workflow first.

**Rob setup still manual:** [`docs/ROB-REMAINING-TODO.md`](../docs/ROB-REMAINING-TODO.md) · **Tally:** [`docs/TALLY-COPY-PASTE.md`](../docs/TALLY-COPY-PASTE.md)

## When to use each

| Script | BL ID | Status | When to first run |
|--------|-------|--------|-------------------|
| `customers_track.py` | — | ready | After `init` — every payment / delivery |
| `audit_checklist.py` | — | ready | Start of every manual audit |
| `findings_lookup.py` | — | ready | During write-up — search library |
| `email_render.py` | — | ready | Before sending any transactional email |
| `qsg_compose_prompt.py` | BL-09 | ready | First Launch Pack customer |
| `qsg_render.py` | BL-10 | ready | After QSG edited in ChatGPT |
| `qsg_generate.py` | BL-09 v2 | skeleton — needs API key | When you decide to automate QSG generation |
| `notion_test.py` | BL-04 | ready | After Notion workspace + token set up |
| `referral_create.py` | BL-12 | skeleton — needs Stripe + Notion keys | First customer to deliver |
| `followup_send.py` | BL-13 | skeleton — needs Notion + Resend keys | First customer to deliver + 3 days |
| `crawler.py` (TODO) | BL-14 | NOT BUILT | After customer 10 — hard gate |
| `notion_populate.py` (TODO) | BL-15 | NOT BUILT | After BL-14 |

## Order of operations per customer

```
1. Customer pays via Stripe → customers_track.py add → row in Notion Customers DB
2. Intake → customers_track.py mark-intake
3. Rob audits manually using templates/notion/report-* template
   ↓
3. (BL-09) For Launch Pack/Polish tier:
   python scripts/qsg_compose_prompt.py --app-name ... > qsg_prompt.txt
   → Paste into ChatGPT → edit → paste into Notion report Part 2
   ↓
4. (BL-12) Generate referral code:
   python scripts/referral_create.py --customer-id <notion_page_id>
   ↓
5. Rob delivers — copies Notion link into delivery email
   → Marks Delivered=true + Payment Date in Notion
   ↓
6. (BL-13) GitHub Actions runs daily at 14:00 UTC:
   python scripts/followup_send.py --days-after 3
   → Sends day-3 follow-up to anyone delivered 3 days ago
```

## Manual fallbacks

If any script breaks or any API key isn't set, the workflow degrades gracefully:

- `qsg_compose_prompt.py` works without any API key — its output is paste-ready
- `referral_create.py` has `--dry-run` to print the code without calling Stripe
- `followup_send.py` has `--dry-run` to print the emails it would send

## Common gotchas

- **Notion property names are case-sensitive.** If the DB schema diverges from the spec in `templates/notion/README.md`, scripts will silently miss customers. Run with `--dry-run` first whenever the schema changes.
- **Stripe coupon codes are uppercase.** `referral_create.py` enforces this. Don't manually create lowercase codes in Stripe — the script can't find them by their canonical form.
- **GitHub Actions secrets** must be set via `gh secret set` or the web UI. Never check `.env` into the repo.
