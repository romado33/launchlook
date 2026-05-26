# AI audit pipeline

**Last updated:** May 25, 2026
**Owner:** Rob
**Status:** Live as of this commit. The foundational shift from
manual-writing to AI-drafted + founder-curated audits.

The pipeline drops per-audit time from ~2 hours of hand-written findings
to ~15 minutes of spot-checking. The customer-facing deliverable
(`output/reports/{slug}/main-report.pdf` + `quick-start-guide.pdf`) is
completely unchanged. Only the path to get there is different.

---

## Architecture

```
            ┌──────────────────────────────────────────────────────┐
Customer    │                                                      │
URL  ─────► │  scripts/ai_audit.py                                 │
            │                                                      │
            │  1. Capture     scripts/capture_screenshots.py       │
            │     desktop + mobile PNGs                            │
            │     → output/customers/{slug}/screenshots/*.png      │
            │                                                      │
            │  2. Prescreen   scripts/prescreen_findings.py        │
            │     38 regex patterns from findings.csv              │
            │     → list[hit{finding,page,matches}]                │
            │                                                      │
            │  3. HTML        scripts/ai_audit/html_extract.py     │
            │     Playwright + BeautifulSoup, scripts stripped     │
            │     → list[page{title,meta,text,buttons,links}]      │
            │                                                      │
            │  4. LLM         scripts/ai_audit/llm_client.py       │
            │     Claude (vision + tool-use) or GPT (vision +      │
            │     json_schema). Sends screenshots + prescreen      │
            │     hits + HTML extracts + findings.csv reference    │
            │     + the system prompt (prompts/system.txt).        │
            │     Receives structured findings, verdict, QSG.      │
            │                                                      │
            │  5. YAML        scripts/audit_ui/yaml_writer.py      │
            │     Same emitter audit_ui uses, so the file          │
            │     round-trips cleanly back through audit_ui        │
            │     and deliver_report.py.                           │
            │     → customers/{slug}.yaml                          │
            │                                                      │
            └──────────────────────────────────────────────────────┘
                            │
                            ▼
            ┌──────────────────────────────────────────────────────┐
            │  scripts/audit_ui.py --review-ai                     │
            │                                                      │
            │  Loads customers/{slug}.yaml in "review mode".       │
            │  Per finding: Approve, Edit, Regenerate, Reject.    │
            │  Tracks every action in                              │
            │  data/ai_feedback/{slug}.json. "Approve all          │
            │  remaining & ship" rolls into deliver_report.py.     │
            └──────────────────────────────────────────────────────┘
                            │
                            ▼
            ┌──────────────────────────────────────────────────────┐
            │  scripts/deliver_report.py                           │
            │  Same PDF + Resend pipeline as before. Unchanged.    │
            └──────────────────────────────────────────────────────┘
```

---

## Setup (one-time)

```powershell
# Windows
pip install -r requirements-ai.txt
playwright install chromium  # already done if you've run capture_screenshots
```

Then add ONE of these to `.env`:

```dotenv
# Preferred (better at structured output + vision in our benchmarks)
ANTHROPIC_API_KEY=sk-ant-...

# Or fallback
OPENAI_API_KEY=sk-proj-...
```

`.env` is gitignored. Without a key set, the CLI exits with a clear
error. Use `--provider stub` to dry-run the wiring without an LLM.

Optional model overrides:

```dotenv
LAUNCHLOOK_CLAUDE_MODEL=claude-sonnet-4-5-20250929
LAUNCHLOOK_GPT_MODEL=gpt-4o
```

The client also tries known good fallbacks (`claude-3-5-sonnet-20241022`,
`gpt-4o-mini`) if the configured model 404s.

---

## Running it

### Starter Package, Claude (default)

```powershell
python scripts/ai_audit.py `
    --slug jane-smith `
    --url https://jane.lovable.app `
    --tier "Starter Package" `
    --builder Lovable `
    --name "Jane Smith" `
    --email jane@example.com `
    --app-name "Sparkle"
