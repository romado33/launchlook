# AI cost monitoring

**Last updated:** May 26, 2026
**Owner:** Rob
**Status:** Live as of gap5 ship. Every LLM call in the audit pipeline
is now logged for per-customer cost tracking, daily roll-ups, and
margin alerts.

This is an **internal-only tool** per `SIMPLICITY-GUARDRAILS.md` §6.
Nothing in this system is ever shown to a customer (no landing page,
no report PDF, no QSG, no email). Cost data lives only on Rob's local
disk under `data/ai_costs/`.

---

## Why this exists

LaunchLook's pricing is fixed at $19 / $49 / $99 (see
`PRODUCT-DECISIONS.md` §1 and §7). The original spec assumed AI cost
would be 1 to 2% of revenue per audit (see `AI-AUDIT-PIPELINE.md`,
"Cost expectations"). As customer volume grows we need a way to catch
the moment that ratio drifts before the per-audit margin disappears.

The system answers three questions:

1. **Per-customer:** how much did this customer's audit actually cost?
2. **Daily / weekly:** what is the total LLM bill, and what is the
   blended margin against revenue?
3. **Alert:** which audits cost more than 20% of the tier price, and
   are any of them looping / retrying excessively?

---

## How the log gets written

Every call to Anthropic / OpenAI in `scripts/ai_audit/llm_client.py`
is wrapped with `cost_tracker.track_call(...)`. The pipeline sets the
customer context once per audit:

```python
with cost_tracker.customer_context(customer_ctx.slug, customer_ctx.tier):
    findings = client.generate_findings(...)
    verdict  = client.generate_verdict(...)
    qsg      = client.generate_qsg(...)   # Full / Pro only
```

Each call appends one JSON line to
`data/ai_costs/<YYYY-MM-DD>.jsonl`:

```json
{
  "timestamp": "2026-05-26T01:15:42Z",
  "customer_id": "jane-sparkle",
  "tier": "Starter Package",
  "model": "claude-sonnet-4-5-20250929",
  "call_type": "finding_generation",
  "input_tokens": 8420,
  "output_tokens": 2150,
  "cost_usd": 0.0578,
  "latency_ms": 4280
}
```

The `customer_id` field is the slug Rob passes to `--slug` (e.g.
`jane-sparkle`). No emails, no URLs, no findings content land in this
file. See `SIMPLICITY-GUARDRAILS.md` §6.

The whole `data/ai_costs/*.jsonl` glob is gitignored - the directory
itself is committed via `.gitkeep` so the first run does not have to
create it.

`call_type` is one of: `finding_generation`, `qsg_generation`,
`verdict_generation`, `dedup_check`, `prescreen`, `other`.

---

## How to read the log

### Daily totals

```powershell
python scripts/ai_costs_report.py --date 2026-05-26
```

Prints total cost, call count, unique customer count, input / output
token totals, and p50 / p95 latency, plus breakdowns by model and by
call type.

### Per-customer breakdown

```powershell
python scripts/ai_costs_report.py --customer jane-sparkle
```

Aggregates every cost row tagged with that slug, across all daily
files. Shows tier, total cost, the cost-to-tier-price ratio (the
margin signal), call count, and call types.

### Period summary with margin analysis

```powershell
python scripts/ai_costs_report.py --summary --days 30
```

Outputs:

* Total AI cost over the window.
* Total revenue, preferring `data/customers.json` (delivered audits)
  and falling back to "one row per unique `customer_id` in the cost
  log" when the local tracker is empty / not yet wired up. The data
  source is printed alongside the number so you can tell which mode
  ran.
* Blended margin = (revenue - cost) / revenue.
* Average AI cost per Starter / Scale Up / Pro audit, plus the average
  as a percent of tier price.
* High-cost outliers (any customer whose cost exceeds 10% of their
  tier price).

The weekly task in `ROB-REMAINING-TODO.md` is:

> Run `python scripts/ai_costs_report.py --summary --days 7` and
> check margin > 70%.

If margin dips below 70%, see "What to do if margin drops" below.

### Alerts

```powershell
python scripts/ai_costs_report.py --alert --days 7
```

Prints (one per line) any of:

