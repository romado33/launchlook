# Email templates

All transactional email copy lives here. One template per scenario. Variables in `{ALL_CAPS}`.

## Templates

| File | Trigger | Tier | Automated? |
|------|---------|------|------------|
| `welcome.txt` | Stripe purchase | all | BL-13 (or Stripe receipt + manual) |
| `delivery.txt` | After Notion report is ready | all | manual week 1 |
| `ask-for-quote.txt` | 48h after delivery if no quote | all | manual |
| `followup-d3.txt` | 3 days after `Delivered = true` | all | BL-13 cron |
| `followup-d7.txt` | 7 days after `Delivered = true` | all | optional manual |
| `free-sample-outreach.txt` | Manual outreach (week 1) | n/a | manual |
| `share-snippets.txt` | Paste into reports / DMs | n/a | reference |

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
