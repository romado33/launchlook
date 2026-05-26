# Best Practices Extraction — 2026-05-26

Source: `C:\Users\RobDods\Apps\Cursor\onceover\bestpractices\`
Articles scanned: **4**
Tidbits extracted: **23** (5 high, 7 medium, 8 validation, 3 rejected)

> **No time-sensitive callouts.** All four articles are 3–8 months old, focused on persistent advice (planning, reviewing, security basics). Nothing makes existing LaunchLook advice stale, and nothing changes a competitor's position vs. the May 2026 `COMPETITIVE-INTEL.md` snapshot. Proceed at normal priority.

---

## The four articles, at a glance

| Filename | Source | Authority | Posture |
|---|---|---|---|
| `Vibe Coding Best Practices_ Avoid the Doom Loop with Planning and Code Reviews.html` | Teresa Torres, Product Talk (Ghost blog), Apr 1 2026 | **High.** Torres is a recognized product-discovery author; this is a long-form article with paid-subscriber transcripts. | Pro-vibe-coding, structured; coins "vibe coding doom loop." Audience: PMs who code. |
| `Vibe Coding Best Practices_ How To Get Consistent Results.html` | Ekene Eze, roadmap.sh | **Medium-high.** roadmap.sh is one of the most-starred dev-learning projects on GitHub. | Tutorial-style "10 best practices" checklist. Audience: devs using Claude Code/Cursor. |
| `How to ACTUALLY make your (vibe coded) apps secure (from an actual hacker) _ r_ChatGPTCoding.html` | u/cryptoviksant, r/ChatGPTCoding (8mo old, 798 upvotes) | **Medium.** Anonymous pentester, anecdotes plausible but uncorroborated. Comments thread adds real signal (geek_404, Key-Boat-7519). | Security checklist + horror stories. Audience: shipping vibe coders. |
| `Vibe coded 30+ apps. Here's how I avoid debugging nightmares (5 steps) _ r_vibecoding.html` | u/Postmortal_Pop, r/vibecoding (4mo old, 266 upvotes) | **Medium-low.** Self-claimed Columbia ML grad, 30+ apps. Practical. | 5-step debugging workflow. Audience: working vibe coders. |

**Signal hierarchy:** Torres > roadmap.sh > Reddit pentester > Reddit debug post. Most extractable advice clusters around two themes: (a) plan-before-code / review-the-diff workflow for the buyer to follow when applying our fixes, and (b) a thin set of new audit checks where missing controls show up on the rendered page.

---

## Top 5 highest-leverage changes (action queue, ranked)

### 1. New finding category: missing bot protection on public forms

- **One-line summary.** Add a check for absent CAPTCHA / Cloudflare Turnstile / honeypot on the signup, contact, and password-reset forms of audited apps.
- **Source article.** `How to ACTUALLY make your (vibe coded) apps secure...html` (cryptoviksant):
  > *"Without it, you're basically paying for spam. Your database fills with garbage, your email service burns through the monthly quota, and boom: One client ended up with a $500+ AWS bill from a single bot attack."*
  Comment by Key-Boat-7519 corroborates: *"Cloudflare Turnstile for bot gating... worked well."*
- **Why it matters for LaunchLook.** Vibe-coded apps ship with public forms by default and almost never wire in a CAPTCHA. The cost-blowout story (wallet pain, not abstract security) is exactly the plain-English wedge the report needs: *"Your contact form has no spam protection — a stranger with a bot could flood your database overnight and burn through your email quota."* It is detectable from a URL-only audit (DOM scan for hCaptcha / reCAPTCHA / Turnstile widget, or honeypot field), so it sits in our existing scope. It also slots cleanly into the `security_lite` Snoop story without breaking the "no pentest, no jargon" rule (per `OUTREACH-PLAYBOOK.md` §6).
- **Specific concrete change.** New entry in `scripts/ai_audit/finding_categories.yaml` — propose `id: bot_protection`, `display_name_buyer: "spam protection on public forms"`, `severity_default: medium`, `tester: "The Snoop"` (so it flows through the existing `security_lite.py` external-source pattern). Companion detector logic in `scripts/ai_audit/security_lite.py` (DOM probe for the three widget signatures). Add corresponding entry in `docs/06-findings-library.md` (new ID after FL-035) with Lovable / Bolt / Generic fix prompts that recommend **Cloudflare Turnstile** specifically (cheap, generous free tier, widely supported — see Key-Boat-7519 + popiazaza in the article comments; reCAPTCHA is increasingly bypassed by AI bots per the same thread).
- **Effort.** Medium (~2 hr): one YAML entry, one DOM-probe function, one findings-library row with three platform prompts.
- **Blocked by.** Nothing technical. Rob decision: confirm we want a fourth Snoop-tagged finding (currently 2: `security_lite` + `cross_user_data`). Recommend yes.

