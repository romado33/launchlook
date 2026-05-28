# Lessons learned — building LaunchLook v1

A comprehensive retrospective covering every recurring correction, every
technical pitfall, every product decision that was hard-won, and a
first-week checklist for the next app. Written from a complete reading of
the project docs, transcript, and codebase.

Pair this with [`.cursor/rules/launchlook-defaults.mdc`](../.cursor/rules/launchlook-defaults.mdc)
which encodes the recurring corrections as standing Cursor agent instructions.
**Copy that rule file into the next repo on day one.**

---

## Part 1 — Recurring corrections (things Rob had to tell me more than once)

### 1. Numbers are sacred — never substitute your own

**The mistake I kept making:** Defaulting to what "sounds right" when a number
wasn't immediately visible (e.g. writing 3 free findings, 7 Pro findings).

**The rule:** Always grep `scripts/launchlook_constants.py` and
`docs/PRODUCT-DECISIONS.md` §1 before using any number. If uncertain, ask.
Never substitute.

**Canonical values as of 2026-05-27:**

| Surface | Value |
|---|---|
| Free tier delivery count | **2 findings** (`FREE_AUDIT_DELIVER_COUNT = 2`) |
| Free tier pipeline depth | Starter cap (10) — runs deeper, delivers top 2 |
| Starter Package ($19) | Up to **10** findings |
| Scale Up Package ($49) | Up to **30** findings |
| Pro Package ($99) | Up to **40** findings |
| Refund window | **7 days** |
| Free → Starter dedup window | **90 days** |
| Starter → Scale Up price gap | **$19 → $49 → $99** (intentional, fixed) |
| Handoff Report add-on | **$49** (was $99 — reduced 2026-05-26) |
| Fix Check re-scan standalone | **$19** standalone, **$9** within 14 days |
| Delivery email max words | **150** (per `SIMPLICITY-GUARDRAILS.md` §5.3) |
| Report: max sections | **5** |
| Report: max pages per finding | **1** |
| Landing pricing cards: max bullets | **5 per tier** |
| Tier count: hard cap | **4** (Free / Starter / Scale Up / Pro) |
| Tester personas: hard cap | **7** (do not add an 8th) |

**Drift test pattern** — any number that appears in both code and copy needs
a test that checks they match:

```python
def test_api_inline_constant_matches() -> None:
    src = (REPO_ROOT / "api" / "free-audit.py").read_text("utf-8")
    match = re.search(r"^FREE_AUDIT_DELIVER_COUNT\s*=\s*(\d+)", src, re.MULTILINE)
    assert int(match.group(1)) == FREE_AUDIT_DELIVER_COUNT
```

### 2. Brand voice — specific banned words and patterns

**`docs/SIMPLICITY-GUARDRAILS.md` §6 and `docs/04-content-and-copy.md` are
the canonical sources. Read them before touching any customer-facing surface.**