```

### Full Package, GPT-4o explicitly

```powershell
python scripts/ai_audit.py `
    --slug acme-pro `
    --url https://acme.bolt.host `
    --tier "Full Package" `
    --builder Bolt `
    --name "Pat Acme" `
    --email pat@acme.test `
    --app-name "Acme Pro" `
    --provider gpt
```

### Dry-run + skip stages (smoke testing)

```powershell
python scripts/ai_audit.py `
    --slug ai-test --url https://example.com `
    --tier "Starter Package" --builder Lovable `
    --name "Test" --email test@test.com --app-name "TestApp" `
    --provider stub --dry-run --skip-capture --skip-prescreen
```

`--provider stub` produces deterministic placeholder findings from
whatever the prescreener returned (or a single placeholder if the
prescreener was skipped). Useful for smoke tests and CI.

### After the YAML lands

```powershell
# 1. Spot-check in the UI (browser opens automatically)
python scripts/audit_ui.py --slug jane-smith --review-ai

# 2. In the UI: Approve / Edit / Regenerate / Reject each finding,
#    then click "✓ Approve all remaining & ship" in the footer.

# 3. Or, if you prefer the CLI, render PDFs without sending:
python scripts/deliver_report.py --customer customers/jane-smith.yaml --no-open

# 4. Or ship them via Resend:
python scripts/deliver_report.py --customer customers/jane-smith.yaml --send
```

---

## Adding a finding category (data-driven taxonomy)

The list of categories the LLM looks for is **data-driven**. Edit
`scripts/ai_audit/finding_categories.yaml`, do not edit the prompt:

```yaml
categories:
  - id: trust_gaps
    display_name_buyer: "trust signals & legal pages"
    display_name_internal: "Trust gaps"
    severity_default: medium
    description_for_llm: "Missing privacy policy, terms, contact info..."
    tester: "The Skeptic"
  # ...
  - id: cross_user_data
    display_name_buyer: "user data isolation"
    display_name_internal: "Cross-user data check"
    severity_default: high
    description_for_llm: "Scale Up and Pro tiers only..."
    tester: "The Snoop"
    tier_min: "Scale Up Package"   # gates by tier