### 2. New finding: mixed-content warnings on HTTPS pages

- **One-line summary.** Flag pages that load HTTP assets (images, scripts, iframes) on an otherwise HTTPS site — Chrome shows a "Not Secure" warning bar that wrecks first-impression trust.
- **Source article.** `How to ACTUALLY make your (vibe coded) apps secure...html`:
  > *"Every endpoint needs HTTPS. Redirect HTTP automatically. Zero exceptions here. I intercept unencrypted traffic during pentests constantly, and you'd be shocked what I see."*
- **Why it matters for LaunchLook.** Vibe-coded apps frequently pull avatar URLs, embeds, or test images from `http://` sources because the AI scaffolds with placeholder URLs and never normalizes them. The browser's "Not Secure" pill is the most visible trust-killer a buyer can ship — exactly what the Skeptic tester would catch. Not currently in `06-findings-library.md` despite being trivially detectable from the page console (mixed-content warnings are logged automatically). The existing `security_lite.py` already inspects HTTP headers; extending it to also scan rendered DOM for `http://` resource URLs is a small lift.
- **Specific concrete change.** Add finding to `docs/06-findings-library.md` (next free FL-ID, in **Performance & polish** or **Trust pages & legal** category — recommend Trust because the visible symptom is the trust-killing browser warning). Add detector in `scripts/ai_audit/security_lite.py` that grep's `http://` (with word boundary) from rendered HTML body, excluding the canonical `http://www.w3.org/` namespace declarations. Customer-facing copy idea: *"Your page is HTTPS but loads {N} things over plain HTTP. Browsers warn visitors when this happens, which scares people away from the page."*
- **Effort.** Small (≤30 min): one detector function, one library entry, three fix-prompt variants.
- **Blocked by.** Nothing.

### 3. Add a "before you paste these fixes" preamble to the QSG PDF

- **One-line summary.** Open every Quick Start Guide with a single short page that tells the buyer to run their AI builder in plan mode and review the diff before accepting any of our fix prompts. Adds value to QSG without breaking `SIMPLICITY-GUARDRAILS.md`.
- **Source article.** Three of the four converge:
  - Torres: *"Instead of iterating in code, I iterate on the plan. ... Every vibe coding session starts with a plan."*
  - Eze: *"Plan Mode workflow ... Without a plan, [agents] can make architectural decisions mid-implementation, change approaches or naming conventions, and create multiple unnecessary files."*
  - Postmortal_Pop step 4: *"Before Claude writes anything, prompt it with something like: 'Before writing any code, explain your approach and identify what could break.'"*
- **Why it matters for LaunchLook.** Today the QSG hands buyers a list of paste-ready prompts. Roughly half of vibe-coder support tickets are "I pasted your prompt and the AI broke three other things." This preamble offloads that risk to the buyer's own process without us doing more work per audit. It also reinforces the trust premium ("here's how to use these like a real engineer would, in plain English") without violating `SIMPLICITY-GUARDRAILS.md` §4 — the rules already allow brand-voice intros, and this stays well clear of "advanced configuration" territory (§4.5).
- **Specific concrete change.** Edit the QSG template under `templates/qsg/` (likely `templates/qsg/qsg_template.html` or whatever the generator points at; do **not** edit per the constraint — Rob actions). Add a single page, ~80 words, plain English: *"Three quick habits before you paste these. (1) Tell your builder to plan, not code, first. (2) Tell it to only touch the file the prompt names. (3) After it's done, ask 'what could break that I haven't tested?' before accepting changes."* No jargon, no `/plan` slash commands (different builders use different syntax — keep it generic per `SIMPLICITY-GUARDRAILS.md` §6 banned-vocab list).
- **Effort.** Small (≤30 min) once Rob actions: one template edit, one regression of the sample report.
- **Blocked by.** Rob decision (does the QSG want a preamble at all, or should this live in the email cover instead?). Recommend QSG because that's where buyers go when they're actively pasting.

