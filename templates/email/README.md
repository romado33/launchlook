# Email templates

All transactional email copy lives here. One template per scenario. Variables in `{ALL_CAPS}`.

## Templates

| File | Trigger | Tier | Automated? |
|------|---------|------|------------|
| `welcome.txt` | Stripe purchase | all | BL-13 (or Stripe Customer Receipt) |
| `delivery.txt` | Rob sends manually after delivery | all | manual at MVP |
| `followup-d3.txt` | 3 days after `Delivered = true` | all | BL-13 cron |
| `followup-d7.txt` | 7 days after `Delivered = true` | Polish only | BL-13 cron |
| `free-sample-outreach.txt` | Manual outreach (week 1) | n/a | manual |

## Tone rules (apply to every template)

- Plain language. No marketing words (leverage, seamless, robust, etc.).
- Second person, active voice. Short sentences.
- Friendly, never condescending. Vibe coders are smart people, not beginners to talk down to.
- Sign as "Rob" — not "the Onceover team."
- One specific concrete ask per email. Don't bury the action.

## Forbidden words

Anywhere in customer-facing email copy:
`leverage`, `seamless`, `robust`, `cutting-edge`, `innovative`, `streamline`, `powerful`, `elevate`, `empower`, `unlock`, `supercharge`, `revolutionize`, `transform` (as a sales verb), `best-in-class`, `world-class`

## Variable substitution

For MVP, Rob substitutes manually before sending. Once BL-13 lands, the cron script does it via Python `.format()` from Notion Customers DB fields.

## Sender setup (Resend)

When ready:
1. Add `onceover.app` as a verified domain in Resend
2. Add SPF, DKIM, DMARC DNS records as Resend instructs
3. Use sender: `Rob at Onceover <hello@onceover.app>`
4. Set Reply-To: `hello@onceover.app`
5. Test deliverability to Gmail, Outlook, Apple Mail, ProtonMail before going live
