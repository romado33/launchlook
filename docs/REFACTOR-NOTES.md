# Refactor Notes — q-final-lint (May 26, 2026)

Single-doc summary of everything `q-final-lint` did between `181d300` (q-final-audit) and the launch commit. This is the LAST worker before Rob wakes up. Goal: lint clean, q18 regression fixed, customer-facing copy aligned with `SIMPLICITY-GUARDRAILS.md` §6, smoke tests green, repo shipping-ready.

Cites: `SIMPLICITY-GUARDRAILS.md` §6 (forbidden vocab + em-dash rule), `PRODUCT-DECISIONS.md` §1 (canonical tier ladder: Starter cap 10, Scale Up cap 30), `CONSISTENCY-AUDIT-REPORT.md` (the punch list q-final-audit produced).

---

## 1. Linters that ran + auto-fixes applied

| Tool | Scope | Result | Auto-fixes |
|---|---|---|---|
| `ruff check --fix` | `scripts/ scripts/ai_audit/ tests/ api/ lib/` | clean (2 harmless `WPS433` noqa warnings, flake8-wps codes that ruff doesn't recognise) | unused imports, import sorting (`I001`), `datetime.UTC` modernisation (`UP017`), ambiguous variable names (`E741`), dead variables (`F841`) |
| `black` | same scope, line-length 100 (project default in `pyproject.toml`) | clean (62 files unchanged after a 3-file reformat pass) | reformatted `scripts/ai_audit/html_extract.py`, `scripts/ai_audit/pipeline.py`, `scripts/share_report.py` |
| `mypy --follow-imports=silent` | `scripts/ai_audit/` (the main AI pipeline; targeted scope to avoid `lib/customer_loader.py` noise outside the AI pipeline) | clean (14 source files, no issues found) | see "type-fix notes" below |
| `prettier` | `landing/assets/*.js` (HTML deliberately skipped — see below) | clean | minor JS spacing |

### Type-fix notes (mypy)

These were applied in addition to ruff's auto-fixes:

- `scripts/ai_audit/feedback_summary.py`: added explicit `Counter` annotations on `actions_total`, `severity_drift`, `rejected_titles` (lines 67–69). Without them, `mypy` can't infer the value type and complains about `Counter[<nothing>]`.
- `scripts/ai_audit/security_lite.py`: `seen_keys` was typed `set[str]` but the code calls `seen_keys.add((host, path))` — retyped to `set[tuple[str, str]]` to match the actual key shape.
- `scripts/ai_audit/html_extract.py`: BeautifulSoup `tag.get(...)` returns `str | AttributeValueList | None`. Wrapped a handful of `.strip()` call sites with `str(...)` to satisfy `union-attr`. Also renamed `for l in links` → `for link in links` to clear `E741`.
- `scripts/ai_audit/pipeline.py`: tightened a few `dict.get()` call sites where mypy couldn't prove the return type was a string. Specifically `cid = str(cat.get("id") or "")` (with an early `continue` on empty), `display = str(...)`, and `_form_email = form_cfg.get("customer_email")` with an `isinstance(_form_email, str)` guard before passing to `form_smoke_test.run_form_smoke_test(...)`. Removed dead `verdict = (audit_payload or {}).get("verdict") or {}` (line 1489) flagged by ruff `F841`.
- `scripts/ai_audit/llm_client.py`: added `# type: ignore[call-overload]` with one-line justifications on three `provider.chat.completions.create(...)` call sites. The Anthropic + OpenAI SDKs' overloads can't be statically resolved when the model string is dynamic. Suppressing locally with a documented reason is preferable to relaxing the project-wide mypy config.
- `scripts/consistency_check.py`: removed unused `needs_review_lines = []` flagged by `F841`.
- `api/tally-webhook.py`: renamed `for l in labels` → `for label in labels` (`E741`).
- `tests/test_sanitize_for_public.py`, `tests/test_share_report.py`: added `# noqa: E402` to imports below `sys.path.insert` (the pattern is deliberate; the path manipulation must happen first).

### Why HTML is NOT auto-formatted

`prettier` was run in `--check` against `landing/*.html` and it wanted to reflow ~all files: change indentation, rebreak long attribute lists, and collapse single-line `<p>` tags into multi-line. The existing HTML is hand-tuned to 2-space indent with 100ish-char prose-friendly line widths. Auto-formatting would produce a noisy diff that obscures every other change in this commit. We left HTML alone deliberately. A future opt-in pass can land later (see `ROB-REMAINING-TODO.md` q-final-lint follow-ups for the suggested `.prettierrc.json` config).

JS files (`landing/assets/*.js`) were auto-formatted; the diff is tiny (spacing only).

---

## 2. The q18 signature-bug fix

**What was wrong.** `q-final-audit` flagged that:

```
python scripts/deliver_report.py --customer customers/example-pro-package.yaml --handoff-report --provider stub
```

throws `takes 0 positional arguments but 1 positional argument and 3 keyword-only arguments were given`. The function in `scripts/ai_audit/pipeline.py` was defined as keyword-only:

```python
def run_handoff_report(
    *,
    audit_payload: dict[str, Any],
    effective_tier: str,
    audit_date: str,
    provider: str = "auto",
) -> str:
```

But `scripts/deliver_report.py` was calling it positionally: `ai_pipeline.run_handoff_report(data, effective_tier=..., audit_date=..., provider=...)`. The keyword-only `*` marker in the signature meant `data` was rejected.

**How we diagnosed.** Read both files side-by-side, then `git show 473e891 -- scripts/ai_audit/pipeline.py` (q18's original commit) confirmed the keyword-only signature was q18's intent — i.e. some downstream worker added a positional `data` call when refactoring the delivery script, not the other way around. Decision: fix the call site, preserve q18's signature.

**The fix** (`scripts/deliver_report.py`):

```python
narrative = ai_pipeline.run_handoff_report(
    audit_payload=data,
    effective_tier=canonical_tier,
    audit_date=delivered_at,
    provider=provider,
)
```

Plus a defensive `sys.path.insert(0, str(REPO_ROOT))` near the top of `scripts/deliver_report.py` (mirroring the same pattern in other scripts) so the `from scripts.sanitize_for_public import ...` chain resolves cleanly from any cwd.

**Verified by** re-running the exact command. It produces both `handoff-report.md` (15.3 KB) and `handoff-report.pdf` (401.0 KB) in `output/reports/example-pro-package/`. Smoke test confirms.

---

## 3. Forbidden-vocabulary rewrites (customer-facing)

Per `SIMPLICITY-GUARDRAILS.md` §6, the forbidden vocab list bans tagline copy like "Priority triage" / "Comprehensive audit" / "AI-powered" / "synthetic values" on customer surfaces. q-final-audit found 19 leaks. q-final-lint applied sentence-level rewrites (NOT bulk replace).

### "Comprehensive audit" → outcome / "Full audit" (4×)

| File | Line | Before | After |
|---|---|---|---|
| `landing/index.html` | 308 | Scale Up card tagline: "Comprehensive audit" | "Ready for real users" |
| `landing/index.html` | 361 | Comparison table cell: "Comprehensive audit" | "Ready for real users" |
| `landing/index.html` | 426 | Mobile Full card tagline: "Comprehensive audit" | "Ready for real users" |
| `landing/index.html` | 517 | FAQ body: "comprehensive audit" prose | rewritten to use "up to 30 findings" framing |

(`"comprehensive checklist"` is still allowed and still present in tier-card bullets — it refers to the §8 deliverable, not a marketing tagline.)

### "Priority triage" → "The 10 things to fix first" / "the 10 most important" (5×)

| File | Line | Before | After |
|---|---|---|---|
| `landing/index.html` | 140 | Sample-report verdict line: "5 findings (priority triage — Starter caps at 7)" | "5 findings shown (Starter shows the 10 most impactful)" |
| `landing/index.html` | 290 | Starter card tagline: "Priority triage" + "7 things" | "The 10 things to fix first" + "10 things" |
| `landing/index.html` | 360 | Comparison table cell: "Priority triage" | "The 10 things to fix first" |
| `landing/index.html` | 413 | Mobile Starter card: "Priority triage" + "7 most important" | "The 10 things to fix first" + "10 most important" |
| `landing/index.html` | 516 | FAQ body: "priority triage" prose | rewritten to "the 10 most impactful pre-launch issues" |

### "safe synthetic values" → "safe test data" (2×)

| File | Line | Before | After |
|---|---|---|---|
| `landing/index.html` | 622 | The Stranger persona blurb | "safe test data" |
| `landing/webflow.html` | 475 | Same persona blurb on Webflow SKU | "safe test data" |

### Stale finding caps in tier prose (paired rewrites, 8 spots)

While doing the Starter / Scale Up copy rewrites, the stale `7` (Starter) and `25` (Scale Up) numbers were also bumped to the canonical `10` / `30` from `PRODUCT-DECISIONS.md` §1. Specifically:

| File | Line(s) | Before | After |
|---|---|---|---|
| `landing/index.html` | 140 | "Starter caps at 7" | "Starter shows the 10 most impactful" |
| `landing/index.html` | 290–293 | Starter card "7 things" / "7 most important" | "10 things" / "10 most important" |
| `landing/index.html` | 308–311 | Scale Up card "25 findings" / "25" | "30 findings" / "30" |
| `landing/index.html` | 360–367 | Comparison table "7 most important" / "Up to 25" | "The 10 most important" / "Up to 30" |
| `landing/index.html` | 413–415 | Mobile Starter "7 most important" | "10 most important" |
| `landing/index.html` | 426–428 | Mobile Full "25 across all categories" | "30 across all categories" |

### Not rewritten (verified in context, allowed by §6)

- "AI scanner" (2× in `landing/index.html` line 496, `landing/webflow.html` line 357) — both are anti-pattern framing of competitor tools ("Not just another AI scanner"), not self-description. Read correctly, left as-is.
- "security audit" + "pentest" (6× across `landing/index.html`, `landing/webflow.html`, `landing/checklist.html`, `landing/sample.html`) — all read as scope-disclaimer ("LaunchLook is NOT a security audit, NOT a pentest"). Allowed by §6 in disclaimer context. Left as-is.

---

## 4. Em-dash sweep

Per `SIMPLICITY-GUARDRAILS.md` §6, em-dashes (`—`, U+2014) are forbidden on customer-facing prose surfaces (they read as AI-style copy).

| Category | Count | Decision |
|---|---|---|
| Prose em-dashes in `landing/index.html` lines 140 / 516 / 517 | 3 | Eliminated naturally — these were all inside the "Priority triage" / "Comprehensive audit" tier-card rewrites in §3 above. |
| Prose em-dash in `landing/index.html` line 326 | 1 | "(Stripe / auth / email / analytics setup — what's wired right" → "(Stripe / auth / email / analytics setup: what's wired right" (colon instead). |
| UI placeholder em-dashes in `landing/index.html` table cells (lines 378, 384, 390, 391, 396, 397) | 6 | Swapped to ASCII `-`. These are "no value here" markers populated by JS at render time, never read as prose. |
| UI placeholder em-dashes in `landing/r.html` (lines 104, 105, 110) | 3 | Swapped to ASCII `-`. Same JS-populated slots as above. |
| UI placeholder em-dash in `templates/r/shareable.html.j2` (line 109) | 1 | Swapped to ASCII `-`. Matches `landing/r.html`. |
| UI placeholder em-dashes in delivered `landing/r/<slug>.html` (3 customer-page files) | 3 | Auto-regenerated to `-` when smoke tests re-ran `deliver_report.py` against the example customers. |

Total: 17 em-dash sites touched. 0 prose em-dashes remain on customer-facing surfaces. 0 UI placeholder em-dashes remain. `python scripts/consistency_check.py --report-only` now reports `customer-facing em-dashes: 0`.

---

## 5. Refactors landed (light touch)

Each entry has a one-line justification.

- **Removed dead `verdict` variable** in `scripts/ai_audit/pipeline.py:1489`. Computed but never referenced; `ruff F841`.
- **Removed dead `needs_review_lines`** in `scripts/consistency_check.py:816`. Same reason.
- **Renamed ambiguous `l` → `link`** in `scripts/ai_audit/html_extract.py` and **`l` → `label`** in `api/tally-webhook.py`. `ruff E741` (single-char `l` is visually identical to `1`).
- **Tightened type narrowing** in `scripts/ai_audit/pipeline.py` (the `cid` / `display` / `_form_email` paths described in §1 above). Each fix has a defensible runtime behavior change — previously these would silently accept non-string values and either crash on `.strip()` or pass non-strings into downstream APIs that documented `str` only.
- **`UnicodeEncodeError` fix** in `scripts/share_report.py`: added `sys.reconfigure(encoding="utf-8")` block mirroring the same pattern in `scripts/deliver_report.py`. The script was crashing on Windows consoles (cp1252) when printing the checkmark `✓` character after toggling public/private. Now matches the delivery script's behavior.
- **`sys.path.insert(0, REPO_ROOT)`** added to `scripts/deliver_report.py`. The script imports `from scripts.sanitize_for_public import ...` which only resolves if the repo root is on `sys.path`. Other scripts do this; deliver_report didn't, which broke `python scripts/deliver_report.py ...` invocations from cwd != repo root.

### Considered but NOT refactored (deliberately)

- **HTML auto-formatting via prettier.** Considered, then declined — see §1 "Why HTML is NOT auto-formatted." Rob can opt in later.
- **Merging the two slugify helpers (`scripts/sanitize_for_public.py` + `scripts/share_report.py`).** Both have subtle differences (one strips PII tokens, the other only path components). Consolidation is risky without a separate unit-test pass. Left alone.
- **Refactoring `scripts/ai_audit/pipeline.py` into smaller modules.** That file is 1500+ lines and would benefit from being split. But splitting it is NOT a "light touch" refactor — it would touch every other file that imports from it. Out of scope. Flagged for a future cleanup pass.
- **Renaming the internal `Full` references in `scripts/ai_audit/`.** Some internal-only code still calls the middle tier "Full" (in variable names like `is_full_tier`). The customer-facing surfaces all say "Scale Up" now. Renaming internals would touch ~40 spots across the pipeline + tests and isn't visible to customers. Out of scope. (`PRODUCT-DECISIONS.md` §1 is canonical; internal naming can drift one cleanup pass behind.)
- **Removing `docs/MANUAL-TASKS-PRICE-BUMP.md`.** This doc references the pre-bump $9/$29 pricing, but it's a migration guide Rob still needs while doing the live Stripe live-mode retest. Not dead doc until that retest is complete.
- **Removing references to dropped ideas (Founder Roast, Discord, Cal.com) in old docs.** Same reason — old docs in `docs/` are intentionally historical; `PRODUCT-DECISIONS.md` §3 already lists what was dropped. Touching old docs risks rewriting history.

---

## 6. Full smoke-test results

All 12 commands from the prompt's Part 7, ran in order. Every command produced expected output. Two notes:

- `share_report.py --public` / `--private` automatically commits to git via the production code path. These transient commits were `git reset --mixed`'d back to `181d300` before the final commit (the `landing/data/reports/<slug>.json` artifacts were restored via `git checkout`). See "share_report.py automatic git commits" entry in `ROB-REMAINING-TODO.md`.
- `data/confidence_checks/` (q6 artifact) and `landing/images/badges/jane-sparkle-marketplace/*.png` (q17 artifacts) are gitignored or operator-local; they aren't part of the final commit.

| # | Command | Result | Notes |
|---|---|---|---|
| 1 | `deliver_report.py --customer customers/example-jane-sparkle.yaml --no-open` | ✓ | Produces report PDF + QSG PDF + `landing/r/jane-sparkle-marketplace.html` (private) + `landing/data/reports/...json` |
| 2 | `deliver_report.py --customer customers/example-webflow.yaml --no-open` | ✓ | Same artifact set, Webflow SKU |
| 3 | `deliver_report.py --customer customers/example-pro-package.yaml --no-open` | ✓ | Pro tier (40-finding cap, deep links in QSG) |
| 4 | `deliver_report.py --customer customers/example-pro-package.yaml --handoff-report --provider stub --no-open` | ✓ | **The q18 fix.** Produces `handoff-report.md` (15.3 KB) + `handoff-report.pdf` (401.0 KB) |
| 5 | `confidence_check.py --customer jane-sparkle --original example-jane-sparkle --provider stub` | ✓ | q6 Confidence Check re-scan; writes `data/confidence_checks/...` (gitignored) |
| 6 | `generate_verified_badge.py --customer customers/example-jane-sparkle.yaml` | ✓ | q17 badge generation; writes SVG (tracked) + PNG (untracked) |
| 7 | `share_report.py --slug jane-sparkle-marketplace --status` | ✓ | q22 status check; prints current public/private state |
| 8 | `share_report.py --slug jane-sparkle-marketplace --public` | ✓ | Toggle public; required `share_report.py` `UnicodeEncodeError` fix to land first (now ✓) |
| 9 | `share_report.py --slug jane-sparkle-marketplace --private` | ✓ | Restored to default; matching toggle behavior |
| 10 | `ai_costs_report.py --summary --days 7` | ✓ | gap5 cost reporting; margin OK 100.0% (target >=70%) |
| 11 | `github_push.py --customer customers/example-pro-package.yaml --dry-run` | ✓ | q19 dry-run; 14 issues would be created on `https://github.com/jane-sparkle/main-site` |
| 12 | `consistency_check.py --report-only` | ✓ | 41 issues / 22 needs human review / **0 critical (block ship)** |
| 13 | `pytest tests/` | ✓ | **124 / 124 passing in 0.56s** |

13/13 commands green. 0 failures. 0 skipped (no missing env vars).

---

## 7. Repo state at handoff

- Branch: `main`
- Pre-existing HEAD: `181d300` (q-final-audit)
- New HEAD: q-final-lint commit (this one)
- Working tree: clean after commit
- `origin/main`: synced (pulled --rebase before push)
- Test suite: 124 / 124 passing
- Linters: ruff + black + mypy + prettier all clean

**Repo is in shipping-ready state.**

### Next-step prompts for Rob

1. Review `docs/ROB-REMAINING-TODO.md` — the manual blocking tasks (Tally form choice, Stripe live-mode retest, Notion DB creation for Confidence Check, Resend domain verification, Vercel sanity check). Nothing in the repo prevents launch; these are operational tasks outside the codebase.
2. Skim this doc + `docs/CONSISTENCY-AUDIT-REPORT.md` for what changed during the overnight pass.
3. Open `landing/index.html` in a browser for a visual sanity check of the tier-card copy rewrites (`Starter → "The 10 things to fix first"`, `Scale Up → "Ready for real users"`).
4. Verify Vercel deployed `origin/main` cleanly (Vercel dashboard → Deployments → latest production).
5. Record the gap4 Loom demo when ready (60-second walkthrough; flagged in `docs/ROB-REMAINING-TODO.md`).
6. After the first paying customer, run `python scripts/customers_track.py add ...` per `CUSTOMER-TRACKING.md`.