### 4. New Reddit/Discord pitch variant — "the vibe coding doom loop" hook

- **One-line summary.** Add a Variant #3.13 to `OUTREACH-PLAYBOOK.md` §3 that opens with the shared vibe-coder vocabulary ("doom loop", "context rot", "scope creep") that's now currency in r/vibecoding and the Lovable Discord.
- **Source article.** Torres explicitly coins it:
  > *"The Vibe Coding Doom Loop ... Every vibe coder eventually has the experience where they end up in the vibe coding doom loop. They encounter a bug, the agent says it fixed it, but it's not fixed."*
  r/vibecoding post (Postmortal_Pop) uses "scope creep" and "mass debugging" — same vocabulary set.
- **Why it matters for LaunchLook.** `OUTREACH-PLAYBOOK.md` §3.4 is canonically the highest-converting variant (reply with 3 specific findings). But its lead-in is generic ("Just clicked through your site"). A second short variant that opens with *"If you're stuck in the doom loop, here's what a first-time visitor would catch before debugging swallows your week..."* would self-select for founders who already have the vocabulary. That self-selection is exactly what `02-strategy-and-context.md` and the playbook's §1 "30 messages → 3 strangers pay $9" math need. Costs nothing to add; opens a new entry-point per channel without touching anything customer-facing.
- **Specific concrete change.** Add §3.13 to `docs/OUTREACH-PLAYBOOK.md` with a ready-to-paste 4-line pitch reusing the §3.4 substitution rules. Keep it strictly Reddit / Discord — do NOT use this on the landing page or in customer-facing reports (the landing page is governed by `SIMPLICITY-GUARDRAILS.md` §2.1: no internal taxonomy). The "doom loop" vocabulary is community-native, not jargon for non-technical buyers, so it's safe in soft outreach only.
- **Effort.** Small (≤30 min): one paragraph in one doc.
- **Blocked by.** Nothing. Suggested wording:

  ```
  If you're stuck in the vibe coding doom loop on {APP_NAME} — keep fixing the same bug, three new ones pop up — here are three things a first-time visitor would notice in the first 30 seconds before any of that:

  1. {Specific thing #1, exact label in quotes}
  2. {Specific thing #2}
  3. {Specific thing #3}

  None of these are doom-loop bugs (those live in your data layer). These are the polish-layer stuff a stranger spots in 30 seconds. Happy to send a quick free pass with 2 to 3 more, DM me your builder.
  ```

### 5. Codify a `PRODUCT-DECISIONS.md` §3 rejection: no IDE plugin, no buyer-side "vibe coding workflow" product

- **One-line summary.** Add a row to the `PRODUCT-DECISIONS.md` §3 dropped-ideas list explicitly rejecting the "LaunchLook IDE plugin / vibe coding workflow tool" wedge. All four articles describe that wedge (CLAUDE.md, plan mode, code-reviewer subagent) — Rob will get pressure to ship it; nail the door shut now.
- **Source article.** Cumulative pattern across all four. Eze's article in particular is **entirely** about workflows that live inside the buyer's IDE, not their deployed URL. The temptation to ship "LaunchLook for Cursor" is real because the audience overlaps perfectly.
- **Why it matters for LaunchLook.** `COMPETITIVE-INTEL.md` §4.1 already flags Cursor Bugbot as **entrenched at PR-level** and explicitly says *"LaunchLook lives upstream of the PR — at the live-URL moment when the vibe coder asks 'is this ready?'"* That positioning is the wedge. An IDE plugin breaks it and puts us in head-on competition with Bugbot, Coderabbit, Snyk, and Tanagram.ai (mentioned in the r/vibecoding comments). The Spec / Requirements helper is already rejected in §3 of `PRODUCT-DECISIONS.md`. Add the IDE-plugin sibling alongside it so the next worker reading the doc sees the line.
- **Specific concrete change.** Edit `docs/PRODUCT-DECISIONS.md` §3. New bullet: *"**IDE plugin / vibe coding workflow tool (CLAUDE.md helpers, code-reviewer subagent, plan-mode prompts).** Wedge mismatch. We live at the live-URL moment, not in the buyer's IDE. Cursor Bugbot, Coderabbit, Snyk, and Tanagram.ai are entrenched here; see `COMPETITIVE-INTEL.md` §4.1. If a worker has a strong case (e.g. customer demand from 30+ paying buyers), write a separate proposal."* Update §9 change log.
- **Effort.** Small (≤15 min).
- **Blocked by.** Nothing. This is pure scope discipline.

