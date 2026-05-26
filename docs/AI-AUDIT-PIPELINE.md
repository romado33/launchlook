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
            â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
Customer    â”‚                                                      â”‚
URL  â”€â”€â”€â”€â”€â–º â”‚  scripts/ai_audit.py                                 â”‚
            â”‚                                                      â”‚
            â”‚  1. Capture     scripts/capture_screenshots.py       â”‚
            â”‚     desktop + mobile PNGs                            â”‚
            â”‚     â†’ output/customers/{slug}/screenshots/*.png      â”‚
            â”‚                                                      â”‚
            â”‚  2. Prescreen   scripts/prescreen_findings.py        â”‚
            â”‚     38 regex patterns from findings.csv              â”‚
            â”‚     â†’ list[hit{finding,page,matches}]                â”‚
            â”‚                                                      â”‚
            â”‚  3. HTML        scripts/ai_audit/html_extract.py     â”‚
            â”‚     Playwright + BeautifulSoup, scripts stripped     â”‚
            â”‚     â†’ list[page{title,meta,text,buttons,links}]      â”‚
            â”‚                                                      â”‚
            â”‚  4. LLM         scripts/ai_audit/llm_client.py       â”‚
            â”‚     Claude (vision + tool-use) or GPT (vision +      â”‚
            â”‚     json_schema). Sends screenshots + prescreen      â”‚
            â”‚     hits + HTML extracts + findings.csv reference    â”‚
            â”‚     + the system prompt (prompts/system.txt).        â”‚
            â”‚     Receives structured findings, verdict, QSG.      â”‚
            â”‚                                                      â”‚
            â”‚  5. YAML        scripts/audit_ui/yaml_writer.py      â”‚
            â”‚     Same emitter audit_ui uses, so the file          â”‚
            â”‚     round-trips cleanly back through audit_ui        â”‚
            â”‚     and deliver_report.py.                           â”‚
            â”‚     â†’ customers/{slug}.yaml                          â”‚
            â”‚                                                      â”‚
            â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                            â”‚
                            â–¼
            â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
            â”‚  scripts/audit_ui.py --review-ai                     â”‚
            â”‚                                                      â”‚
            â”‚  Loads customers/{slug}.yaml in "review mode".       â”‚
            â”‚  Per finding: Approve, Edit, Regenerate, Reject.    â”‚
            â”‚  Tracks every action in                              â”‚
            â”‚  data/ai_feedback/{slug}.json. "Approve all          â”‚
            â”‚  remaining & ship" rolls into deliver_report.py.     â”‚
            â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                            â”‚
                            â–¼
            â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
            â”‚  scripts/deliver_report.py                           â”‚
            â”‚  Same PDF + Resend pipeline as before. Unchanged.    â”‚
            â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
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

### Pro Package, Claude

```powershell
python scripts/ai_audit.py `
    --slug mira-tessera `
    --url https://tessera.lovable.app `
    --tier "Pro Package" `
    --builder Lovable `
    --name "Mira Okafor" `
    --email mira@example.com `
    --app-name "Tessera Boards"
```

The Pro Package prompt extends the Full Package guidance with a
dedicated integrations review (Stripe / auth / email / analytics).
Findings are still emitted in the standard `findings` list â€” there is
no separate `integrations_review` YAML key. Prefix integrations-flavored
finding titles with `Integrations:` so they group visibly in the PDF
(see `customers/example-pro-package.yaml` for the canonical pattern).
The 30-minute Loom walkthrough is a separate scheduling step, not a
YAML field.

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
#    then click "âœ“ Approve all remaining & ship" in the footer.

# 3. Or, if you prefer the CLI, render PDFs without sending:
python scripts/deliver_report.py --customer customers/jane-smith.yaml --no-open

# 4. Or ship them via Resend:
python scripts/deliver_report.py --customer customers/jane-smith.yaml --send
```

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
* Severity drift (`highâ†’medium` etc).
* Most-rejected titles (top 10) â†’ prompt patterns to add to the
  "Do not generate findings like this" section.
* Edited title pairs (AI â†’ final) â†’ tone hints for system.txt.

Use this every 5-10 customers to refine the prompts. The first round of
real data will probably show:
* AI calibrates severity too high (Rob bumps `criticalâ†’high`).
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

Cost data is internal-only per `SIMPLICITY-GUARDRAILS.md` Â§6 - it
never crosses into a customer-facing surface.

---

## Cost expectations (approximate)

Per audit (Starter Package, ~8 screenshots, 5 HTML extracts, ~7 findings):

| Provider | Model | Approx input / output tokens | Approx cost |
|----------|-------|------------------------------|-------------|
| Claude   | `claude-sonnet-4-5-20250929` | ~25k in / ~3k out (3-shot + 8 images) | **$0.10 to $0.25** |
| Claude   | `claude-opus-4-5-20250929` | ~25k in / ~3k out | ~$0.50 to $1.20 |
| GPT      | `gpt-4o` | ~22k in / ~3k out (8 images) | **$0.08 to $0.20** |
| GPT      | `gpt-4o-mini` | ~22k in / ~3k out | ~$0.03 to $0.08 |
| GPT      | `gpt-5-mini` (if available) | similar to 4o-mini | ~$0.04 to $0.10 |

Full Package adds a second LLM call (the QSG generator with ~4
screenshots and a smaller HTML payload), roughly **+50%** on the
Starter base. Pro Package adds the same QSG call plus a longer
finding-generation prompt (40-cap output and the integrations-review
guidance), roughly **+100%** on the Starter base.

At $19 Starter / $49 Full / $99 Pro, AI cost is roughly **1 to 2% of
revenue** across all tiers. That leaves the founder's 15-minute review
(the real cost on Starter / Full) and the 30-minute Loom (Pro only)
as the bottlenecks, which is exactly where the strategy wanted it.

If the LLM bill creeps up, the levers (in order) are:
* Reduce the number of screenshots sent (currently 8 max).
* Drop the findings.csv reference from the user prompt (~1k tokens).
* Cap HTML text extraction lower (`TEXT_CAP` in `html_extract.py`).

---

## Adding a new builder

The fix-prompt voice differs per builder (Lovable speaks
natural-language, v0 wants component paths, etc). To add a new platform:

1. `scripts/audit_ui/yaml_writer.py` â†’ add to `VALID_BUILDERS`.
2. `scripts/audit_ui.py` â†’ add to the `--builder` choices.
3. `scripts/ai_audit/prompts/system.txt` â†’ add a paragraph under
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
* The sticky footer's deliver button becomes "âœ“ Approve all remaining
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
`docs/SIMPLICITY-GUARDRAILS.md` Â§6 (no internal taxonomy on customer
surfaces).

The `tier_min` field gates visibility: a category is excluded from the
prompt for any tier below its `tier_min`. The tier rank order is
`Starter Package` (1) â†’ `Scale Up Package` (2) â†’ `Pro Package` (3).
Free tier audits cap at 3 findings total across all categories and
are filtered after generation, not at the category-list step.

Active category IDs (as of q14+q16, May 26 2026):

| ID | Buyer-facing display name | Tester | tier_min | Source |
|---|---|---|---|---|
| `trust_gaps` | trust signals & legal pages | The Skeptic | â€” | llm |
| `broken_ctas_links` | broken buttons & dead links | The Klutz | â€” | llm |
| `mobile_layout` | mobile layout issues | The Phone-First Friend | â€” | llm |
| `copy_clarity` | confusing or placeholder text | The Tourist | â€” | llm |
| `dev_artifacts` | dev tools and test data on the live site | The Klutz | â€” | llm |
| `security_lite` | obvious visible risks | The Snoop | â€” | external (Snoop) |
| `cross_user_data` | user data isolation | The Snoop | Scale Up Package | llm |
| `ai_sounding_copy` | copy that sounds AI-written | The Tourist | â€” | llm |
| `scale_ready_audit` | growth-readiness checks | The Snoop | Scale Up Package | llm |
| `compliance_lite` | common legal must-haves | The Skeptic | â€” | llm |
| `performance_speed` | performance & speed | The Phone-First Friend | â€” | external (PSI) |
| `accessibility_checks` | accessibility checks | The Phone-First Friend | â€” | external (axe-core) |
| `form_submit_smoke` | form & signup flows | The Stranger Who Tried to Sign Up | â€” | external (form_smoke_test) |

When you add a new category, also list it here (ID + buyer-facing
display name + tester + `tier_min` if any + source) so the canonical
list stays a one-stop read.

---

## Free â†’ Starter deduplication

When a buyer used the free 3-finding hook and then upgrades to Starter
for the same email + URL within 90 days, the paid pipeline MUST surface
**10 NEW findings**, excluding the prior 3. This is non-negotiable per
`docs/PRODUCT-DECISIONS.md` Â§2: the Free â†’ Starter conversion is the
funnel's most fragile moment; re-reading the free preview would burn it.

### How it works in the pipeline

1. `scripts/ai_audit/free_audit_lookup.load_excluded_fingerprints(...)`
   queries the Notion **Free Audit Requests DB**
   (`NOTION_FREE_AUDIT_DB_ID`) for the most recent row matching
   `(email, URL host, within 90 days)`. It pulls the
   `Finding Fingerprints` rich-text column and parses out the
   semicolon-separated hashes. Optional `Finding Summaries` get parsed
   too (newline-separated, one short summary per prior finding).
2. `scripts/ai_audit/dedup.render_exclude_block(fps, summaries)`
   renders an `### EXCLUDE_FINGERPRINTS` block that the pipeline
   appends to the finding-generation user prompt. The LLM is told NOT
   to re-surface them.
3. After generation + sort + cap, `dedup.collisions(...)` checks
   whether any survived. If yes, the pipeline re-prompts the LLM once
   with a `### COLLISION_RETRY` hint listing the colliding titles and
   asking for replacements. The fresh findings get filtered through
   the same collision check; anything that still collides is dropped.
   If we still can't fill the cap, the pipeline logs a warning and
   ships anyway (soft constraint per the q4 task spec).

### Where the fingerprints come from

The free-audit Notion row stores `Finding Fingerprints` AFTER Rob
approves the 3 free findings via the audit UI. The helper
`free_audit_lookup.persist_free_audit_fingerprints(row_id, fps, summaries)`
writes them back. Hook it from the free-tier deliver step (queued in
`ROB-REMAINING-TODO.md` until that script lands; in the meantime Rob
copies the hashes from the pipeline log into the Notion column by hand).

### Fingerprint shape

`hashlib.sha256(category_id + url_path + normalized_description)`
truncated to 16 hex chars (64 bits). See `scripts/ai_audit/dedup.py`
docstring for the rationale and stability guarantees (wording drift,
trailing-slash path canonicalization, case-insensitive description).
Tests live in `tests/test_dedup.py` (3 main cases + 6 edge cases).

### Customer-visible boundary

Per `docs/SIMPLICITY-GUARDRAILS.md` Â§6 the dedup mechanism never
crosses into customer copy. If a customer asks, the answer is "your
Starter findings build on your free preview." Never "deduplication,"
"fingerprints," "exclude block," or "collision retry."

### Why we chose Notion over a separate datastore

The Notion free-audit DB is the same surface Rob already opens to
clear the queue (per `docs/FREE-AUDIT-WORKFLOW.md` Â§3). Storing the
fingerprints there means: one place to manage abuse, dedup, status,
and delivery state. A future worker can move this to a real datastore
once volume justifies the complexity (no fixed trigger yet).

---

## GitHub integration (Pro tier opt-in)

Pro Package customers can opt into having their findings auto-created
as GitHub issues on their repo, with optional PR comment. The
integration is **opt-in, manually triggered by Rob**, and never
auto-runs from `deliver_report.py`. The delivery script only logs a
one-line reminder when a Pro customer has a `github:` block in their
YAML. Full setup + invocation + failure-recovery docs at
`docs/GITHUB-INTEGRATION.md`. Library lives at
`scripts/github_integration.py`; the thin CLI is
`scripts/github_push.py`.

---

## Performance & speed (Core Web Vitals translator)

`scripts/ai_audit/performance_speed.py` runs alongside Snoop and
calls the PageSpeed Insights v5 API for the customer's homepage. The
free anonymous quota is 25 req/100s shared; set `PSI_API_KEY` in
`.env` for the per-project 25,000 req/day budget (key is optional,
the pipeline falls back to anonymous with retry-on-429 backoff).

Responses cache for 24h per (url, mobile/desktop) in
`data/psi_cache/<hash>.json` (gitignored) so test runs and re-runs of
the same customer never burn the daily quota. Override the TTL with
the `PSI_CACHE_TTL_SECONDS` env var if you need a faster local loop.

Each Core Web Vital is translated into a plain-English finding:

| Internal metric | Buyer-facing dimension |
|---|---|
| LCP (Largest Contentful Paint) | how fast the main image or headline shows up |
| INP (Interaction to Next Paint) | how fast the page reacts to a tap or click |
| CLS (Cumulative Layout Shift) | how much things jump around as the page loads |

The customer NEVER sees the internal acronyms (LCP / INP / CLS) or
the phrase "Core Web Vitals" anywhere on a customer surface, per
`docs/SIMPLICITY-GUARDRAILS.md` section 6. The buyer-facing display
name for the whole category is "performance & speed".

Findings are tier-capped inside `translate_to_findings`:

| Tier | Findings exposed |
|---|---|
| Starter Package | 1 (worst-rated metric only) |
| Scale Up Package | up to 3 (one per metric) |
| Pro Package | full breakdown |

Fix prompts are pre-generated per (metric Ã— platform) and live in
`_FIX_PROMPT_LIBRARY` inside `performance_speed.py`. Supported
builders: Lovable, Bolt, v0, Cursor, Webflow, plus a generic
fallback. We never ask the LLM to draft these prompts: deterministic
templates keep cost flat and tone consistent.

When all three metrics return GOOD (or PSI has no field data for the
URL and we don't know), the category does NOT roll into the report's
"What's working" section unless the runner explicitly returned a
non-empty `passed_check_ids` list (mirrors the Snoop gate). Silence
is not certification.

---

## Accessibility checks (axe-core)

`scripts/ai_audit/accessibility_axe.py` injects axe-core (pinned at
`4.10.0` via the unpkg CDN) into a headless Playwright tab pointed at
the customer's homepage, runs the WCAG 2.1 AA rule subset, and rolls
the violations into five buyer-facing buckets:

| Internal bucket | Buyer-facing finding title |
|---|---|
| `image_alt` | Some images on your site have no description for screen readers |
| `color_contrast` | Some text on your site is hard to read against its background |
| `form_label` | Some form fields on your site don't tell screen readers what to type |
| `button_name` | Some buttons on your site have no readable text |
| `keyboard` | Some interactive parts of your site can't be reached with the Tab key |

Customer-facing copy never says "axe-core", "WCAG", "aria-label", or
"a11y" per `docs/SIMPLICITY-GUARDRAILS.md` section 6. The
buyer-facing display name for the whole category is
"accessibility checks".

Findings are tier-capped (1 / 3 / all) the same way as performance &
speed. Fix prompts are pre-generated per (bucket Ã— platform); the
same builder set as `performance_speed.py` (Lovable, Bolt, v0, Cursor,
Webflow, generic).

When Playwright is not installed or the headless run can't reach the
URL, `run_accessibility_axe(...)` returns
`{"ran": False, ...}` and the pipeline still produces a YAML. Axe
results are cached for 24h per URL in `data/axe_cache/<hash>.json`
(gitignored) so re-runs don't re-launch Chromium.

---

## Form-submit smoke test (The Stranger)

`scripts/ai_audit/form_smoke_test.py` is The Stranger Who Tried to
Sign Up's runner. It re-uses the Playwright capture pattern (same
shape as q14 and q16) to: detect `<form>` elements, fill each with
safe synthetic values from `SYNTHETIC_VALUES` (every value labelled
"LaunchLook smoke test" so the customer can spot the rows in their
inbox or database), submit, and watch the page for a thank-you
state, redirect, error toast, validation message, or silent no-op.

The buyer-facing display name for the whole category is
"form & signup flows". The strings "form-submit smoke test",
"synthetic values", and "round-trip" never appear on a customer
surface per `docs/SIMPLICITY-GUARDRAILS.md` section 6; the finding
voice is The Stranger's (bemused, patient, "I tried to do the thing
your page asked me to do").

Tier-cap (same shape as performance + accessibility):

| Tier | Findings exposed |
|---|---|
| Starter Package | 1 (worst form) |
| Scale Up Package | up to 3 |
| Pro Package | full breakdown |

### Safety guardrails

The smoke test submits real forms on the customer's live site. The
runner is conservative about what it touches:

* **Payment / checkout forms are skipped.** Any form whose selector,
  id, name, action URL, parent class list, or field names match the
  payment-token list (`stripe`, `paypal`, `card_number`, `cvv`,
  `checkout`, `billing`, etc.) gets a finding ("We saw your checkout
  form but didn't submit it â€” we don't want to accidentally place a
  real order") but never a fill / submit.
* **Destructive-label forms are skipped.** Submit buttons reading
  `Delete`, `Cancel subscription`, `Unsubscribe me`, `Close my
  account` (etc.) also short-circuit to a skip finding.
* **Hard cap of 3 forms per audit.** Even on Pro, the runner never
  submits more than 3 forms per page. Limits blast radius.
* **No repeat submits.** A form that's already been submitted in
  this run won't be re-detected (Playwright reloads between forms).
* **Synthetic values label themselves.** Every fillable text input
  carries "LaunchLook smoke test" or its component, so the customer
  can grep their inbox and database for rows we generated.

### Opt-out + selector blocklist (customer YAML)

A customer can opt out of the runner or block specific selectors
from ever being submitted by adding a `form_smoke_test:` block to
their customer YAML alongside the `customer:` block. Both knobs are
optional and default to safe values:

```yaml
form_smoke_test:
  enabled: false              # default true; set false to skip the runner entirely
  blocked_forms:               # selectors the runner must never submit
    - "#prod-checkout"
    - "form[action='/api/real-money']"
  customer_email: stranger+launchlook@example.com  # Pro-tier round-trip target
```

`pipeline._form_smoke_config(...)` reads the block lazily so we don't
drag YAML state through every layer. Missing block = defaults applied
(runner enabled, no blocked selectors, no customer email override).

### Pro-tier email round-trip

When the customer's tier is `Pro Package`, the runner additionally
polls a disposable mailbox (`scripts/ai_audit/disposable_mailbox.py`,
mail.tm by default) for up to 60 seconds after each email-capturing
form submits. If the confirmation email arrives, the form "passes"
its check; if not, we surface a "Your signup flow didn't trigger a
confirmation email within 60 seconds" finding. The mailbox API is
externally hosted; we fall back gracefully (no finding, no crash,
just a stderr warning) when the provider is unreachable.

### Falls back when Playwright is missing

When the Playwright dependency isn't installed, the headless run
can't reach the URL, or the customer opted out, the runner returns
`{"ran": False, ...}` with empty findings and an empty
`passed_check_ids`. The pipeline still produces a YAML; we just
don't get to claim "your forms work" if we never submitted them.

### Builder-specific fix prompts

Fix prompts are pre-generated per `(failure type Ã— platform)` in the
`_FIX_PROMPT_LIBRARY` inside `form_smoke_test.py`. The supported
builders mirror q14 + q16: Lovable, Bolt, v0, Cursor, Webflow, plus
a generic fallback. We never ask the LLM to draft these prompts.

---

## AI-builder deep links in QSG (Pro Package)

`templates/qsg/qsg.html.j2` renders each Quick Start Guide step with
an "Open this in your AI builder" action row when
`customer.tier == "Pro Package"`. The row contains real PDF
hyperlinks that open the customer's AI builder with the step body
URL-encoded as the chat prompt:

| Builder | Deep-link scheme used |
|---|---|
| Bolt | `https://bolt.new/?q={encoded_prompt}` |
| v0 | `https://v0.app/chat?q={encoded_prompt}` |
| Cursor | `cursor://anysphere.cursor-deeplink/prompt?text={encoded_prompt}` |
| Lovable | `https://lovable.dev/` (no native chat deep link; opens the dashboard so the buyer can paste) |
| Webflow | `https://webflow.com/dashboard` (no AI deep link; opens the Designer) |

The customer's own builder gets the primary (filled) button style;
the others render with the secondary outline style so the buyer's
default tool is the obvious next click. The "Copy" pill is a visual
cue that the step body above is copyable (PDF readers don't expose a
JS clipboard; the buyer selects and copies the text directly).

Pro tier audits also pick up a "How to apply these prompts in one
pass" appendix tailored to the customer's builder. This appendix is
Pro-only and gated by the same `customer.tier` Jinja conditional.

Per `docs/SIMPLICITY-GUARDRAILS.md` section 6 + section 2.5
("Integrations stay invisible on the main landing"), the deep-link
feature is **never** marketed on `landing/index.html` or
`landing/webflow.html`. It is a delivery-only delight that appears
inside the PDF after purchase.

---

## Verified badge generation (post-delivery)

q17 added a small "LaunchLook Verified" badge that ships with every
paid tier. The badge is **not** part of the audit pipeline itself - it
is a post-delivery step Rob runs once the report has been emailed and
the customer has signed off (or after the 7-day refund window, if Rob
prefers to wait).

The flow:

1. Rob receives the Stripe checkout event (already routed via
   `api/stripe-webhook.py`).
2. Rob runs `python scripts/ai_audit.py --customer customers/{slug}.yaml`
   to produce the YAML + PDFs as usual.
3. **New step**: Rob runs `python scripts/generate_verified_badge.py
   --customer customers/{slug}.yaml` to mint the badge assets and the
   `verify.json` record. Output paths:
   * `landing/images/badges/{slug}/light.svg` + `.png`
   * `landing/images/badges/{slug}/dark.svg` + `.png`
   * `landing/data/verified/{slug}.json`
4. Vercel deploy picks these up on the next push. The delivery email
   / report PDF already reference the same URLs, so once the assets
   land on prod the customer's embed snippet is live.

For `` badge re-verifications, the same script is run with
`--re-verify`. See `docs/VERIFIED-BADGE-WORKFLOW.md` for the full
runbook, including the operator guardrail that prevents a misfired
`` re-verify from issuing a badge to a customer who never had one.

---

## Related docs

* `docs/FREE-AUDIT-WORKFLOW.md`: daily flow for the free 3-finding
  hook â€” queue triage, manual pipeline run, dedup write-back, abuse
  watch.
* `docs/MANUAL-REVIEW-WORKFLOW.md`: the previous (pre-AI) workflow,
  kept for reference.
* `docs/DELIVERY-PIPELINE.md`: what happens after the YAML lands
  (PDF render, Resend email).
* `docs/GITHUB-INTEGRATION.md`: the Pro-only, opt-in, manually-
  triggered post-delivery step that turns findings into GitHub issues.
* `docs/06-findings-library.md`: the 38 patterns the prescreener
  matches against and the LLM uses as calibration.
* `scripts/ai_audit/prompts/system.txt`: the prompt itself. Read it
  before iterating.

## Handoff Report (Pro tier + $99 add-on)

After the main audit YAML is generated, an optional pass produces a Handoff Report: a separate Markdown + PDF deliverable formatted for the developer the customer hires next. It reuses the same findings, verdict and passed_checks the main report does -- nothing is re-audited.

Three short LLM calls generate the narrative pieces:

1. `handoff_context_paragraph.txt` -> one plain-English paragraph describing the site, the builder, the customer, and what shape it's in.
2. `handoff_recommended_order.txt` -> a short numbered list of fixes in the order an experienced developer would tackle them.
3. `handoff_code_review_notes.txt` -> Pro tier only; 3 to 5 architecture or integration concerns that aren't surface findings.

Entry point: `scripts.ai_audit.pipeline.run_handoff_report(...)`. Delivered via `scripts/deliver_report.py --handoff-report`. The report is gated by paid tier (free on Pro, paid add-on on Starter and Scale Up); the Pro-only code-review section is gated inside the template by the `tier == "Pro Package"` check.