**Hard bans on all customer-facing copy:**
- ❌ Em-dashes anywhere except the `— Rob` sign-off in emails
- ❌ "Trust Gaps" → ✅ "embarrassing bugs" or "things a visitor would notice"
- ❌ "native apps" → ✅ "desktop and mobile width testing" or "web app responsive"
- ❌ "AI-powered scanner" as a value prop
- ❌ "automation," "intelligent analysis," "next-generation," "seamless," "robust"
- ❌ "leverage," "utilize," "elevate," "empower," "unlock," "supercharge," "revolutionize"
- ❌ "advanced," "premium," "professional" (we have a Pro tier; don't reuse the word)
- ❌ "AI pipeline," "fingerprint dedup," "Snoop," "Scale-Ready," "Compliance-Lite" (internal taxonomy — never crosses to customers)
- ❌ "Trust Gaps," "RLS policies," "CSP headers," "Largest Contentful Paint" in finding titles
- ❌ Logo walls until logos are real
- ❌ "Our analysis indicates..." → ✅ "I saw that..."

**Voice test:** Would a non-technical vibe-coder founder understand this in
under 5 seconds? Is every sentence under 20 words? Is it second person active?

### 3. "Up to X" not "X" for finding caps

**The mistake:** Writing "40 findings + fix prompts" on pricing cards.
A Pro customer getting 12 real findings feels cheated even though 12 was correct.

**The rule:** Always say **"Up to X findings"** on all pricing cards, FAQ, and
copy. The LLM prompt uses a target range (not just a ceiling) so it delivers
closer to the cap, but the customer promise must be "up to."

Pricing card pattern:
```html
<li>Up to <strong class="text-ink">40</strong> findings + fix prompts</li>
```

### 4. LLM prompts: target ranges, not ceilings

**The mistake:** Prompt said "Return up to {cap} findings." GPT treated this
as a ceiling and stopped at 6-7 "obvious" issues regardless of tier.

**The fix** (`scripts/ai_audit/pipeline.py` `_tier_guidance()`):
- Starter: target 5-10 (cap 10)
- Scale Up: **target 20-30**, minimum 20, walk every category
- Pro: **target 30-40**, minimum 30, walk every category, integrations too

**Anti-padding guardrail is non-negotiable:**
> "You may NOT invent findings to pad the count. If a category truly does
> not apply, skip it. But the target minimum exists because most live apps
> genuinely have that many real issues — being well under usually means
> you stopped early."

### 5. Center status text and microcopy under CTAs

**The mistake I kept making:** Leaving disclaimer / status text under form
submit buttons left-aligned.

**The rule:** Any `<p>` between a primary CTA button and the next section
gets `text-center`:

```html
<button ...>Get my free 2 findings</button>
<p data-free-audit-status class="mt-2 text-sm text-muted text-center hidden" ...></p>
<p class="mt-3 text-xs text-footnote text-center">Free, no credit card...</p>
```

### 6. Personal contact card footer, not corporate footer

**The mistake:** Building a standard `Company / Product / Legal` footer.

**Rob wants:**
- His name (`Made by Rob Dods`)
- One-line bio (15+ years technical writer, personally reviews every audit)
- One email link (`hello@launchlook.app`)
- One LinkedIn link (hidden until populated via `data-launchlook-linkedin`)
- Nothing else — no duplicate email links elsewhere on the same page

**Never add:** newsletter signup, logo wall, nav columns, "Powered by" line.

### 7. URL inputs must accept bare hostnames

**The mistake:** Validating `https://` prefix strictly, breaking submissions
from users who type `mysite.com`.

**The rule:** Normalize **both** client-side and server-side:

```javascript
// Client-side (landing/assets/free-audit.js)
if (payload.url && !/^https?:\/\//i.test(payload.url)) {
  payload.url = "https://" + payload.url.replace(/^\/+/, "");
}
```

```python
# Server-side (api/free-audit.py)
if not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", cleaned):
    cleaned = "https://" + cleaned.lstrip("/")
```

### 8. Email notifications must be HTML + text multipart

**The mistake:** Sending plain-text-only notification emails. A long
`mailto:customer@x.com?subject=...&body=<500 chars URL-encoded>` in a
plain-text email gets autolinked only at the first `?` by Gmail. The rest
of the query string spills into the visible body as garbage.

**The fix:** Always send via Resend with both `html` and `text` fields:

```python
payload = {
    "from": f"LaunchLook Automation <{from_email}>",
    "to": [admin],
    "subject": subject,
    "text": text_body,        # compact mailto (subject only, no body)
    "html": html_body,        # full mailto behind <a href>
}
```

The long mailto URL goes inside `<a href="...">Open delivery draft →</a>` in
HTML. The plain-text version uses a compact subject-only mailto as fallback.

### 9. PowerShell is the shell — write commands for it

**Rules:**
- ❌ `cmd1 && cmd2` → ✅ `cmd1; if ($?) { cmd2 }`
- ❌ Heredocs (`<<EOF`) → ✅ Here-strings (`@"..."@`) or `git commit -F file.txt`
- ❌ `ruff check` → ✅ `python -m ruff check`
- ❌ Unicode `print("→ done")` → ✅ `print("-> done")` or set `$env:PYTHONIOENCODING="utf-8"` first
- ❌ Assuming stderr = failure — PowerShell wraps Flask's dev-server warning
  in `NativeCommandError` at exit 0. Read actual output before concluding failure.

### 10. Reduce CLI friction — clickable links beat terminal commands

**The pattern I kept breaking:** Writing "now run `python scripts/foo.py --slug=...`"
in notification emails. Rob wants to click things.

**The rule:** If a workflow step can be a link, make it a link:
- Draft-ready email → three buttons: `Refine findings →`, `Preview report →`, `Open delivery draft →`
- `/review/<slug>` opens the AI review UI pre-loaded for that customer
- `/preview/<slug>` renders the live Jinja report (same template as PDF)
- The mailto button opens a pre-composed Gmail draft with findings in the body

Terminal commands appear in email **only** as fallbacks for when the review
server isn't running.

### 11. Lint + test before every push — specific paths, not whole repo

```powershell
python -m ruff check scripts/audit_automation/notify.py
python -m ruff format scripts/audit_automation/notify.py  # specific file only
python -m pytest tests/ -x -q
```

**Never:** `python -m ruff format .` — this reformats untouched files and
creates noise in the diff. Always pass the specific files you changed.

### 12. Commit message style

Pattern: `scope: one-line present-tense summary`

Examples:
- `fix(audit): make tier guidance target minimums so Pro audits hit ~30-40 findings, not 7`
- `landing: center the form status + disclaimer text under the submit button`
- `fix(api): inline FREE_AUDIT_DELIVER_COUNT to fix Vercel function crash`
- `trust: add IP-theft FAQ answer + pricing trust note`

No multi-line bodies for small changes. No emojis. Cite `SIMPLICITY-GUARDRAILS.md` rule numbers (e.g. `§2.1`) in commits when making brand judgment calls.

### 13. Don't create new docs/markdown files without being asked

**What Rob actually wants:**
- Update `docs/ROB-REMAINING-TODO.md` (the canonical TODO)
- Update `canvases/*.canvas.tsx` (project status snapshot)
- Ask before creating anything else

The one exception: `docs/LESSONS-LEARNED.md` and `.cursor/rules/` are
explicitly requested and should be updated as the project grows.

### 14. The Testers cast is internal-only

The 7 personas (Tourist, Skeptic, Klutz, Snoop, Phone-First Friend, Saboteur,
Stranger Who Tried to Sign Up) drive the audit pipeline internally but are
**never named on customer surfaces** as of 2026-05-26. Finding tags say
"Caught by The Snoop" in small text on the finding card only. No hero sections,
no marketing copy about the personas.

**Do not add an 8th Tester** without explicit approval and a new audit category
to justify it.

### 15. GitHub integration is dormant — do not re-enable silently

`scripts/github_integration.py` and `scripts/github_push.py` exist but are
dormant. The "auto-create GitHub issues" promise was removed from Pro tier
marketing in May 2026. `GITHUB_PAT` is in `.env.example` under "DORMANT".
Do not reintroduce without explicit approval.

### 16. What the form smoke status means

"Form smoke: skipped/failed" in founder emails means Playwright didn't run
form submission tests on that particular job — either Playwright wasn't
available, no eligible forms were detected, or the email was a manual replay
not a real pipeline run. It does **not** mean the site's forms are broken.

The customer never sees this label. In the HTML email it shows as:
- `ran ✓` when Playwright submitted and checked forms
- `not run (Playwright unavailable or no forms detected)` otherwise

---

## Part 2 — Technical pitfalls and how we solved them

### Vercel Python serverless: `FUNCTION_INVOCATION_FAILED`

**Problem:** `api/*.py` imported from `scripts/launchlook_constants.py` via
`from scripts.launchlook_constants import X`. Works locally, crashes at Vercel
cold start.

**Root cause:** Vercel's Python runtime doesn't reliably bundle top-level
sibling modules even with `__init__.py` present.

**Fix that worked:**
1. Add `scripts/__init__.py` (necessary but not sufficient alone)
2. **Inline critical constants** directly in `api/*.py`
3. Add a drift test to catch any divergence:

```python
# tests/test_launchlook_constants.py
def test_api_inline_constant_matches() -> None:
    src = (REPO_ROOT / "api" / "free-audit.py").read_text("utf-8")
    match = re.search(r"^FREE_AUDIT_DELIVER_COUNT\s*=\s*(\d+)", src, re.MULTILINE)
    assert int(match.group(1)) == FREE_AUDIT_DELIVER_COUNT
```

**For next app:** Keep `api/*.py` self-contained from day one. If you need
shared logic, copy small constants and write a drift test.

### Resend + Cloudflare WAF: HTTP 403

**Problem:** Resend API calls returned HTTP 403 with Cloudflare error 1010.

**Root cause:** Cloudflare blocks the default `Python-urllib/X.Y` User-Agent.

**Fix:** Set an explicit `User-Agent` on every outbound API call:

```python
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
    "User-Agent": "LaunchLook-Automation/1.0 (+https://launchlook.app)",
}
```

**For next app:** Set a custom User-Agent on every third-party API call on
day one. Applies to Resend, Notion, and any other service behind Cloudflare.

### Long mailto URLs in plain-text emails

**Problem:** `mailto:customer@x.com?subject=X&body=<entire findings list>`
in a plain-text email body gets autolinked only at the first `?` by Gmail.
Rest spills as `%20`-encoded garbage.

**Fix:** Send multipart HTML + text. Put the long URL inside `<a href>` in
HTML; use a compact subject-only mailto in plain text (see §Part 1, item 8).

### OpenAI structured output: schema `required` array

**Problem:** `response_format={"type":"json_schema",...}` in strict mode
silently drops fields not listed in `required`, even if they're in
`properties`.

**Fix:** Put **every** property name into `required`. Use `"description"` to
mark fields that are optional in meaning — the model returns `""` when not
applicable.

### Notion property normalization

**Problem:** Notion select values come back decorated (`"Pro Package ($99)"`).
Downstream `tier_caps[tier]` KeyErrors silently and falls to a bad default.

**Fix:** Normalize at the boundary, warn loudly on miss:

```python
TIER_NORMALIZE = {
    "pro package": "Pro Package",
    "pro package ($99)": "Pro Package",
    "pro": "Pro Package",
    # ... etc
}
tier = TIER_NORMALIZE.get(raw.lower(), raw or "Starter Package")
if tier not in KNOWN_TIERS:
    print(f"WARN: unrecognised tier {raw!r}", file=sys.stderr)
```

Never use a silent fallback like `.get(key, 7)` — always log when the fallback
fires.

### Playwright on Windows — Unicode encoding

**Problem:** Playwright stdout includes Unicode (✓, →) that crashes Python on
Windows with `UnicodeEncodeError`.

**Fix:**
1. `os.environ["PYTHONIOENCODING"] = "utf-8"` at the top of Playwright scripts
2. Replace Unicode arrows in your own `print()` with ASCII (`->`)
3. In PowerShell sessions: `$env:PYTHONIOENCODING="utf-8"` before running

### Ruff format drift on unrelated files

**Problem:** `python -m ruff format .` produces cosmetic diffs on files you
weren't editing (collapsed multi-line args etc.), making diffs noisy.

**Fix:** Always pass specific paths: `python -m ruff format scripts/ai_audit/pipeline.py`.
If you accidentally formatted everything, `git checkout HEAD -- <files>` to revert.

### Vercel cannot run the full audit pipeline

Vercel serverless functions time out at 10-60 seconds and have no Playwright.
The pipeline (capture → prescreen → LLM → YAML) must run locally or on a VM.

**Queue state lives in Notion, not on the server filesystem.** The Vercel API
endpoints just write `Status=queued` to Notion. The local worker (`process_audit_queue.py`)
polls Notion and processes jobs.

### `pipeline.run()` doesn't call form smoke internally

The form smoke test (`scripts/ai_audit/form_smoke_test.py`) is a **separate
module**. It's called by the worker but not inside `pipeline.run()`. The
`PipelineResult.form_smoke_ran` flag defaults to `False` and is only set to
`True` when the worker explicitly invokes form smoke. Manual replays that skip
the worker will always show "not run."

### Flask dev server stderr in PowerShell

Flask writes `WARNING: This is a development server...` to stderr. PowerShell
wraps this in `NativeCommandError` output even when exit code is 0. Read the
actual server output before concluding the server failed to start. Smoke check
with a quick HTTP request:

```powershell
(Invoke-WebRequest -Uri "http://127.0.0.1:8000/" -UseBasicParsing).StatusCode
```

---

## Part 3 — Product decisions that were hard-won (read before touching these)

### Tier ladder is frozen at 4

Free / Starter ($19) / Scale Up ($49) / Pro ($99). No 5th tier. No renaming.
No "Enterprise," "Premium," "Founder Roast." See `docs/PRODUCT-DECISIONS.md` §3.

Explicitly killed: Founder Roast tier ($229), Watch subscription, Verified badge,
public `/checklist` page, GitHub auto-issue creation in Pro.

### Human gate before customer delivery is non-negotiable

The pipeline drafts; Rob delivers. `deliver_report.py --send` is never called
automatically. The risk of an AI hallucination shipped to a paying customer is
too high. The human gate is the product's trust signal.

### Free → Starter dedup rule

When a free-tier user upgrades to Starter within 90 days, the AI generates
**10 NEW findings** that exclude the original 2. Never re-surface the free
findings on a paid report. See `docs/PRODUCT-DECISIONS.md` §2.

### Notion as the customer database (for now)

No custom dashboard until ~30 customers. Notion: zero engineering, easy to
template, customers can share by link. Trigger to re-evaluate: Notion becomes
a friction point at scale.

### Webflow is a parallel SKU, not a new tier

Same pricing, same 4-tier ladder, platform-aware fix prompts (Webflow Designer
language). Treat as a separate landing page (`/webflow`), not a product extension.

### PageSpeed Insights, Lighthouse, Microsoft Clarity: never compete head-on

Free, Google/Microsoft-backed. LaunchLook's wedge is **translator + curator**.
Never "faster than Lighthouse." Never "deeper than Snyk."

### The one-liner competitive positioning

> **"PageLens is a scanner. LaunchLook is a scanner with judgment."**

Use this exact phrasing in `/vs-pagelens` and comparison content. Do not paraphrase.

### Plausible analytics: currently dormant

`plausible-event-name=…` CSS classes are on every CTA. The `<script>` tag was
removed in May 2026. Re-enable is a one-line `<script>` re-add. Trigger:
≥10 paying customers or noticeable traffic without obvious conversion.

### Fix Check (formerly Confidence Check): internal name vs customer name

- **Internal/webhook/Stripe/Notion/filename:** `confidence_check` — do not rename
- **Customer-facing:** "Fix Check" — what appears in emails, report PDF footer, and copy
- Offered only via post-delivery email + report PDF footer. Not on landing pricing cards.

---

## Part 4 — The full environment variable list

These are all required environment variables. Any missing one silently breaks
a workflow step.

| Variable | Purpose | Where used |
|---|---|---|
| `LAUNCHLOOK_DOMAIN` | `launchlook.app` | API redirects |
| `FROM_EMAIL` | `hello@launchlook.app` | Resend sender |
| `ADMIN_EMAIL` | `rob@launchlook.app` or `romado33@gmail.com` | Founder notifications |
| `NOTION_TOKEN` | Notion integration token | All Notion calls |
| `NOTION_CUSTOMERS_DB_ID` | Paid customer records | Stripe/Tally webhooks, dashboard |
| `NOTION_FINDINGS_DB_ID` | Finding templates (38 rows) | Audit pipeline |
| `NOTION_OUTREACH_DB_ID` | Cold-outreach pipeline | Outreach tracker |
| `NOTION_FREE_AUDIT_DB_ID` | Free audit request queue | `/api/free-audit` |
| `NOTION_CONFIDENCE_CHECK_DB_ID` | Fix Check deliveries | Stripe webhook |
| `NOTION_REPORTS_PARENT_PAGE_ID` | Report sub-pages parent | Report rendering |
| `STRIPE_SECRET_KEY` | Stripe live mode | Webhook verification |
| `STRIPE_WEBHOOK_SECRET` | Webhook signature verify | `/api/stripe-webhook` |
| `RESEND_API_KEY` | Transactional email | All email sends |
| `TALLY_API_KEY` | Tally form API | `scripts/tally_create_intake.py` |
| `TALLY_WEBHOOK_TOKEN` | Inbound webhook auth | `/api/tally-webhook` |
| `E2E_CHECKLIST_PASSWORD` | Internal go-live checklist auth | `/api/e2e-auth` |
| `OPENAI_API_KEY` | LLM (primary in practice) | `scripts/ai_audit/llm_client.py` |
| `ANTHROPIC_API_KEY` | LLM (preferred, fallback) | `scripts/ai_audit/llm_client.py` |
| `PSI_API_KEY` | Google PageSpeed Insights | `performance_speed.py` |
| `HEADLESS` | Playwright headless mode | All Playwright scripts |
| `GITHUB_PAT` | **DORMANT** — GitHub auto-issues | (removed from live workflow) |

**Critical for Vercel:** `FROM_EMAIL` must be a domain verified in Resend
(`launchlook.app` is already verified). Free-audit confirmation emails to
customers will bounce without it.

---

## Part 5 — Infrastructure: what lives where

| Concern | Solution | Reason |
|---|---|---|
| Landing pages | Vercel (static HTML) | Free, fast, CDN |
| API endpoints | Vercel serverless (Python) | Co-located with landing |
| Full audit pipeline | Local machine / VM | Playwright + long runtime |
| Job queue | Notion `Status` field | No infra, founder can see/edit |
| Customer data | Notion Customers DB | Zero engineering, easy to template |
| Emails | Resend | Simple API, generous free tier, great deliverability |
| Intake form | Tally (form ID: QKOX1A) | No-code, Notion webhook integration |
| Payments | Stripe Payment Links | No custom checkout, no backend |
| Scheduling | Windows Task Scheduler (local) | Not GitHub Actions — pipeline needs local Playwright |
| Report rendering | Jinja2 → WeasyPrint PDF | Templates in `templates/report/` |
| Local review UI | Flask (`scripts/audit_ui.py`) | Clickable link workflow |

---

## Part 6 — Stripe product IDs and payment links

| Product | Stripe URL | Price |
|---|---|---|
| Starter Package | `https://buy.stripe.com/28EdR81OlbU00p51u83cc08` | $19 |
| Scale Up Package | `https://buy.stripe.com/7sY4gy0KhaPWfjZa0E3cc09` | $49 |
| Pro Package | `https://buy.stripe.com/9B600idx36zG3Bha0E3cc03` | $99 |
| Fix Check (standalone) | `https://buy.stripe.com/3cI28q3Wt5vCb3J2yc3cc04` | $19 |
| Handoff Report add-on | `plink_1TbNP9BxCiPye3m0c5A1DNfq` | $49 |
| Tally intake form | `https://tally.so/r/QKOX1A` | N/A |

---

## Part 7 — What to bring to the next app on day one

This is ordered. Don't skip steps.

### Day 1 — Foundation

1. **Init repo:** `python -m venv .venv`, `requirements.txt` pinned, `pyproject.toml` with `[tool.ruff]`
2. **Copy `.cursor/rules/launchlook-defaults.mdc`** — rename it, edit project-specific values (name, numbers, URLs)
3. **Create `scripts/launchlook_constants.py`** with every magic number that appears on the marketing site AND in the worker — this is your single source of truth
4. **Create `tests/test_constants.py`** with drift tests for every constant that appears in two places
5. **Create `scripts/__init__.py`** if you'll have any cross-package imports (Vercel bundling)
6. **Set up Resend** with a custom `User-Agent` header from minute zero — don't wait for the first 403
7. **Create `docs/ROB-REMAINING-TODO.md`** as the single TODO source of truth

### Day 2-3 — Infrastructure

8. **Document all required env vars** in `.env.example` with a one-line comment explaining where to get each one
9. **Notion DB schema as code** — a module listing expected property names + types so a pytest can sanity-check them
10. **One canonical queue worker** that handles every job type through dispatch — no one-off scripts per job type
11. **Vercel project.json** and env vars documented on day one, not retrofitted

### Day 4-7 — Customer-facing

12. **Build the local Flask review UI before the LLM integration.** The UI forces you to define the data schema (YAML structure) before the model has to produce it. Then the LLM prompt mirrors the schema.
13. **HTML + text multipart for all email notifications** from the first `_post_resend()` call
14. **Personal footer template** from day one — not a corporate footer "to refactor later"
15. **`text-center` on status text under CTAs** in the base CSS for forms
16. **URL normalization helper** shared between client JS and server Python
17. **`ruff check` + `ruff format` (specific paths) + `pytest` as the pre-push checklist** — enforce from commit one

---

## Part 8 — Anti-patterns to never repeat

- ❌ Substituting a number you "think is more common" — always grep first
- ❌ Writing "X findings" (not "Up to X") on pricing copy
- ❌ LLM prompts with only a ceiling — always pair with a target range and minimum
- ❌ Silent fallbacks (`.get(key, 7)`) — always log a WARN when the fallback fires
- ❌ Importing from `scripts/` inside `api/*.py` (Vercel bundling breaks)
- ❌ Using `&&` in PowerShell
- ❌ Running `python -m ruff format .` on the whole repo
- ❌ Pushing without all three green: lint, format, pytest
- ❌ Creating new `docs/*.md` files without being asked
- ❌ Writing CLI commands in notification emails when a link would do
- ❌ Plain-text-only email notifications
- ❌ Long mailto URLs in plain-text email bodies
- ❌ Corporate footer — Rob wants a personal bio card
- ❌ Trust Gaps, em-dashes, AI-speak in customer copy
- ❌ Adding a 5th tier, an 8th Tester, or reintroducing any item from `PRODUCT-DECISIONS.md §3`
- ❌ Re-enabling GitHub integration silently
- ❌ Sending customer delivery emails automatically (always requires Rob's manual approval)

---

## Part 9 — What worked unexpectedly well (double down next time)

1. **Inline findings preview in the founder email.** The review is right there in the email. Rob can decide in 5 seconds whether the draft is worth opening.
2. **`canvases/*.canvas.tsx` for project status.** Visual snapshots easier to scan than markdown TODOs.
3. **Stripe + Tally + Notion as the entire backend for v1.** No app database. Cut weeks of work.
4. **One YAML file per customer as the canonical artifact.** Easy to diff, version, and hand-edit when the AI gets something wrong.
5. **`audit_ui.py` Flask wrapper.** A tiny local web UI beats any CLI for a solo-founder workflow.
6. **Drift tests.** `tests/test_launchlook_constants.py` caught the inline Vercel constant immediately. Write drift tests anywhere a number appears in two places.
7. **The human gate.** AI drafts, Rob delivers. This is the product's trust signal and its price justification. Never automate delivery.
8. **`docs/SIMPLICITY-GUARDRAILS.md`.** Having the brand discipline rules as a separate file that workers read before touching customer surfaces prevented a lot of copy drift.
9. **`docs/PRODUCT-DECISIONS.md §3`.** The "deliberately dropped" list prevented re-introducing killed features in later sessions.

---

## Appendix A — Major decisions with rationale

| Date | Decision | Rationale |
|---|---|---|
| 2026-05-25 | Free trial = 2 findings (was 3) | Lower delivery cost, cleaner conversion to Starter ("8 more for $19") |
| 2026-05-26 | Add automation pipeline (worker + Notion queue) | Manual reviews didn't scale past ~5/week |
| 2026-05-26 | Keep human gate before customer delivery | LLM hallucination risk; human curation is the price justification |
| 2026-05-26 | Handoff Report add-on: $99 → $49 | $99 add-on made Scale Up + Handoff = $148 (above Pro $99), so it never sold; $49 makes it $98, just below Pro |
| 2026-05-26 | Verified badge killed | Zero customer demand, maintenance tax on every tier rename |
| 2026-05-26 | Plausible `<script>` pulled | Simplification pass; `plausible-event-name=` classes preserved for one-line re-enable |
| 2026-05-26 | GitHub auto-issues removed from Pro marketing | Dormant code kept; removed from promises |
| 2026-05-26 | Fix Check renamed from Confidence Check (customer-facing only) | "Fix Check" clearer to non-technical buyers; internal routing unchanged |
| 2026-05-27 | Replace Tally Q8 (tier select) with hidden tier from Stripe URL | Cleaner customer flow; tier already implied by the price paid |
| 2026-05-27 | Inline `FREE_AUDIT_DELIVER_COUNT` in `api/free-audit.py` | Vercel bundling issue (see Part 2) |
| 2026-05-27 | Footer = personal card, not LaunchLook brand | Trust signal: "a senior technical writer personally reviews your audit" |
| 2026-05-27 | URL inputs accept bare hostnames | Friction reduction on the top-of-funnel form |
| 2026-05-27 | Pro tier guidance: target 30-40 (not "up to 40") | Pro was producing 7 findings, same as Starter |
| 2026-05-27 | Draft-ready emails: HTML + text multipart | Plain-text mailto URLs leak query string into visible body |
| 2026-05-27 | "Up to X findings" on all pricing cards | Customer who gets 12 real findings feels cheated if copy promises "40" |
| 2026-05-27 | IP theft FAQ + pricing trust note | Real fear at the moment of purchase; addressed with specific, concrete reassurances |

---

## Appendix B — The 7 Testers cast (internal reference)

| Persona | Dev equivalent | What they find |
|---|---|---|
| The Tourist | Happy-path E2E | Confusion, dead ends, unclear CTAs on main path |
| The Skeptic | Trust audit | Missing privacy/terms, dead footer links, no contact info |
| The Klutz | Error handling | Double-submit, back-button mid-flow, lost form data |
| The Snoop | Security-lite | Exposed API keys, public admin routes, missing headers |
| The Phone-First Friend | Mobile audit | Tiny tap targets, broken layouts, viewport bugs |
| The Saboteur | Regression / Fix Check | Things that worked last week and now don't |
| The Stranger Who Tried to Sign Up | Form smoke test | Silent form failures, missing confirmation emails |

**INTERNAL-ONLY** as of 2026-05-26. Tags appear in small text on finding cards only ("Caught by The Snoop"). No marketing use. Max 7 forever.

---

_Last updated: 2026-05-27. Update this file whenever you learn something that
would have saved you time building LaunchLook, or would save time on the next app._