---

## All other tidbits (medium / low priority)

| # | Source article | Tidbit | Suggested change | Priority |
|---|---|---|---|---|
| 6 | Torres | The "data / controller / view" three-layer model — bugs appear when the agent updates one layer and forgets the others. Example: change "what's stored" but interface still shows stale shape. | Useful frame for explaining "your interface and underlying data are out of sync" findings in the report. Add as a one-line aside in `docs/06-findings-library.md` severity-calibration section: *"Cross-layer mismatches (UI shows X, data is actually Y) deserve High severity even when individually small."* | Medium |
| 7 | Torres | "Context rot" — agent quality degrades the longer a conversation runs. Recommends fresh sessions between tasks. | Mention once in QSG preamble (item #3 above): *"Open a new chat per fix prompt, don't pile them in one long conversation."* No standalone change. | Medium |
| 8 | Eze | Reference-file pattern: "Before writing any code, read src/routes/users.ts. Match that pattern exactly." | Out of scope for URL-only audit, but useful tone for QSG fix prompts that say "match the existing pattern in your codebase." Could subtly raise prompt quality. Light pass over `findings_library/findings.json` prompts to add *"match the existing patterns in your codebase"* where it doesn't already say so. | Low |
| 9 | Eze | The "diff review" checklist (file deletions, public API changes, new deps, schema changes, secrets). | Material for a Pro-tier Handoff Report section: *"Things to check in the next AI-generated diff after applying these fixes."* Adds defensible Pro-tier polish without code. | Medium |
| 10 | Eze | Migration plan pattern (forward SQL, down SQL, rollback) before any schema change. | Out of scope for URL-only audit. Possible mention in Pro Handoff Report. | Low |
| 11 | Postmortal_Pop | Self-updating rules file (`CLAUDE.md` / `.cursorrules` / project context doc). | Out of LaunchLook's scope (this is buyer-side IDE setup). Validation only — explicitly DO NOT productize this; see Top-5 item #5. | Low / Validation |
| 12 | Postmortal_Pop | Commit before every "quick fix." | Out of scope (URL-only audit). Could mention in QSG preamble alongside item #3. | Low |
| 13 | Postmortal_Pop | "Scope lock" — *"Only modify [specific file]. Do not touch anything else unless you ask first."* | Already baked into our existing fix prompts (e.g. FL-001: *"Don't change any code structure or styling — only the visible text"*). Light pass to make sure every fix prompt in `findings_library/findings.json` ends with a scope-lock clause. | Medium |
| 14 | cryptoviksant | Rate limiting (100 req/hr per IP) to stop AWS-bill bot attacks. | **Not URL-detectable** without active probing. Out of scope for the scanner. Could surface in Pro Handoff Report as a single line: *"Confirm rate-limiting is on the auth and contact endpoints (Cloudflare or Supabase plan-level)."* | Low |
| 15 | cryptoviksant | Dependabot / Renovate / 90-day key rotation. | Out of URL-only scope. Possibly worth a single line in the Handoff Report. | Low |
| 16 | cryptoviksant + comments | "Sanitize every input" → stored XSS, CSRF, SQL injection. | Out of URL-only scope. Reject as a finding category. | Low |
| 17 | cryptoviksant comment (geek_404) | "Default-deny inbound AND outbound" — many vibe-coded apps fire third-party requests that leak data without realizing it. | **Partially detectable** — we can flag unexpected outbound calls visible in the page's Network panel (e.g. unrecognized analytics domains, mystery SaaS endpoints). Could be a future addition. | Low |
| 18 | cryptoviksant comment (geek_404) | "Only collect data you actually need" — data privacy minimization. | Aligns with our Skeptic / privacy-page findings (FL-008 family). Validation only. Could add a single Pro-tier check: *"Does the signup form ask for data the product doesn't need?"* | Low |
| 19 | Postmortal_Pop comment (You--Know--Whoo) | Mentions tanagram.ai as a tool that "enforces accumulated rules in the code, not just documented." | Add to `docs/COMPETITIVE-INTEL.md` Tier 1 watch-list (not Tier 1 competitor — different shape, lives in the IDE per item #5). Note as adjacent. | Low |

---

## Tidbits we already cover (validation)

| # | Source article | Tidbit | Where we already do it |
|---|---|---|---|
| V1 | cryptoviksant | RLS / row-level security / cross-user data isolation | `scripts/ai_audit/finding_categories.yaml` → `cross_user_data` (Scale Up + Pro). `docs/06-findings-library.md` FL-021. `PRODUCT-DECISIONS.md` §8. |
| V2 | cryptoviksant | Hidden API keys, exposed credentials in rendered HTML | `finding_categories.yaml` → `security_lite` (Snoop), source: external. `scripts/ai_audit/security_lite.py`. |
| V3 | cryptoviksant | HTTPS everywhere / HSTS / security headers | `security_lite` Snoop entry: *"HSTS / CSP / X-Frame-Options / X-Content-Type-Options headers."* |
| V4 | cryptoviksant | "AI writes code; another AI audits; you review." Hybrid AI + human pattern. | This is **exactly** our positioning ("AI-drafted, founder-curated"). See `OUTREACH-PLAYBOOK.md` §1 — *"AI scans every screen, I personally review and curate every finding."* Torres explicitly codifies the same pattern as plan-reviewer + code-reviewer in her article. **Strong third-party validation that the wedge is correct.** Worth quoting in `/vs-pagelens` content. |
| V5 | Eze | Off-limits zones in CLAUDE.md (auth/payments/middleware/migrations) | Mirrors our Snoop tester's beat: auth, billing, cross-user data. The same axes show up under `cross_user_data` and `security_lite`. |
| V6 | Postmortal_Pop | MCP servers for context | Already on the deferred queue per `PRODUCT-DECISIONS.md` §4 + `COMPETITIVE-INTEL.md` §4.3 ("MCP server / Cursor integration" listed as high-leverage feature bet). |
| V7 | Torres | Plan-review-fix and implement-review-fix cycles | Same shape as our pipeline (AI drafts findings → Rob reviews → release). Validation. |
| V8 | Postmortal_Pop comment (sogasg) | "AI is performing much better with test-driven development." | Out of LaunchLook's product scope, but reinforces V4 — humans-in-the-loop are the differentiator. Validation only. |

---

## Tidbits we deliberately rejected

| # | Source article | Tidbit | Reason rejected |
|---|---|---|---|
| R1 | All four articles | Build an IDE plugin / vibe coding workflow / CLAUDE.md helper / code-reviewer subagent product | **Wedge mismatch.** `COMPETITIVE-INTEL.md` §4.1 explicitly positions LaunchLook as "upstream of the PR — at the live-URL moment." Cursor Bugbot, Coderabbit, Snyk, Tanagram.ai own that lane. See Top-5 item #5 to codify this in `PRODUCT-DECISIONS.md` §3. |
| R2 | Torres + Eze | Multi-agent consensus / multiple agents converging on the same diagnosis | `COMPETITIVE-INTEL.md` §4.3 graveyard: *"Multi-model AI consensus ... sounds smart, costs you in compute, doesn't move conversion."* |
| R3 | cryptoviksant | "GitHub bots are scraping for exposed AWS keys 24/7" → recommend full-repo SAST | **Code/repo access is explicitly out of scope.** `PRODUCT-DECISIONS.md` §3 deferred "Migration helper" because it needs repo access. `OUTREACH-PLAYBOOK.md` §5 forbidden words: "security audit," "pentest." Rendered-HTML secret-scanning (V2 above) is our scoped version. |

---

## Cross-references to existing docs

- **`COMPETITIVE-INTEL.md`** already establishes the "human-in-the-loop is the wedge" positioning. The Torres article (item V4) is independent corroboration from a high-authority source — worth a citation when the `/vs-pagelens` page gets written. The Reddit articles add community-vocabulary (item #4: "doom loop") and a comment-thread mention of Tanagram.ai (item #19) that should be tracked in the next competitive update.
- **`OUTREACH-PLAYBOOK.md` §3.4** is the highest-converting variant (reply with 3 findings). Item #4 (new §3.13 "doom loop" hook) extends this without replacing it.
- **`PRODUCT-DECISIONS.md` §3** is the right home for the IDE-plugin rejection (Top-5 #5). Note that §3 already rejects the Spec / Requirements helper — IDE plugin is its sibling.
- **`SIMPLICITY-GUARDRAILS.md` §2 + §6** governs the "doom loop" vocabulary boundary: keep it in outreach (Reddit/Discord), banned on landing/report/QSG. Item #4 respects this.
- **`docs/06-findings-library.md`** is where the two new finding entries (Top-5 #1 bot protection + #2 mixed-content) land. The new entries should be FL-036 and FL-037 in the existing numbering scheme.
- **`scripts/ai_audit/finding_categories.yaml`** gets one new category (`bot_protection`) tied to the Snoop tester, mirroring the existing `security_lite` external-source pattern.
- **`scripts/ai_audit/security_lite.py`** is where the two new detector functions live (DOM probe for CAPTCHA widgets; HTTP-URL grep for mixed content).
- **`templates/qsg/`** (Top-5 #3 preamble) — owner: Rob. Not edited in this branch per the constraint.

---

## Notes on the articles themselves

**Voice / authority / freshness:**

- **Torres article (Apr 1 2026).** Strongest signal in the folder. She's a credentialed product-discovery author and the article is calm, structured, and free of hype. Her plan-reviewer + code-reviewer architecture is **the same shape** as LaunchLook's AI-drafted/founder-curated pipeline. Treat as a citable authority when building `/vs-pagelens` and any "why human review matters" copy. Caveat: the second half ("paid subscribers get full transcripts") was paywalled in the saved HTML — we have the top ~50% only, which is the framework portion. The transcripts would add color but the actionable content is already in what we can read.

- **Ekene Eze / roadmap.sh article.** Tutorial-style; reads like a checklist for working devs. Authoritative within its audience (roadmap.sh has ~355K GitHub stars per the article footer). Less directly translatable to LaunchLook's audit product because most of its content is buyer-side workflow advice, not auditable-on-the-live-URL signal. Strong corroboration that humans must review AI diffs — same line as Torres and cryptoviksant.

- **cryptoviksant Reddit post (8mo old).** Locked, stickied, archived, 798 upvotes — meaning it's been promoted by mods and is now considered a community reference. The author admits to using ChatGPT as a translator, which is plausible (some commenters dispute this; not material). The **comment thread** is at least as valuable as the post: geek_404, Key-Boat-7519, popiazaza, and tinkeringidiot add real depth on supply-chain, default-deny networking, Cloudflare Turnstile, and dependency hygiene. Specifically:
  - Key-Boat-7519: *"Kill stored XSS and SSRF first in chat apps... Cloudflare Turnstile for bot gating and Auth0 for JWTs worked well."*
  - popiazaza: *"Captcha nowadays do a lot more verification from network usage. Big players like Google and Cloudflare do a great job of that."*
  - tinkeringidiot: *"Dependabot is great, but it can't see past your package manager. Every one of those packages you installed has its own dependencies."*

- **Postmortal_Pop Reddit post (4mo old, 266 upvotes).** Practical, less authoritative, but the **5-step workflow** is now well-distributed vocabulary in r/vibecoding. The "scope creep is the silent killer" framing is directly useful for our outreach voice. The author's claim of "30+ apps shipped" is unverifiable but the advice is consistent with the other three articles. Comments add: TDD-as-quality-signal (sogasg), tanagram.ai as a rules-enforcement tool (You--Know--Whoo), `diary.txt` as an alternative to letting the AI update its own ruleset (moxyte).

**Strongest signal:** Torres > comments under cryptoviksant > Eze > Postmortal_Pop main post.
**Weakest signal:** speculation about commenter motives (some of the cryptoviksant pushback is "this is AI-translated"); we can ignore that meta-discussion.

---

*End of extraction. Decisions to action are in the Top 5 list above; rest is reference material.*
