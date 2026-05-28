# Lessons learned — building LaunchLook

A retrospective of everything we troubleshot, every recurring correction Rob had
to give me, and every "next time, do this from day one" insight. Written so the
**next app** ships faster.

Pair this with [`.cursor/rules/launchlook-defaults.mdc`](../.cursor/rules/launchlook-defaults.mdc),
which encodes the recurring corrections as a Cursor rule any agent will read
automatically. Copy that rule file (renamed) into the next repo on day one.

---

## Part 1 — Recurring corrections Rob had to give me

These are the patterns I (the AI) defaulted to wrong, often multiple times.
**Pin these to memory for the next app.**

### 1. Numbers in the product spec are sacred

If Rob says "2 findings", "$19 Starter", "40 Pro findings", "10 Starter",
"30 Scale Up", I should never quietly substitute different numbers — even if
my training prior says "3 is a more common free tier". Always grep the
constants file (`scripts/launchlook_constants.py` here) before changing a
number, and update **every** call site at once.

Examples I got wrong here:
- Free trial: I kept writing 3 instead of 2.
- Pro tier: prompt produced 7 findings when cap was 40 (the cap was right, the
  *prompt language* was wrong — see §10).

### 2. Brand voice is informal, not jargon

- ❌ "Trust Gaps" → ✅ "embarrassing bugs"
- ❌ "native apps" → ✅ "desktop and mobile width testing"
- ❌ "synergize", "leverage", "ideate"
- ❌ em-dashes anywhere in customer-facing copy or finding output

The voice rule lives in the LLM system prompt for findings; mirror the same
voice in landing copy, FAQ, and email body.

### 3. Center text by default for status / disclaimer copy under CTAs

I keep leaving these left-aligned. Pattern: `<p class="... text-center">` for
anything between a primary CTA and the next section header (status messages,
disclaimers, microcopy, "no credit card needed", etc.).

### 4. Personal contact card, not corporate footer

Rob does not want a "LaunchLook" branded footer. He wants:
- His name (`Made by Rob Dods`)
- One-line bio (15+ years technical writer, personally reviews every audit)
- One contact link (email)
- One social link (LinkedIn)

And nothing else. No newsletter signup. No "Company / Product / Legal"
columns. No duplicate email links elsewhere on the same page.

### 5. URL inputs accept bare hostnames

Users will type `mysite.com`, not `https://mysite.com`. Normalize **both**:
- Client-side JS before submit
- Server-side in the API handler

The validation regex must accept either form. Test with `mysite.com`,
`https://mysite.com`, `http://localhost:3000` (reject), and `not-a-url`.

### 6. PowerShell is the shell — write commands accordingly

- ❌ `cmd1 && cmd2 && cmd3` → ✅ `cmd1; if ($?) { cmd2 }; if ($?) { cmd3 }`
- ❌ Heredocs (`<<EOF`) → ✅ Here-strings (`@"..."@`) or `-F filename`
- ❌ Unicode in `print()` without setting `$env:PYTHONIOENCODING="utf-8"`
- When stderr writes happen, PowerShell wraps them in `NativeCommandError`
  even on exit 0 — read the actual output before assuming failure.

### 7. Reduce CLI friction in the founder workflow

Rob wants to click things, not type commands. Pattern:
- Email notifications include **clickable links** to a local web UI
- The local web UI handles editing AND preview
- A "deliver" button creates a pre-filled mailto so he doesn't compose from
  scratch
- Terminal commands appear in the email only as fallbacks for when the server
  isn't running

