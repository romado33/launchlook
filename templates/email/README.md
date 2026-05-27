# Email templates

All transactional email copy lives here. One template per scenario. Variables in `{ALL_CAPS}`.

## Templates

| File | Trigger | Tier | Automated? |
|------|---------|------|------------|
| `welcome.txt` | Stripe purchase | all | BL-13 (or Stripe receipt + manual) |
| `delivery.txt` | After Notion report is ready | all | manual week 1 |
| `delivery_pdf.html.j2` / `delivery_pdf.txt.j2` | Resend send via `scripts/deliver_report.py` | paid | automated |
| `ask-for-quote.txt` | 48h after delivery if no quote | all | manual |
| `confidence_check_email.html.j2` / `confidence_check_email.txt.j2` | Fix Check delivery (internal filename retained) | paid | automated |
| `free-sample-outreach.txt` | Manual outreach (week 1) | n/a | manual |
| `share-snippets.txt` | Paste into reports / DMs | n/a | reference |

> **Note (May 2026):** the Day-3 and Day-7 follow-up nudges (`followup-d3.txt`, `followup-d7.txt`) and their cron / GitHub Actions runner were removed. Rob is not running automated nudges; the post-delivery email already carries the Fix Check / refund offer, so a separate cadence isn't earning its keep. If reinstating, the templates can be recovered from git history and the runner skeleton lived in `.github/workflows/daily-followup.yml` + `scripts/followup_send.py`.

Growth playbook: [`docs/SHARE-AND-REVIEWS.md`](../../docs/SHARE-AND-REVIEWS.md)

## Tone rules (apply to every template)

- Plain language. No marketing words (leverage, seamless, robust, etc.).
- Second person, active voice. Short sentences.
- Friendly, never condescending.
- Sign as "Rob" — not "the LaunchLook team."
- One specific concrete ask per email.

## Sender setup (Resend)

When ready:
1. Verify **launchlook.app** in Resend
2. Sender: `Rob at LaunchLook <hello@launchlook.app>`
3. Reply-To: `hello@launchlook.app`
