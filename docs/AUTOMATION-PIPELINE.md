# Audit automation pipeline (human gate before customer delivery)

Automates **draft generation** for free and paid audits. **Never** sends customer report emails — that stays manual (`deliver_report.py --send` or audit UI “Approve & ship”).

## Architecture

```
Free hero form ──► /api/free-audit ──► Notion Free Audit (Status=queued)
Tally intake     ──► /api/tally-webhook ──► Notion Customers (Status=Intake Received)
Stripe pay       ──► /api/stripe-webhook ──► Notion Customers (Tier + Paid)  [already existed]

Local worker (you or cron):
    python scripts/process_audit_queue.py
        ──► capture + prescreen + HTML + security/perf/a11y + form smoke (+ Pro email poll)
        ──► LLM findings + YAML → customers/{slug}.yaml
        ──► Notion Status → draft_ready / notes [automation:draft_ready]
        ──► Email ADMIN_EMAIL with review checklist

You:
    python scripts/audit_ui.py --slug {slug} --review-ai
    deliver_report.py --send   # only when ready (paid)
    free email delivery        # manual; pick top 2 findings (see FREE_AUDIT_DELIVER_COUNT)
```

Vercel cannot run the full pipeline (timeout + no Playwright). **Queue state lives in Notion**, not on the server filesystem.

## Free tier: 2 findings

- Constant: `scripts/launchlook_constants.py` → `FREE_AUDIT_DELIVER_COUNT = 2`
- Pipeline runs at **Starter cap (10)**; you deliver **2** after review in audit UI.

## Paid tier: tier caps unchanged

| Tier | Pipeline cap |
|------|----------------|
| Starter | 10 |
| Scale Up | 30 |
| Pro | 40 |

## Form smoke + email tests

Included automatically when the worker runs `ai_audit.pipeline.run()`:

- **Form smoke** — Playwright fills public forms with `stranger+launchlook-smoke-test@launchlook.app` fixtures; skips checkout/destructive forms.
- **Pro email round-trip** — polls for confirmation email when `customers/{slug}.yaml` sets `form_smoke_test.customer_email` (worker seeds this for Pro jobs).

Submissions and test mail land in **your** inbox (and the customer’s provider if they use Resend etc.). Review before promoting anything to a customer-facing finding.

## Commands

```bash
# List pending
python scripts/process_audit_queue.py --list

# Process oldest job
python scripts/process_audit_queue.py

# Process up to 3
python scripts/process_audit_queue.py --limit 3

# Re-run one slug after a fix
python scripts/process_audit_queue.py --slug jane-example-com

# Offline smoke (stub LLM)
python scripts/process_audit_queue.py --slug test --dry-run --provider stub
```

## Notion statuses

### Free Audit Requests DB

| Status | Meaning |
|--------|---------|
| `queued` | Submitted; waiting for worker |
| `processing` | Worker running |
| `draft_ready` | YAML ready — **your** review |
| `failed` | Automation error — check email / logs |
| `delivered` | You sent the free findings email |
| `skipped` / `abuse` | Manual |

Add `processing` and `draft_ready` to the Status select in Notion (or run `scripts/ensure_free_audit_notion_db.py --create-if-missing` on a fresh DB).

### Customers DB

No new Status required. Worker sets **In progress** and appends `[automation:draft_ready]` to Notes. Skip re-processing while that marker is present.

## Environment

Same as AI pipeline plus:

| Variable | Purpose |
|----------|---------|
| `ADMIN_EMAIL` | Draft-ready + failure notifications |
| `RESEND_API_KEY` | Founder emails only |
| `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` | LLM |
| Playwright + Chromium | Capture + form smoke |

## Scheduling (suggested)

On your machine or a small VM:

```bash
# Every 15 minutes, one job at a time
*/15 * * * * cd /path/to/onceover && python scripts/process_audit_queue.py >> logs/automation.log 2>&1
```

## What we explicitly do not automate

- Customer delivery email / PDFs (`deliver_report.py --send`)
- Notion `Delivered` checkbox (you)
- Loom booking (Pro)
- Fingerprint writeback after free delivery (`persist_free_audit_fingerprints` — still manual)

## Related docs

- `docs/AI-AUDIT-PIPELINE.md`
- `docs/FREE-AUDIT-WORKFLOW.md`
- `docs/MANUAL-REVIEW-WORKFLOW.md`