```

At runtime, `pipeline.build_system_prompt(...)` loads this YAML, filters
out tier-restricted categories the customer's tier doesn't reach, and
substitutes `{{ categories_list }}` in `scripts/ai_audit/prompts/system.txt`.
The Webflow platform-conditional appendix architecture
(`PLATFORM_PROMPT_FILES` registry) is unchanged: per-platform
appendices and per-category prompt content compose **additively**.

To add a category:

1. Append a new `- id: ...` block to `finding_categories.yaml`.
2. Buyer-facing display name follows
   `docs/SIMPLICITY-GUARDRAILS.md` §6 (no internal jargon, no taxonomy
   codes; if a layperson wouldn't say it, don't put it here).
3. If the category is generated outside the LLM (e.g. by Snoop's
   `security_lite.py`) set `source: external` so the prompt tells the
   model not to regenerate it.
4. If the category should only apply at certain tiers, set `tier_min`
   to the lowest tier that should include it.

The buyer-facing display name is also what shows up in the report's
"What's working" / "Passed checks" section
(`templates/report/report.html.j2`). Categories with no critical / high
finding emit a passed-check line automatically; the buyer never sees
the internal taxonomy code.

---

## Snoop's security-lite checks

`scripts/ai_audit/security_lite.py` runs five deterministic checks
*before* the LLM finding-generation pass:

1. HSTS header presence (HTTPS sites only)
2. Content-Security-Policy header presence
3. X-Frame-Options (DENY or SAMEORIGIN)
4. X-Content-Type-Options nosniff
5. Exposed credentials and admin-route paths in the rendered HTML
   (AWS / Google / Stripe / Slack / private-key blocks; `/admin`,
   `/.env`, `/.git`, `/debug`, `/dev-tools` link hrefs)

Each finding is tagged `Caught by The Snoop` (per
`docs/TESTERS-CAST.md` §7 voice rules) and rendered with the persona
badge in the report PDF. Snoop's findings are **merged into the
final findings list before the cap is applied**, so a critical
exposed-credential finding can't be dropped because the LLM filled the
cap with lower-severity items.

The `security_lite` category in `finding_categories.yaml` carries
`source: external` so the LLM is told to merge incoming findings, not
regenerate them. When all five Snoop checks pass, the security-lite
category appears in the report's "What's working" section as
"obvious visible risks".

---

## Verdict labels (constrained vocabulary)

`scripts/ai_audit/prompts/verdict_generation.txt` constrains the LLM to
choose **exactly one** of four labels:

* `Ready to share` (🟢)
* `Safe for friends/family testing` (🟡)
* `Needs fixes before launch` (🔴)
* `Do not invite real users yet` (🔴)

The schema in `scripts/ai_audit/llm_client.py::VERDICT_SCHEMA` enforces
the four-value enum at the API boundary. `pipeline._normalize_verdict`
coerces any drift (missing label, wrong casing, an extra trailing
period) back to one of the four canonical values before the YAML is
written, so the report template can render deterministically. The label
becomes the hero phrase under the report title; the `summary` is the
1-line tagline beneath it.

---

## Prompt iteration

Every prompt lives in `scripts/ai_audit/prompts/`. Iterate on these
without code changes:

| File | Purpose |
|------|---------|
| `system.txt` | Voice, severity definitions, fix-prompt rules, few-shot examples, forbidden patterns. The big one. |
| `finding_generation.txt` | User-prompt template: customer context, tier guidance, screenshot count, prescreener hits, HTML extracts, findings library reference. |
| `qsg_generation.txt` | User-prompt template for Quick Start Guide (Full Package only). |
| `verdict_generation.txt` | User-prompt template for the emoji + summary + narrative. |

The python templates use `str.format(...)`, so prompt placeholders use
`{var}` syntax. If you add a new placeholder, also add the matching
keyword in `scripts/ai_audit/pipeline.py` (`build_finding_user_prompt`,
`build_qsg_user_prompt`, or `build_verdict_user_prompt`).

**When iterating on the system prompt**, the highest-leverage things to
tune (in order):

1. The severity definitions (Rob's edits cluster around severity drift).
2. The forbidden-patterns section (em-dashes especially).
3. The few-shot examples (replace with your best real audits as you ship
   more customers).
4. The fix-prompt-by-builder section (refine per platform).

---

## Quality feedback loop

Every AI-drafted audit logs to `data/ai_feedback/{slug}.json` (gitignored).
Each record captures:

* When the AI generated the draft (`ai_generated_at`).
* Provider + model used.
* When Rob finished review (`reviewed_at`).
* Per-finding actions: `approved` / `edited` / `rejected` /
  `regenerated`, with the AI's original title/severity for diffing.

Read aggregated stats:

```powershell
python scripts/ai_audit/feedback_summary.py
# or filter to recent drafts
python scripts/ai_audit/feedback_summary.py --since 2026-05-01
```

The summary prints:
* Drafts reviewed, total findings, provider mix.
* Approve % (no edits), edit %, reject %, average regen rate.
* Severity drift (`high→medium` etc).
* Most-rejected titles (top 10) → prompt patterns to add to the
  "Do not generate findings like this" section.
* Edited title pairs (AI → final) → tone hints for system.txt.

Use this every 5-10 customers to refine the prompts. The first round of
real data will probably show:
* AI calibrates severity too high (Rob bumps `critical→high`).
* AI invents fix prompts referencing files it didn't see (banned by
  system.txt but watch for drift).
* AI uses em-dashes despite the prohibition (re-emphasize in system.txt).

---

## Cost tracking (every call is logged)

Every Anthropic / OpenAI call the pipeline makes is wrapped with
`scripts/ai_audit/cost_tracker.track_call(...)` and gets one JSON line
appended to `data/ai_costs/<YYYY-MM-DD>.jsonl` (gitignored). The line
records customer slug, tier, model, call type, token counts, latency,
and computed USD cost. The `pipeline.run(...)` body wraps the LLM
stages in `cost_tracker.customer_context(slug, tier)` so the LLM
client does not need extra arguments.

Read the log with `python scripts/ai_costs_report.py`. The full
docs are at `docs/AI-COST-MONITORING.md`.

Cost data is internal-only per `SIMPLICITY-GUARDRAILS.md` A6 - it
never crosses into a customer-facing surface.

---

## Cost expectations (approximate)

Per audit (Starter Package, ~8 screenshots, 5 HTML extracts, 5 findings):

| Provider | Model | Approx input / output tokens | Approx cost |
|----------|-------|------------------------------|-------------|
| Claude   | `claude-sonnet-4-5-20250929` | ~25k in / ~3k out (3-shot + 8 images) | **$0.10 to $0.25** |
| Claude   | `claude-opus-4-5-20250929` | ~25k in / ~3k out | ~$0.50 to $1.20 |
| GPT      | `gpt-4o` | ~22k in / ~3k out (8 images) | **$0.08 to $0.20** |
| GPT      | `gpt-4o-mini` | ~22k in / ~3k out | ~$0.03 to $0.08 |
| GPT      | `gpt-5-mini` (if available) | similar to 4o-mini | ~$0.04 to $0.10 |

Full Package adds a second LLM call (the QSG generator with ~4
screenshots and a smaller HTML payload), roughly **+50%** on the
Starter base.

At $9 Starter / $29 Full, AI cost is roughly **1 to 3% of revenue**.
That leaves the founder's 15-minute review (the real cost) as the
bottleneck, which is exactly where the strategy wanted it.

If the LLM bill creeps up, the levers (in order) are:
* Reduce the number of screenshots sent (currently 8 max).
* Drop the findings.csv reference from the user prompt (~1k tokens).
* Cap HTML text extraction lower (`TEXT_CAP` in `html_extract.py`).

---

## Adding a new builder

The fix-prompt voice differs per builder (Lovable speaks
natural-language, v0 wants component paths, etc). To add a new platform:

1. `scripts/audit_ui/yaml_writer.py` → add to `VALID_BUILDERS`.
2. `scripts/audit_ui.py` → add to the `--builder` choices.
3. `scripts/ai_audit/prompts/system.txt` → add a paragraph under
   "FIX PROMPT TONE BY BUILDER" describing the new platform's
   conventions.
4. Update the landing page (`landing/index.html`) and the outreach
   playbook (`docs/OUTREACH-PLAYBOOK.md`) if the new builder needs
   surface mention.

No code changes in `llm_client.py` or `pipeline.py` are required.

---

## Review UI (`audit_ui.py --review-ai`)

`--review-ai` flips the audit UI from data-entry mode into spot-check
mode. The changes:

* A banner at the top: "AI-generated draft. Review and approve each
  finding before shipping."
* Each finding card shows Approve, Regenerate, and Reject buttons
  at the top right. Editing any field marks the finding as `edited`.
* A `{n} / {total} reviewed` counter in the banner tracks progress.
* The sticky footer's deliver button becomes "✓ Approve all remaining
  & ship" (confirms, then runs the same generate-yaml + deliver-with-
  --send flow).
* Every Rob action POSTs to `/api/feedback`, which writes to
  `data/ai_feedback/{slug}.json`.
* "Regenerate" POSTs to `/api/regenerate-finding`, which calls
  `scripts.ai_audit.pipeline.regenerate_finding` with a hint to produce
  a different finding. Returns the replacement dict; the UI swaps it
  in place and resets that finding's state to `draft`.

---

## Troubleshooting

### "ERROR: no LLM API key found"

Add `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` to `.env`. Or pass
`--provider stub` to dry-run.

### "Claude returned no tool_use block"

Anthropic occasionally returns text rather than the requested tool
call. The client retries through model fallbacks. If all fail, the
process exits and the YAML is not written. Re-run with `--provider gpt`
as the immediate workaround.

### Rate limits (429)

Both providers backoff differently. The pipeline does not currently
auto-retry rate limits (it's a one-customer-per-run script). If you
hit a 429, wait 60 seconds and rerun. We can add retry/backoff if it
becomes a real issue at scale.

### "Vision input too large"

Caps live in `pipeline.collect_screenshots(max_shots=8)` and
`html_extract.TEXT_CAP = 6000`. Lower either if a particularly
large customer trips the per-request token limit.

### AI hallucinates findings unrelated to the screenshots

This is the founder review's job to catch. When it happens:
1. Reject the finding in the UI (logs to feedback).
2. Run `feedback_summary.py` to see if the same hallucinated title
   appears across customers.
3. If yes, add an explicit "do not generate findings like X" line to
   `prompts/system.txt`'s "Forbidden patterns" section.

### "AI uses em-dashes again"

The system prompt explicitly forbids em-dashes (they're Rob's #1 AI-
tell). If the model regresses, strengthen the language in
`prompts/system.txt`'s tone section. Last resort: add a regex pass at
the end of `pipeline.run()` that replaces em-dashes with colons before
YAML emission.

### Founder review caught nothing: should I trust it more?

For the first 20 customers, no. The current calibration was tuned
against Rob's example YAMLs. Real data from `feedback_summary.py`
should drive the next round of prompt edits. Trust grows with measured
approval rates.

---

## Canonical finding-category taxonomy

The data-driven category list lives in
`scripts/ai_audit/finding_categories.yaml`. The pipeline loads it at
runtime and renders `{{ categories_list }}` into `system.txt`
(`pipeline.build_system_prompt(...)` calls `load_finding_categories()`
then `render_categories_for_prompt(..., tier=tier)`). To add or retire
a category, edit the YAML; do not hardcode category language in the
prompt. Buyer-facing display names are governed by
`docs/SIMPLICITY-GUARDRAILS.md` §6 (no internal taxonomy on customer
surfaces).

The `tier_min` field gates visibility: a category is excluded from the
prompt for any tier below its `tier_min`. The tier rank order is
`Starter Package` (1), `Scale Up Package` (2), `Pro Package` (3).
Free-tier audits cap at 3 findings total across all categories and
are filtered after generation, not at the category-list step.

Active category IDs (as of q3b, May 26 2026):

| ID | Buyer-facing display name | Tester | tier_min | Source |
|---|---|---|---|---|
| `trust_gaps` | trust signals & legal pages | The Skeptic | — | llm |
| `broken_ctas_links` | broken buttons & dead links | The Klutz | — | llm |
| `mobile_layout` | mobile layout issues | The Phone-First Friend | — | llm |
| `copy_clarity` | confusing or placeholder text | The Tourist | — | llm |
| `dev_artifacts` | dev tools and test data on the live site | The Klutz | — | llm |
| `security_lite` | obvious visible risks | The Snoop | — | external (Snoop) |
| `cross_user_data` | user data isolation | The Snoop | Scale Up Package | llm |
| `ai_sounding_copy` | copy that sounds AI-written | The Tourist | — | llm |
| `scale_ready_audit` | growth-readiness checks | The Snoop | Scale Up Package | llm |
| `compliance_lite` | common legal must-haves | The Skeptic | — | llm |

When you add a new category, also list it here (ID + buyer-facing
display name + tester + `tier_min` if any + source) so the canonical
list stays a one-stop read.

---

## Related docs

* `docs/MANUAL-REVIEW-WORKFLOW.md`: the previous (pre-AI) workflow,
  kept for reference.
* `docs/DELIVERY-PIPELINE.md`: what happens after the YAML lands
  (PDF render, Resend email).
* `docs/06-findings-library.md`: the 38 patterns the prescreener
  matches against and the LLM uses as calibration.
* `scripts/ai_audit/prompts/system.txt`: the prompt itself. Read it
  before iterating.