* `[high-cost-customer]` - per-customer cost > 20% of tier price.
  Thresholds: $3.80 Starter, $9.80 Scale Up, $19.80 Pro.
* `[daily-spend]` - any single day's total exceeds $50.
* `[runaway-calls]` - any customer with >15 calls in the window
  (almost always a prompt loop or retry storm; investigate the
  feedback log under `data/ai_feedback/<slug>.json`).

Stdout is structured so Rob can pipe it to Slack / email later. No
auto-send today by design - we are intentionally keeping this
hand-driven until volume justifies more automation.

---

## Current pricing assumptions and where to update them

The canonical table lives in
`scripts/ai_audit/cost_tracker.py` under `PRICING`:

| Model | Input ($/MTok) | Output ($/MTok) | Source |
|---|---|---|---|
| `claude-sonnet-4-5-20250929` (default) | 3.00 | 15.00 | platform.claude.com/docs |
| `claude-sonnet-4-6` | 3.00 | 15.00 | same |
| `claude-3-5-sonnet-20241022` (fallback) | 3.00 | 15.00 | same |
| `claude-opus-4-5-20250929` | 5.00 | 25.00 | same |
| `claude-haiku-4-5` | 1.00 | 5.00 | same |
| `gpt-4o` | 2.50 | 10.00 | developers.openai.com/api/docs/pricing |
| `gpt-4o-mini` | 0.15 | 0.60 | same |
| `gpt-4.1` / `gpt-4.1-mini` | 2.00 / 0.40 | 8.00 / 1.60 | same |
| `gpt-5-mini` | 0.25 | 2.00 | best-effort estimate (confirm at next bump) |

If a provider shifts prices, edit the `PRICING` dict and update the
date in the comment at the top of the dict. Unknown models fall back
to the Sonnet 4.5 rate with a one-time stderr warning so you notice
the gap. The pricing table deliberately ignores prompt caching and
the >200k long-context premium - both are not in use today; revisit
if either becomes relevant.

---

## Margin thresholds and what to do if margin drops

Target: AI cost stays under **2% of revenue** per audit (so blended
margin stays above ~70% once Rob's review time is factored back in).
Below 70% blended margin over 7 days, walk the levers below in order:

1. **Tier mix:** if 90% of customers are buying Starter, push the
   Scale Up upsell harder. `PRODUCT-DECISIONS.md` §7 already calls
   out the Free -> Starter -> Scale Up conversion funnel.
2. **Prompt size:** reduce the screenshot count
   (`pipeline.collect_screenshots(max_shots=8)`), drop the
   findings.csv reference from the user prompt, or lower
   `html_extract.TEXT_CAP`. Same three levers documented in
   `AI-AUDIT-PIPELINE.md`.
3. **Cheaper model for finding-generation:** route finding generation
   to `claude-haiku-4-5` or `gpt-4o-mini` while keeping Sonnet for
   verdict / QSG (which is where voice matters most). Override with
   `LAUNCHLOOK_CLAUDE_MODEL` or `LAUNCHLOOK_GPT_MODEL` in `.env`.
4. **Audit the high-cost outliers:** if one customer dominates the
   cost, their site probably tripped the regen / retry loop. Look at
   `data/ai_feedback/<slug>.json` for high `regen_count` values.

Do not change tier prices to fix margin. Prices are intentional and
discussed in `PRODUCT-DECISIONS.md` §7.

---

## Disabling the log (for tests / offline runs)

Set `LAUNCHLOOK_DISABLE_COST_LOG=1` in the environment. The pipeline
still runs end-to-end; nothing is appended to `data/ai_costs/`. Used
by the audit-UI unit tests so they do not pollute Rob's real cost log.

---

## Related docs

* `SIMPLICITY-GUARDRAILS.md` §6 - the rule that keeps cost data off
  customer surfaces.
* `PRODUCT-DECISIONS.md` §1, §7 - tier ladder and pricing rationale.
* `AI-AUDIT-PIPELINE.md` - upstream pipeline architecture and the
  "Cost expectations" table that this monitoring system enforces.
* `CUSTOMER-TRACKING.md` - the local customer tracker that the
  `--summary` mode reads for revenue truth.