If I find myself writing instructions like "now run `python scripts/foo.py
--slug=...`", I should ask: can this be a link in the email instead?

### 8. Don't create files unless asked

Rob explicitly does not want me proactively creating new markdown files,
canvases, or docs as a side effect of solving a different problem. The
exceptions are:
- Updating `docs/ROB-REMAINING-TODO.md` (this is the canonical TODO)
- Updating the project snapshot canvas (`canvases/*.canvas.tsx`)
- Updating files he explicitly named in the conversation

When I want to create a new doc, **ask first**.

### 9. Always lint + test before pushing

Standing pre-commit checklist:
```
python -m ruff check <changed-files>
python -m ruff format <changed-files>
python -m pytest tests/ -x -q
```
No commit without all three green. Rob does not want me to commit broken
code "to iterate quickly".

### 10. LLM prompts: targets, not ceilings

"Up to N" is a ceiling and produces under-delivery. Use **target ranges**
with explicit minimums per tier, paired with an anti-padding guardrail:

> "Target 25-40 findings. If you return fewer than 25, you have not looked
> hard enough. **You may NOT invent findings to pad the count** — if a
> category truly does not apply, skip it. But the target minimum exists
> because most live apps genuinely have that many real issues."

Pattern is in `scripts/ai_audit/pipeline.py` `_tier_guidance()`.

### 11. Commit messages: 1 line, present tense, scoped

Pattern: `<scope>: <one-line summary in present tense>`

Examples that worked:
- `fix(audit): make tier guidance target minimums so Pro audits hit ~30-40 findings, not 7`
- `landing: center the form status + disclaimer text under the submit button`
- `fix(api): inline FREE_AUDIT_DELIVER_COUNT to fix Vercel function crash`

Avoid: multi-line bodies (Rob doesn't read them), conventional-commits ceremony
for tiny changes, emojis.

---

## Part 2 — Technical pitfalls and how we solved them

Things that bit us. Bookmark these for the next app.

### Vercel Python serverless functions

**Problem**: `FUNCTION_INVOCATION_FAILED` at cold start when `api/*.py`
imports from sibling top-level modules (e.g. `from scripts.launchlook_constants
import X`).

**Root cause**: Vercel's Python runtime sometimes fails to bundle top-level
modules even with `__init__.py` present. Imports work locally, fail on cold
start.

**Fix that actually worked**:
1. Add `scripts/__init__.py` (necessary but not sufficient)
2. **Inline critical constants** into the API file itself
3. Add a test that fails if the inline value drifts from the canonical one

Code pattern (`tests/test_launchlook_constants.py`):
```python
def test_api_inline_constant_matches() -> None:
    src = (REPO_ROOT / "api" / "free-audit.py").read_text("utf-8")
    match = re.search(r"^FOO\s*=\s*(\d+)", src, re.MULTILINE)
    assert int(match.group(1)) == FOO  # canonical
```

**For next app**: keep `api/*.py` self-contained from day one. If you need
shared logic, prefer copying small constants and writing a drift test over
importing from `scripts/`.

### Resend + Cloudflare WAF

**Problem**: Resend API calls returned `HTTP 403` with Cloudflare error 1010.

**Root cause**: Cloudflare in front of Resend blocks the default
`Python-urllib/X.Y` User-Agent.

**Fix**: Always set an explicit `User-Agent` header on outbound HTTP calls:
```python
"User-Agent": "AppName/1.0 (+https://yoursite.com)"
```

Applies to **all** third-party APIs behind Cloudflare (Stripe, Notion's own
WAF, etc.). Default to setting UA on day one.

### Email rendering — long mailto URLs leak as plain text

**Problem**: A `mailto:foo@bar.com?subject=X&body=<huge URL-encoded blob>`
in a plain-text email body gets only its first segment autolinked by Gmail;
the rest spills into the visible body as `%20`-encoded garbage. Looks broken.

**Fix**: Always send notifications as **multipart HTML + text** (Resend
`html` + `text` fields). Put the long URL inside `<a href="...">friendly
text</a>` in the HTML version. The plain-text version uses a short subject-
only mailto as fallback.

Pattern is in `scripts/audit_automation/notify.py`.

### Notion property normalization

**Problem**: Notion select values come back as the raw label, which often
includes pricing/decoration (`"Pro Package ($99)"`). Downstream code that
does `caps[tier]` then KeyErrors silently and falls back to a default.

**Fix**: Centralize a normalization table at the boundary:
```python
TIER_NORMALIZE = {
    "pro package": "Pro Package",
    "pro package ($99)": "Pro Package",
    "pro": "Pro Package",
    ...
}
tier = TIER_NORMALIZE.get(raw.lower(), raw or "DEFAULT")
```

And log a `WARN` when an unrecognised value falls through, so silent drift
becomes loud.

### LLM structured output schemas

**Problem**: OpenAI's `response_format={"type":"json_schema",...}` requires
every property listed in `properties` to also be in `required`, or the
generation silently drops fields.

**Fix**: When defining the schema, just put **every** property name into
`required`. Use `"description"` to mark fields that are "optional in meaning"
— the model fills them with empty string when not applicable.

### Playwright on Windows — encoding & path issues

**Problem**: Playwright stdout includes Unicode (✓, →) which crashes Python
on Windows consoles with `UnicodeEncodeError`.

**Fix**:
1. Set `os.environ["PYTHONIOENCODING"] = "utf-8"` at the top of any Playwright
   wrapper script.
2. Replace Unicode arrows in your own `print()` with ASCII (`->`).
3. For PowerShell sessions: `$env:PYTHONIOENCODING="utf-8"` before running
   the script.

### Ruff format drift on unrelated files

**Problem**: Running `ruff format` on the whole repo can produce cosmetic
diffs on files you weren't editing (collapsed multi-line args, etc.), making
the diff noisy and the PR hard to review.

**Fix**: Always pass **specific paths** to `ruff format`, never the whole
repo. If you accidentally formatted everything, `git checkout HEAD -- <files>`
to revert the unintended changes.

### Stripe webhook → Notion → worker pipeline

**Problem**: Three systems with different latencies; hard to know which step
failed when a customer reports "I paid but nothing happened".

**Fix**: Status enum on every Notion row that progresses through states:
`queued → processing → draft_ready → delivered → fix_check_pending`. Each
worker step transitions the status. Founder dashboard query: "show me
everything stuck in `processing` > 1 hour".

### Local Flask UI for founder review

**Problem**: I initially built only a CLI for review. Rob wanted clickable
links from email → web editor → live PDF preview.

**Fix**: Tiny Flask app (`scripts/audit_ui/app.py`), routes:
- `/review/<slug>` — JSON-form editor that writes back to YAML
- `/preview/<slug>` — renders the actual report template (Jinja → HTML),
  same template the PDF pipeline uses
- `/api/bootstrap?slug=&review_ai=1` — JSON for the JS frontend

For the next app: **build the local Flask UI on day one**, not as an
afterthought.

---

## Part 3 — Things to bring to the next app from day one

Order matters. This is a "first week of the next project" checklist.

### Day 1 — Foundation

1. **Init repo** with `python -m venv .venv`, `requirements.txt` pinned,
   `pyproject.toml` with `[tool.ruff]` config.
2. **Create `.cursor/rules/<projectname>-defaults.mdc`** (copy from this
   repo, edit project name + numbers).
3. **Create `tests/test_constants.py`** with drift tests for every magic
   number that appears in both code and customer-facing copy.
4. **Create `scripts/__init__.py`** if you'll have any cross-package imports.
5. **Set up Resend + a `_post_resend()` helper** with the User-Agent header
   from minute zero. Don't wait until the first 403.
6. **Add `docs/ROB-REMAINING-TODO.md`** as the single source of truth for
   what's left to do manually.

### Day 2-3 — The boring infrastructure

7. **Vercel `.vercel/project.json` + env vars** documented in
   `docs/AUTOMATION-SETUP.md`. List every required var with a one-line
   description and where to get it.
8. **Notion DB schemas** as code (a `notion_schema.py` module listing the
   expected property names + types) so a `pytest` test can sanity-check
   them.
9. **One canonical `process_queue.py` worker** that handles every kind of
   job through dispatch. Avoid one-off scripts per job type.

### Day 4+ — Customer-facing

10. **Build the local Flask review UI before the LLM integration.** The UI
    forces you to define the data model (YAML schema) before the model has
    to produce it. Then the LLM prompt mirrors the schema, not the other
    way around.
11. **HTML + text multipart for all email notifications** from the first
    `_post_resend()` call.
12. **PowerShell-safe commands in every README and runbook.** No `&&`,
    no heredocs, no Unicode in print statements.

### Day 7 — Polish loop

13. **Footer template** is a personal card from the start. Don't build a
    corporate footer "and refactor later".
14. **Center status text under CTAs** in the base CSS for forms.
15. **URL-input normalization helper** shared between client JS and server
    Python.

---

## Part 4 — Anti-patterns I should never repeat

- ❌ Inventing a number when uncertain. Always grep first.
- ❌ Writing customer-facing copy without checking the brand-voice rules in
  `.cursor/rules/`.
- ❌ Running `ruff format .` instead of `ruff format <specific-paths>`.
- ❌ Pushing without `pytest` green.
- ❌ Creating a new `docs/*.md` without being asked.
- ❌ Suggesting CLI commands when a clickable link would do.
- ❌ Plain-text-only email notifications.
- ❌ Importing from `scripts/` inside `api/*.py` (Vercel).
- ❌ Using `&&` in PowerShell.
- ❌ Defaulting to "up to N" in LLM prompts for tier-based products.
- ❌ Leaving silent fallbacks (`.get(key, 7)`) — always log a WARN.

---

## Part 5 — What worked unexpectedly well

Things to **double down on** in the next app.

1. **Inline findings preview in the founder email.** No "click to see findings"
   button. The review is right there. Rob can decide in 5 seconds whether the
   draft is worth opening.
2. **`canvases/*.canvas.tsx` for project status.** Visual snapshots of the
   state of the world were easier for Rob to scan than markdown TODOs.
3. **Stripe + Tally + Notion as the entire backend** for v1. No app database.
   Cut weeks of work.
4. **One YAML file per customer** as the canonical artifact. Easy to diff,
   easy to version, easy to hand-edit when the AI gets something wrong.
5. **`audit_ui.py` Flask wrapper.** A tiny local web UI > any CLI for
   founder workflows.
6. **Drift tests.** `tests/test_launchlook_constants.py` caught the inline
   Vercel constant immediately. Add similar tests anywhere a number appears
   in two places.

---

## Appendix — Chronicle of major decisions

Rough timeline of the big calls made during LaunchLook v1, in case the
context helps explain why something is the way it is.

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-05-25 | Free trial = 2 findings (was 3) | Lower delivery cost, easier to convert to Starter ($19 = 8 more) |
| 2026-05-26 | Add automation pipeline (worker + queue) | Manual reviews didn't scale past ~5/week |
| 2026-05-26 | Keep human gate before customer delivery | LLM hallucination risk too high to auto-ship |
| 2026-05-27 | Replace Tally Q8 with hidden tier from Stripe URL | Cleaner customer flow; tier is already implied by the price they paid |
| 2026-05-27 | Inline `FREE_AUDIT_DELIVER_COUNT` in api/ | Vercel bundling issue (see Part 2) |
| 2026-05-27 | Footer = personal card, not LaunchLook brand | Trust signal: founder is reviewing your stuff personally |
| 2026-05-27 | Free trial URL inputs accept bare hostnames | Friction reduction in the top-of-funnel form |
| 2026-05-27 | Pro tier guidance: target 25-40 (not "up to 40") | Pro was producing 7 findings, same as Starter |
| 2026-05-27 | Draft-ready emails: HTML + text multipart | Plain-text mailto URLs leak query string into body |

---

_Last updated: 2026-05-27. Update when you ship something you wish you'd
known on day one._
