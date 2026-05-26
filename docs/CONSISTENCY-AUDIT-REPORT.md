# LaunchLook Internal Consistency Audit

Generated: 2026-05-26 12:01 UTC by `scripts/consistency_check.py` (q-final-audit worker)

> **Post-audit regression caught and fixed (2026-05-26, branch `fix/q4-checklist-demote-regression`):**
> q4 (commit `032c4af`) was reported as completed but only the nav link in `landing/index.html` had actually been updated. The hero CTA, the "Not ready to pay?" section, the social-proof checklist button, the referral FAQ copy, the footer link, and parallel surfaces in `landing/webflow.html`, `landing/vs-pagelens.html`, `landing/README.md`, the customer-facing templates in `templates/`, the external GitHub repo at `external/launchlook-prelaunch-checklist/`, and the operator playbooks in `docs/SHARE-AND-REVIEWS.md` + `docs/OUTREACH-PLAYBOOK.md` all still treated the comprehensive checklist as the free lead magnet. This commit (`fix(landing): complete q4 demote-checklist migration`) finishes the migration: the free 3-finding audit is now the only free lead magnet, the comprehensive checklist is consistently positioned as a Scale Up + Pro paid deliverable (already token-gated by q4's `landing/data/checklist_tokens.json`), and the Scale Up + Pro tier cards now explicitly list the comprehensive checklist as included. The community DIY GitHub repo at `external/launchlook-prelaunch-checklist/` remains a free public artifact, reframed as a "community DIY companion" so it doesn't conflict with the paid on-site deliverable. `rg -in "free checklist" landing/` now returns zero matches; the suite is green at 124/124. Counts after rebase on q-deferred-cleanup are 31 issues / 13 needs-review (down from this report's 32 because the removed Free preview pricing card dropped one stale tier name flag; the 13 remaining are the scope-statement and competitor-framing strings q-deferred-cleanup intentionally left below).
> Like q-deferred-cleanup's section, this note will be wiped on the next `scripts/consistency_check.py` run; the canonical record lives in this commit's message and in `docs/ROB-REMAINING-TODO.md`.


Canonical truth sources audited against:
- `docs/SIMPLICITY-GUARDRAILS.md` section 6 (forbidden vocab, em-dash rule)
- `docs/PRODUCT-DECISIONS.md` section 1 (tier ladder, finding caps), section 7 (pricing)
- `docs/TESTERS-CAST.md` (canonical 7-persona spelling)
- `scripts/ai_audit/finding_categories.yaml` (buyer-facing finding category names)
- `api/stripe-webhook.py` (Stripe cents-to-tier mapping)

## Summary

| Check | Total found | Auto-fixed | Needs review |
|---|---|---|---|
| Stale tier names + finding caps | 19 | 0 | 19 |
| Stale prices | 0 | 0 | 0 |
| Forbidden vocabulary | 13 | 0 | 13 |
| Customer-facing em-dashes | 0 | 0 | 0 |
| Persona typos | 0 | 0 | 0 |
| Stale internal category names | 0 | 0 | 0 |
| Stripe routing | 0 | 0 | 0 |

Auto-fix mode: **not applied** (use `--auto-fix-safe` to write changes). Files modified by auto-fix: **0**.

> **Note for future workers:** this file is regenerated end-to-end by `scripts/consistency_check.py`. If you re-run the script, the "Cleanup pass" section below will be wiped. The persistent record of what was resolved lives in `docs/ROB-REMAINING-TODO.md` under the "follow-ups" sections; treat this in-file Cleanup pass as a snapshot, not the source of truth.

## Cleanup pass (q-deferred-cleanup, 2026-05-26)

The deferred-cleanup worker walked the 22 human-review items the prior pass left open and made the following calls.

**Resolved (9 of 22): internal taxonomy -> buyer-facing display names**

Swapped per the canonical map in `scripts/ai_audit/finding_categories.yaml` (the `display_name_buyer` field is the only thing that should appear on customer surfaces; `display_name_internal` stays inside the pipeline).

| File | Before | After |
|---|---|---|
| `landing/index.html:124` | `Trust gaps` (bold lead-in) | `Trust signals and legal pages` |
| `landing/index.html:309` | "Includes a cross-user data check using 2 test accounts" (Scale Up tier paragraph) | "Includes a user data isolation check using 2 test accounts" |
| `landing/index.html:312` | `<li>Cross-user data check (2 test accounts)</li>` (Scale Up bullet) | `<li>User data isolation (2 test accounts)</li>` |
| `landing/index.html:377` | `<td>Cross-user data check</td>` (comparison table row) | `<td>User data isolation</td>` |
| `landing/index.html:417` | `<li>Cross-user data check: -</li>` (mobile Starter card) | `<li>User data isolation: -</li>` |
| `landing/index.html:430` | `<li>Cross-user data check: Γ£ô (2 test accounts)</li>` (mobile Scale Up card) | `<li>User data isolation: Γ£ô (2 test accounts)</li>` |
| `landing/index.html:443` | `<li>Cross-user data check: Γ£ô (2 test accounts)</li>` (mobile Pro card) | `<li>User data isolation: Γ£ô (2 test accounts)</li>` |
| `landing/index.html:517` | FAQ Scale Up paragraph: "a cross-user data check using 2 test accounts ... including the cross-user security check" | "a user data isolation check using 2 test accounts ... including the user data isolation check" |
| `landing/vs-pagelens.html:147` | `<td>Mobile audit</td>` (comparison table row) | `<td>Mobile layout issues</td>` |
| `landing/vs-pagelens.html:208` | `<p>Mobile audit</p>` (mobile card heading) | `<p>Mobile layout issues</p>` |
| `landing/vs-pagelens.html:282` | "Broken CTAs. Dead links." (prose lead-in) | "Broken buttons and dead links." |

The two prose rewrites (lines 309 and 517 in `landing/index.html`) are not strict 1:1 string replacements; the surrounding sentence was lightly restructured so the buyer-facing name flows naturally as a noun phrase ("a user data isolation check ...") rather than a label drop-in. Voice preserved, meaning preserved, per the SIMPLICITY-GUARDRAILS section 6 instruction to use buyer language.

**Reviewed and intentionally left alone (13 of 22): scope statements + anti-pattern framing**

Every remaining "Forbidden vocabulary" row below is a *scope statement* or *anti-pattern framing*, not a brand-voice violation. Each was reviewed manually:

- `"Not a security audit"` / `"not a full security audit"` / `"not a pentest"` are honest scope disclaimers the buyer benefits from reading (LaunchLook is explicitly not a security platform, per `docs/PRODUCT-DECISIONS.md` section 5). Removing them would over-promise.
- `"AI scanner tools that dump 100 findings"` (`landing/index.html:496`, `landing/webflow.html:357`) is anti-pattern framing aimed at *competitor* tools, not a self-description. Per q3 settle, "AI-powered audit + founder review" is the canonical positioning for LaunchLook itself; the prose around line 496 talks about what we are *not*, which is exactly the framing SIMPLICITY-GUARDRAILS section 6 allows. Verified by reading the surrounding paragraph: "Built by a single founder who's tired of [those tools]..." is the founder voice setting up the differentiator.
- `"Is this a security audit?"` (`landing/webflow.html:399`) is an FAQ heading whose answer below explicitly says no. Removing the question would orphan the answer.

The consistency checker's regex flags these because they contain the string `security audit` / `pentest` / `AI scanner`; the human pass here confirms each appearance is a scope-statement or competitor-framing use, not a self-description leak. No rewrite is safe without losing meaning, so they stay.

**Verified clean, no edit needed (separate from the 22):**

- `customers/example-jane-sparkle.yaml` and `customers/example-pro-package.yaml` cap comments. The q-final-lint follow-up flagged `cap 7` / `cap 25` references; the current state already has the canonical caps (`Starter caps at 10`, `Cap raised to 40 findings`). No edits needed; the original flag was stale.
- `scripts/share_report.py --no-commit` flag. Already implemented; this pass adds an explicit suppression test (`tests/test_share_report.py::test_no_commit_flag_suppresses_git_commit`) plus a paired test that the default still auto-commits, and documents the flag in `docs/SHAREABLE-REPORT-WORKFLOW.md` section 3.

**Counts:** 22 walked, 9 resolved, 13 left intentionally with explanation above, 0 left ambiguous.



## Auto-fixed (already applied)

_No auto-safe fixes were applied (none qualified, or run was --report-only)._

## Needs human review

### Stale tier names + finding caps

None remaining.

### Stale prices

None remaining.

### Forbidden vocab still on customer surfaces (13 instances)

| File | Line | Context | Suggested replacement |
|---|---|---|---|
| `landing/checklist.html` | 98 | <p class="mt-4 text-sm text-muted">This is what <em>visitors</em> notice. Not a code review or security audit.</p> | Security jargon. Reframe per SIMPLICITY-GUARDRAILS section 6. ('not a security audit' style scope-statement is OK.) |
| `landing/index.html` | 93 | <p class="text-muted text-sm mt-1">Desktop and phone-sized layout, key flows, trust pages. Not a code audit or security pentest.</p> | Security jargon. Reframe per SIMPLICITY-GUARDRAILS section 6. ('this is not a pentest' style scope-statements are OK; flag exists so human can verify framing.) |
| `landing/index.html` | 127 | ...ility check, not a full security audit.</p> | Security jargon. Reframe per SIMPLICITY-GUARDRAILS section 6. ('not a security audit' style scope-statement is OK.) |
| `landing/index.html` | 496 | Built by a single founder who's tired of "AI scanner" tools that dump 100 findings. Every audit gets a 5-minute human review before it reaches you. | Per q3 settle, 'AI-powered audit + founder review' is the canonical positioning. Verify this usage is anti-pattern framing (talking about competitor tools), not self-description. |
| `landing/terms.html` | 34 | <h2 class="font-serif text-xl mt-10 mb-3">Not a security audit</h2> | Security jargon. Reframe per SIMPLICITY-GUARDRAILS section 6. ('not a security audit' style scope-statement is OK.) |
| `landing/terms.html` | 35 | ...ibility check, not a full security audit. The Pro Package integrations review covers configuration of St... | Security jargon. Reframe per SIMPLICITY-GUARDRAILS section 6. ('not a security audit' style scope-statement is OK.) |
| `landing/verify-scope.html` | 65 | <li>Not a security audit. We do not pen-test, fuzz, or test for OWASP top 10.</li> | Security jargon. Reframe per SIMPLICITY-GUARDRAILS section 6. ('not a security audit' style scope-statement is OK.) |
| `landing/webflow.html` | 357 | Built by a single founder who's tired of "AI scanner" tools that dump 100 findings. Every audit gets a 5-minute human review before it reaches you. | Per q3 settle, 'AI-powered audit + founder review' is the canonical positioning. Verify this usage is anti-pattern framing (talking about competitor tools), not self-description. |
| `landing/webflow.html` | 399 | <summary class="flex justify-between items-center font-medium text-sm">Is this a security audit?<span class="text-muted text-lg">+</span></summary> | Security jargon. Reframe per SIMPLICITY-GUARDRAILS section 6. ('not a security audit' style scope-statement is OK.) |
| `templates/handoff/handoff.html.j2` | 370 | <li>Security posture against motivated attackers (this is not a pentest)</li> | Security jargon. Reframe per SIMPLICITY-GUARDRAILS section 6. ('this is not a pentest' style scope-statements are OK; flag exists so human can verify framing.) |
| `templates/handoff/handoff.html.j2` | 373 | <p>For any of these, get a developer with that specific specialty. Before processing real payments at volume, get a real pentest.</p> | Security jargon. Reframe per SIMPLICITY-GUARDRAILS section 6. ('this is not a pentest' style scope-statements are OK; flag exists so human can verify framing.) |
| `templates/handoff/handoff.md.j2` | 121 | - Security posture against motivated attackers (this is not a pentest) | Security jargon. Reframe per SIMPLICITY-GUARDRAILS section 6. ('this is not a pentest' style scope-statements are OK; flag exists so human can verify framing.) |
| `templates/handoff/handoff.md.j2` | 124 | For any of these, get a developer with that specific specialty. Before processing real payments at volume, get a real pentest. | Security jargon. Reframe per SIMPLICITY-GUARDRAILS section 6. ('this is not a pentest' style scope-statements are OK; flag exists so human can verify framing.) |

### Em-dashes on customer-facing surfaces

None remaining.

### Persona typos

None remaining.

### Stale internal category names

None remaining.

### Stripe routing

None remaining.

## Critical issues (block ship -- must fix)

None.

## Notes for q-final-lint

- After this audit, run linters as planned.
- Em-dash replacements are stylistic: review the surrounding sentence and pick parenthetical / period / comma / colon. Do not bulk-replace globally; meaning gets lost.
- Stale finding caps (Starter cap=10, Scale Up cap=30) and Starter framing copy are surfaced for human review; pricing-page numbers that conflict with PRODUCT-DECISIONS section 1 need a copywriting pass, not a string-replace.
- Re-run this audit at any time with `python scripts/consistency_check.py --report-only` to verify a fix.
