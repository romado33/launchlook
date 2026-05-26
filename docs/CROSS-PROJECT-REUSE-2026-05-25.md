# Cross-Project Reuse — Sibling Cursor Projects → LaunchLook

**Date:** 2026-05-25 (committed 2026-05-26)
**Status:** Report only. No patterns integrated yet — see "Integration status" on each item below.
**Source projects scanned:** `Cursor_WorkflowAutomation`, `Cursor_ModelVerdikt`, `Cursor_MasterApp` (incl. `risk_room/snyk_signal`, `url_enricher`, `portal`), `Cursor_FreeTrialInbox`, `Cursor_CourtBooking`, `Cursor_LinkedJobsExtractor`, `WealthSimpleDemo`, `Cursor_ConvertMarkdown` (incl. `markdown-migrator`, `markdown-clipper-extension`), `BallLauncher`, `DayOfWeekFinder`, `WifiIssue`, `Cursor_POATrainer`, `UncommonRhymesV3`, `Cursor_Predictors` (NHLPO_Predict, TSX, MM), `z_SnykDemo`, `TheLiloApp`, `Cursor_API_BS/pharma-monitor`.
**Author:** Cross-project explorer subagent run on 2026-05-25.

## TL;DR

- **8 top + 8 medium reusable opportunities** were identified across the sibling Cursor projects. Every item below is currently **Not yet integrated** into LaunchLook.
- **The standout finding (patterns #4 + #5 in the bonus section): idempotency + checkpoint discipline from `Cursor_WorkflowAutomation/agents/templates/`** is the structural fix that would have prevented the recent `q22` / `q-final-lint` worker-clobbering disaster. Adopting `IdempotencyStore` + DLQ + resume-from-output-file in long-running LaunchLook workers is the single most valuable carry-over.
- **Three top picks to actually pull in next** (in dependency order): WorkflowAutomation's 3-phase Claude orchestration (`automation_planner.py`) → ModelVerdikt's JSON-from-Claude recovery (`tryParseStructured`) → WorkflowAutomation's webhook idempotency template for Stripe/Tally.
- **House-rule patterns** Rob already uses across projects (external `.md` prompts, AI-for-interpretation/deterministic-for-execution, never trust raw Claude JSON, markdown-first reports) should be codified in LaunchLook's `docs/PRODUCT-DECISIONS.md` and `docs/SIMPLICITY-GUARDRAILS.md` before any of these patterns are imported.
- This file is **research only** — no code changes, no patterns wired in. Treat this as durable archive of the 2026-05-25 explorer run.

---

## Cross-Project Reuse Report

### Top opportunities (worth integrating now)

#### 1. `Cursor_WorkflowAutomation/agents/templates/` — production-grade Python automation skeletons
- **Path:** `c:\Users\RobDods\Apps\Cursor\Cursor_WorkflowAutomation\agents\templates\{scheduled_batch,event_driven,webhook_consumer}.py`
- **What it does:** Three drop-in Python templates with built-in `IdempotencyStore` (SHA256-keyed file store), `DeadLetterQueue` (JSONL append), exponential-backoff `@retry` decorator, structured JSON logger with `extra={"ctx": ...}`, and graceful shutdown via SIGTERM.
- **How LaunchLook reuses:** Your `api/*.py` Stripe + Tally webhook receivers should adopt the `webhook_consumer.py` pattern verbatim — HMAC signature validation, idempotency keying by event id, ack-then-process-in-thread, DLQ for failed payloads. The AI audit pipeline (long-running) should adopt `event_driven.py` for the customer-app scan queue.
- **Effort:** Small (literally copy + rename + fill TODOs). The retry/idempotency/DLQ classes are 30 lines each.
- **Look at:** `webhook_consumer.py:104-153` (Idempotency + DLQ), `scheduled_batch.py:96-145` (same classes hardened for batch).
- **Integration status:** Not yet integrated.

#### 2. `Cursor_WorkflowAutomation/agents/automation_planner.py` — multi-phase Claude orchestration
- **Path:** `c:\Users\RobDods\Apps\Cursor\Cursor_WorkflowAutomation\agents\automation_planner.py`
- **What it does:** Runs 3 sequential Claude calls (as-is → to-be → ops), each loaded from an external `.md` prompt, with score-aware emphasis injection (`build_score_emphasis`) and bulletproof JSON extraction from ```json fences.
- **How LaunchLook reuses:** This is the exact architecture your AI audit pipeline needs — phase 1 (extract raw findings from screenshots/HTML) → phase 2 (prioritize/categorize) → phase 3 (write the recommendations narrative + Quick Start). The `_extract_json()` helper (lines 62-77) handles "Here's the JSON:" prefixes. The `build_score_emphasis()` pattern (lines 176-222) is perfect for plan-tier-aware prompts ("CRITICAL — this is the free Lite tier, return ≤5 findings").
- **Effort:** Medium — port to your existing audit pipeline structure (~half a day).
- **Look at:** `automation_planner.py:262-307` (3-phase loop), `agents/prompts/plan_phase2_design.md` (templated prompt pattern with `{{SCORE_EMPHASIS}}`).
- **Integration status:** Not yet integrated.

#### 3. `Cursor_ModelVerdikt/prism/src/lib/structured-output/` — JSON-from-Claude validation
- **Path:** `c:\Users\RobDods\Apps\Cursor\Cursor_ModelVerdikt\prism\src\lib\structured-output\validate.ts`
- **What it does:** `tryParseStructured()` recovers JSON from markdown fences and naive prose ("Here is the result:..."); `validateAgainstSchema()` is a JSON-Schema-lite validator with bounded error reporting, format/pattern/enum/const checks. The Anthropic adapter (`engine/providers/anthropic.ts`) also extracts JSON from `tool_use` blocks when models silently drop text output.
- **How LaunchLook reuses:** Critical for your audit pipeline. Even with `response_format` directives, Claude periodically wraps JSON in ```json fences or prefaces with prose. The `firstBalancedJson()` walker (lines 67-91) and `tryParseStructured` together solve this once. Port to Python (~50 LOC) and put it in front of every `client.messages.create()` call.
- **Effort:** Small — port `tryParseStructured` to Python; the schema validator is a nice-to-have for later.
- **Look at:** `validate.ts:35-91` (parsing recovery), `providers/anthropic.ts:49-76` (tool-use fallback — important because Claude sometimes "answers" via tool_use even when you asked for JSON in text).
- **Integration status:** Not yet integrated.

#### 4. `Cursor_MasterApp/risk_room/snyk_signal/` — findings → policy → markdown report pipeline
- **Path:** `c:\Users\RobDods\Apps\Cursor\Cursor_MasterApp\risk_room\src\risk_room\snyk_signal\`
- **What it does:** End-to-end "ingest JSON → score by weighted dimensions → apply policy (block/warn/accept) → emit two flavors of markdown report (developer triage + executive summary)" with a `_PipelineCache` keyed on input file mtime.
- **How LaunchLook reuses:** This is structurally identical to your audit. `reports/triage.md` ≈ Main Report (per-finding actionable table), `reports/exec_summary.md` ≈ Quick Start Guide (executive headline + counts). The scoring pattern in `scoring/risk.py` (weighted `severity × fix_available × tier × exploit_maturity`) is the same shape as a LaunchLook severity model. The policy YAML in `config/policy.yml` lets non-engineers tune scoring without code changes — great if you want a future "audit profile" per plan tier.
- **Effort:** Medium — adapt the markdown templates and policy YAML idea; your Jinja2 PDF flow can keep doing the rendering.
- **Look at:** `reports/exec_summary.py` (whole file), `reports/triage.md` (whole file), `scoring/risk.py:85-123` (score_findings + sort), `main.py:103-167` (cache invalidation pattern).
- **Integration status:** Not yet integrated.

#### 5. `Cursor_MasterApp/url_enricher/` — generic CSV → Playwright deeper crawler
- **Path:** `c:\Users\RobDods\Apps\Cursor\Cursor_MasterApp\url_enricher\src\url_enricher\enrich.py`
- **What it does:** Reads a CSV with a URL column, visits each URL with Playwright using jittered delays + persistent profile, extracts page title and main body text via a hierarchy of selectors (`article > main > [role='main'] > #content > body`), writes results to output CSV with **resume support** (skips URLs already in output).
- **How LaunchLook reuses:** When LaunchLook Watch (or any pre-audit) needs to scan more than the single landing page, this is exactly the loop. Feed it `{url, app_id}` for every internal link discovered on the homepage, set `--profile-dir` for sites that need auth, get back an enriched CSV ready to chunk into Claude.
- **Effort:** Small — already a usable package (`pip install -e`). The `EnrichConfig` dataclass + `enrich_csv()` function is ~100 LOC of dependency.
- **Look at:** `enrich.py:18-25` (MAIN_SELECTORS hierarchy), `enrich.py:88-115` (resume from existing output).
- **Integration status:** Not yet integrated.

#### 6. `Cursor_FreeTrialInbox/trial_tracker/` + `Cursor_CourtBooking/court_booking/verification_mail.py` — IMAP + heuristic scoring
- **Path:** `c:\Users\RobDods\Apps\Cursor\Cursor_FreeTrialInbox\trial_tracker\{detect,scan,mail_utils}.py` and `c:\Users\RobDods\Apps\Cursor\Cursor_CourtBooking\court_booking\verification_mail.py`
- **What it does:** Together they form a complete Gmail IMAP toolkit. `mail_utils.py` handles `IMAP4_SSL`, header decoding, multipart text/html body extraction with cheap de-tagging. `detect.py` scores messages via weighted regex tuples (HIGH_PATTERNS like `\bauto[-\s]?renew\b` = 4 points, MEDIUM_PATTERNS = 1-2) with a "trusted sender domain" bonus. `verification_mail.py` adds polling with monotonic backoff (`interval = min(interval * 1.35, max_interval)`), INTERNALDATE awareness, and `[Gmail]/Spam` fallback.
- **How LaunchLook reuses:** (a) Watch customers' shared `support@` or `feedback@` inboxes for "my Lovable app is broken" tickets and auto-classify them into audit follow-up themes. (b) For audit-reply parsing: when a customer replies "did you mean the contact form on /signup", parse the thread. (c) The **weighted-regex scoring pattern in `detect.py:9-39` is directly portable to your existing findings prescreener** — replace your flat regex list with weight tuples and a min-score threshold.
- **Effort:** Small for the regex-scoring pattern; medium if you actually wire up an inbox.
- **Look at:** `detect.py:8-116` (full scoring engine), `verification_mail.py:280-381` (polling with INTERNALDATE + Spam fallback — much more robust than a naive IMAP loop).
- **Integration status:** Not yet integrated.

#### 7. `Cursor_LinkedJobsExtractor/scripts/linkedin_saved_jobs_extractor.py` — extract structured sections from unstructured HTML
- **Path:** `c:\Users\RobDods\Apps\Cursor\Cursor_LinkedJobsExtractor\scripts\linkedin_saved_jobs_extractor.py`
- **What it does:** Beyond `url_enricher`'s "get the text" — this one auto-detects sections (Requirements, Salary, Qualifications) by regex'ing common heading patterns and extracting until a stop-pattern; handles "Show more" expansion before extraction; uses multiple candidate selectors per field.
- **How LaunchLook reuses:** Two specific applications: (a) **Platform changelog scraping for LaunchLook Sync** — Lovable/v0/Bolt/Replit changelog pages have the same shape (headings + dated entries). Adapt `REQUIREMENTS_SECTION_PATTERNS` and `SECTION_STOP_PATTERNS` to changelog terminology. (b) When auditing a customer app, extract specific known-pattern blocks (pricing tables, signup forms, footer copyright) before sending to Claude for token efficiency.
- **Effort:** Small — copy the section-detection helpers (`extract_requirements`, `looks_like_requirement_line` at lines 273-323).
- **Look at:** `linkedin_saved_jobs_extractor.py:84-122` (regex pattern lists), `linkedin_saved_jobs_extractor.py:298-323` (section extraction with stop conditions), `linkedin_saved_jobs_extractor.py:211-242` (`expand_description` for "Show more" buttons — applicable to vibe-coded apps with collapsed content).
- **Integration status:** Not yet integrated.

#### 8. `Cursor_WorkflowAutomation/agents/scorer.py` — deterministic weighted scoring
- **Path:** `c:\Users\RobDods\Apps\Cursor\Cursor_WorkflowAutomation\agents\scorer.py`
- **What it does:** Pure-function deterministic scoring across 10 dimensions, each with weight (0.06-0.20), with normalized answer mapping and explicit gate dimensions (e.g., `technical_feasibility ≤ 2` forces "avoid"). Calibrated thresholds with academic citations.
- **How LaunchLook reuses:** Your "findings severity" model probably wants this exact shape — score each finding across (visual_severity, functional_severity, conversion_impact, fix_difficulty, brand_risk), weight them, and let a gate dimension force "must-fix-before-launch" when any single dim crosses a threshold. Deterministic + auditable means you can A/B-tune without re-prompting Claude.
- **Effort:** Small — same pattern, your own dimensions.
- **Look at:** `scorer.py:24-52` (DimensionScore/AssessmentResult dataclasses), `scorer.py:356-425` (compute_scores + threshold + override logic).
- **Integration status:** Not yet integrated.

---

### Medium-priority opportunities (could be useful later)

#### 9. `Cursor_ModelVerdikt/prism/src/lib/engine/providers/anthropic.ts` — production Anthropic SDK wrapper
- **Path:** `c:\Users\RobDods\Apps\Cursor\Cursor_ModelVerdikt\prism\src\lib\engine\providers\anthropic.ts`
- **Reuse:** Reference implementation showing timeout/AbortController, cost tracking via token counts, streaming with `input_json_delta` for tool-use, and the **critical gotcha** that Anthropic models sometimes return only `tool_use` blocks (no text) — your audit pipeline needs the same fallback.
- **Effort:** Small (conceptual port to Python; the patterns are language-agnostic).
- **Integration status:** Not yet integrated.

#### 10. `Cursor_ModelVerdikt/prism/src/lib/engine/quality-scorer.ts` — heuristic LLM-output QA
- **Path:** `c:\Users\RobDods\Apps\Cursor\Cursor_ModelVerdikt\prism\src\lib\engine\quality-scorer.ts`
- **Reuse:** Self-check Claude-generated findings before showing them to a customer: refusal detection, completeness vs prompt length, structure signals (headings/bullets/code), instruction-following via prompt-term recall. If quality < 70 on an AI finding, regenerate or escalate to you for manual review.
- **Effort:** Small — single file, no deps.
- **Integration status:** Not yet integrated.

#### 11. `Cursor_MasterApp/portal/main.py` — FastAPI + SPA hosting pattern
- **Path:** `c:\Users\RobDods\Apps\Cursor\Cursor_MasterApp\portal\main.py`
- **Reuse:** When LaunchLook outgrows Vercel serverless and you need a long-running Python API (e.g., the audit pipeline can't fit in a 60-second function), the `_register_spa()` pattern (lines 204-228) shows how to serve `frontend/dist` and an `/api` prefix from one FastAPI process. Includes safe path-traversal handling.
- **Effort:** Small for the pattern; the migration off Flask serverless is the real work.
- **Integration status:** Not yet integrated.

#### 12. `WealthSimpleDemo` — "AI analyzed / Human must decide" UX pattern + parallel Claude calls
- **Path:** `c:\Users\RobDods\Apps\Cursor\WealthSimpleDemo\README.md`
- **Reuse:** The README itself is a goldmine: it documents how the WS demo separates "AI did this quantitatively / human still must decide this qualitatively" in the UI. **Directly applicable** to your audit-UI customer portal — instead of "here are 12 findings", frame as "AI confirmed: 8 fixes / Your judgment needed: 4 design calls". Also runs two Claude prompts **in parallel** (`scenarioNarrationPrompt.md` + `decisionGatePrompt.md`) loaded from `.md` files — same pattern your audit should adopt.
- **Effort:** Small (UX framing) to medium (parallel `asyncio.gather` for two Claude calls).
- **Integration status:** Not yet integrated.

#### 13. `Cursor_ConvertMarkdown/markdown-migrator` — HTML → Markdown conversion service
- **Path:** `c:\Users\RobDods\Apps\Cursor\Cursor_ConvertMarkdown\markdown-migrator`
- **Reuse:** Next.js + Cheerio + Turndown + sanitize-html service that converts HTML uploads into clean markdown with assets extracted and link-rewriting. **Relevant for the AI audit pipeline**: instead of sending raw scraped HTML to Claude (token-heavy, noisy), pre-convert to markdown using this service or its conversion module. Optional OpenAI features (table narration, alt-text via vision, boilerplate trim) are nice but the conversion core is the win.
- **Effort:** Medium — extract the conversion pipeline module out of the Next.js app, or call it as an HTTP service from your Python pipeline.
- **Integration status:** Not yet integrated.

#### 14. `Cursor_ConvertMarkdown/markdown-clipper-extension` — Chrome MV3 page-clipping extension
- **Path:** `c:\Users\RobDods\Apps\Cursor\Cursor_ConvertMarkdown\markdown-clipper-extension`
- **Reuse:** Long-tail idea: a "Send your app to LaunchLook" Chrome extension that POSTs the customer's currently-viewed page HTML + screenshot to your audit endpoint. Useful for customers who can't or won't paste a URL (e.g., behind auth). The full MV3 boilerplate is here — manifest, background, content scripts, popup.
- **Effort:** Medium — the extension scaffold is reusable; you'd adapt the destination URL and POST body shape.
- **Integration status:** Not yet integrated.

#### 15. `Cursor_WorkflowAutomation/z_AnjuDemo/anju-case-router` — LangGraph classify→RAG→policy→action pipeline with audit
- **Path:** `c:\Users\RobDods\Apps\Cursor\Cursor_WorkflowAutomation\z_AnjuDemo\anju-case-router`
- **Reuse:** Conceptually relevant for the audit-UI's "classify → enrich → policy → propose actions → require approval → mock execute → log to audit_trail" flow. The append-only audit trail in SQLite is a useful pattern for customer-facing "show your work" transparency. Deterministic-first classification (`try_strong_keyword_classification`) before falling back to LLM is the cost-saver pattern LaunchLook should adopt for repeat findings.
- **Effort:** Medium-large — full port not warranted, but the architecture document is worth a 15-min read.
- **Integration status:** Not yet integrated.

#### 16. `Cursor_WorkflowAutomation/PITCH_GUIDE.md` — interview/pitch framing patterns
- **Path:** `c:\Users\RobDods\Apps\Cursor\Cursor_WorkflowAutomation\PITCH_GUIDE.md`
- **Reuse:** Not code, but the "AI for interpretation, deterministic for execution" framing is exactly how you should describe LaunchLook on the landing page and in sales calls. Cribs from this doc would make your homepage copy much stronger. The "shadow mode → feature flag → cutover" + "DORA metrics for an internal script" sections will help when customers ask "how do I know your AI audit is right?".
- **Integration status:** Not yet integrated.

---

### Low-priority / one-off / not relevant

- **`BallLauncher/`** — single `OpenCursor.bat`; empty project.
- **`DayOfWeekFinder/`** — single `index.html` utility; irrelevant.
- **`WifiIssue/`** — Windows WiFi-fix PowerShell scripts; unrelated domain.
- **`Cursor_POATrainer/`** — static HTML/CSS PAO card-memory trainer; UI study at best.
- **`UncommonRhymesV3/`** — Gradio + CMU dict rhyme app; not applicable.
- **`Cursor_Predictors/`** (NHLPO_Predict, TSX, MM) — sports/stock prediction models; no audit relevance. Some `prediction_kit` utilities are already re-exported through `Cursor_MasterApp`.
- **`z_SnykDemo/`** — superseded by `Cursor_MasterApp/risk_room/snyk_signal` (already covered above as item #4).
- **`TheLiloApp/`** — Rob's other Lovable-built React app. Treated with care per your note; only the README was read. Not a code source, but a useful **persona reference**: read its `Welcome to your Lovable project` README to feel the gap between a fresh Lovable-shaped repo and LaunchLook-worthy production state. That gap _is_ your product.
- **`Cursor_API_BS/pharma-monitor`** — Health Canada / openFDA / PubMed FastAPI app; not relevant unless health vertical (the FastAPI scaffolding is duplicated in `Cursor_MasterApp/risk_room` already).
- **`Cursor_CourtBooking/scripts/*`** — 60+ legacy one-off booking scripts; ignore. The `court_booking/` package (covered above) is the maintained surface.

---

### Projects you couldn't access or scan
None. Every directory listed was readable. The early Shell tool failed (Windows PowerShell quirk in this environment) but `Glob` + `Read` covered everything.

---

### Bonus: patterns/ideas observed across Rob's projects

These are conventions Rob uses repeatedly. Worth codifying as LaunchLook house rules:

1. **Prompts always live in external `.md` files, never hardcoded strings.** Seen in `Cursor_WorkflowAutomation/agents/prompts/`, `WealthSimpleDemo/backend/prompts/`, `Cursor_MasterApp` — every project that calls Claude does this. LaunchLook's audit pipeline should adopt immediately; it lets you version, A/B test, and (importantly) review prompts in PRs without code diff noise.

2. **"AI for interpretation, deterministic code for execution."** Strict separation everywhere — `scorer.py` is pure functions, `validate.ts` is pure JSON schema, `try_strong_keyword_classification` runs before any LLM call. LaunchLook should keep the regex prescreener as the authoritative findings filter and use Claude only for prioritization narrative.

3. **JSON-from-Claude is never trusted as-is.** Two independent implementations (`_extract_json` in Python, `tryParseStructured` in TS) handle ```json fences, leading prose, and balanced-brace recovery. Port one to your audit pipeline before you ship customer-facing AI output.

4. **Idempotency + DLQ + structured JSON logging are first-class objects, not afterthoughts.** All three workflow automation templates include them by default. Your `api/*.py` Stripe + Tally handlers will get burned without these.

5. **Resume-able processing via "is this key in the output file?" check.** Used in `url_enricher`, `linkedin_extractor`, `IdempotencyStore`. Pattern: every long-running LaunchLook audit should be checkpointable — kill the process mid-customer and re-run picks up at the next URL/finding.

6. **Score-aware prompt construction.** `build_score_emphasis()` injects directive flags (`CRITICAL — ...`, `HIGH PRIORITY — ...`) when scores cross thresholds. LaunchLook can use the same pattern to vary audit prompt strictness based on plan tier (Lite/Standard/Pro) or detected app stack (Lovable vs Base44 vs Replit).

7. **A `CLAUDE.md` (and often `AGENTS.md` + `.cursor/rules/*.mdc`) at the top of every repo.** They're short and concrete: entry points, env vars, gotchas, "use the X package not the legacy scripts". You should add one to LaunchLook if not already present — pays back every Cursor session.

8. **Markdown is the report primitive; PDF is the renderer.** Both `risk_room` (triage.md + exec_summary.md) and `automation_planner` (plan_*.md + kpi_baseline_*.md) write markdown first. LaunchLook's Jinja2-rendered Main Report and Quick Start Guide should probably go via markdown intermediate — gives you a free in-browser preview and an `--output md` mode for customers who'd rather paste into Notion/Linear than read a PDF.

9. **Streamlit for internal tools, Vite+React for customer-facing.** Pattern across `Cursor_WorkflowAutomation/demo/app.py`, `Cursor_FreeTrialInbox/streamlit_app.py`, `Cursor_CourtBooking/streamlit_app.py` (internal) vs `Cursor_MasterApp/frontend` and `Cursor_ModelVerdikt/prism` (customer). Your existing Flask audit-UI fits this model; if you want a faster internal tool for *running* audits, Streamlit will save you days.

10. **Sibling `.env` reuse via parent-dir lookup.** `Cursor_FreeTrialInbox/trial_tracker/dotenv_loader.py` walks up to `c:\Users\RobDods\Apps\Cursor\` and loads `Cursor_CourtBooking/.env` automatically. Cute, but probably not worth adopting for LaunchLook (different security model). Mentioning so you don't accidentally break this if you reorganize folders.

---

## Notes for future Rob

- The standout pattern is **idempotency + checkpoint discipline from `Cursor_WorkflowAutomation/agents/templates/`** — patterns #4 + #5 in the report. Adopting this is the structural fix that prevents future `q*` worker-clobbering disasters.
- Top three to actually pull in next: WorkflowAutomation's 3-phase Claude orchestration (`automation_planner.py`), ModelVerdikt's JSON-from-Claude recovery (`tryParseStructured`), WorkflowAutomation's webhook idempotency template.
- Do not action any of these without first updating `docs/PRODUCT-DECISIONS.md` with the decision rationale, and without considering whether each pattern violates `docs/SIMPLICITY-GUARDRAILS.md`.
