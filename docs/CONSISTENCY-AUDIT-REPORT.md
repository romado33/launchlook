# LaunchLook Internal Consistency Audit

Generated: 2026-05-26 08:12 UTC by `scripts/consistency_check.py` (q-final-audit worker)


Canonical truth sources audited against:
- `docs/SIMPLICITY-GUARDRAILS.md` section 6 (forbidden vocab, em-dash rule)
- `docs/PRODUCT-DECISIONS.md` section 1 (tier ladder, finding caps), section 7 (pricing)
- `docs/TESTERS-CAST.md` (canonical 7-persona spelling)
- `scripts/ai_audit/finding_categories.yaml` (buyer-facing finding category names)
- `api/stripe-webhook.py` (Stripe cents-to-tier mapping)

## Summary

| Check | Total found | Auto-fixed | Needs review |
|---|---|---|---|
| Stale tier names + finding caps | 9 | 0 | 9 |
| Stale prices | 0 | 0 | 0 |
| Forbidden vocabulary | 19 | 0 | 19 |
| Customer-facing em-dashes | 19 | 0 | 19 |
| Persona typos | 0 | 0 | 0 |
| Stale internal category names | 9 | 0 | 9 |
| Stripe routing | 0 | 0 | 0 |

Auto-fix mode: **not applied** (use `--auto-fix-safe` to write changes). Files modified by auto-fix: **0**.

## Auto-fixed (already applied)

_No auto-safe fixes were applied (none qualified, or run was --report-only)._

## Needs human review

### Stale tier names + finding caps (9 instances)

| File | Line | Context | Suggested replacement |
|---|---|---|---|
| `landing/index.html` | 140 | <p class="text-sm text-muted mb-5">🟡 Needs a few fixes before sharing publicly · 5 findings (priority triage — Starter caps at 7)</p> | Replaced in q3 with plain-English Starter framing per PRODUCT-DECISIONS section 7. Replace with 'top issues' or 'the most important findings'. |
| `landing/index.html` | 290 | <p class="text-sm text-accent mt-1 font-medium uppercase tracking-widest">Priority triage</p> | Replaced in q3 with plain-English Starter framing per PRODUCT-DECISIONS section 7. Replace with 'Top issues' or similar. |
| `landing/index.html` | 360 | <td class="px-4 py-3 align-top text-ink font-medium">Priority triage</td> | Replaced in q3 with plain-English Starter framing per PRODUCT-DECISIONS section 7. Replace with 'Top issues' or similar. |
| `landing/index.html` | 413 | <p class="text-sm text-ink font-medium">Priority triage</p> | Replaced in q3 with plain-English Starter framing per PRODUCT-DECISIONS section 7. Replace with 'Top issues' or similar. |
| `landing/index.html` | 516 | ...($19)</strong> is priority triage — we identify the top 7 issues a first-time visitor would notice and ne... | Replaced in q3 with plain-English Starter framing per PRODUCT-DECISIONS section 7. Replace with 'top issues' or 'the most important findings'. |
| `landing/index.html` | 140 | <p class="text-sm text-muted mb-5">🟡 Needs a few fixes before sharing publicly · 5 findings (priority triage — Starter caps at 7)</p> | Starter cap was bumped to 10. Update to 'Starter caps at 10' per PRODUCT-DECISIONS section 1. |
| `landing/index.html` | 367 | <td class="px-4 py-3 align-top text-ink">Up to 25 across all categories</td> | Scale Up cap was bumped to 30 (was 25). Verify whether 'Up to 25' should be 'Up to 30'. |
| `landing/index.html` | 415 | <li>Findings: the 7 most important</li> | Starter cap was bumped to 10 (was 7). Verify whether '7 most important' should be '10 most important'. |
| `landing/index.html` | 517 | ...rehensive audit — up to 25 findings across every category, plus a cross-user data check using 2 test accoun... | Scale Up cap was bumped to 30 (was 25). Verify whether '25 findings' should be '30 findings'. |

### Stale prices

None remaining.

### Forbidden vocab still on customer surfaces (19 instances)

| File | Line | Context | Suggested replacement |
|---|---|---|---|
| `landing/checklist.html` | 98 | <p class="mt-4 text-sm text-muted">This is what <em>visitors</em> notice. Not a code review or security audit.</p> | Security jargon. Reframe per SIMPLICITY-GUARDRAILS section 6. ('not a security audit' style scope-statement is OK.) |
| `landing/index.html` | 93 | <p class="text-muted text-sm mt-1">Desktop and phone-sized layout, key flows, trust pages. Not a code audit or security pentest.</p> | Security jargon. Reframe per SIMPLICITY-GUARDRAILS section 6. ('this is not a pentest' style scope-statements are OK; flag exists so human can verify framing.) |
| `landing/index.html` | 127 | ...ility check, not a full security audit.</p> | Security jargon. Reframe per SIMPLICITY-GUARDRAILS section 6. ('not a security audit' style scope-statement is OK.) |
| `landing/index.html` | 308 | <p class="text-sm text-accent mt-1 font-medium uppercase tracking-widest">Comprehensive audit</p> | Vocabulary list per SIMPLICITY-GUARDRAILS section 6. Only 'comprehensive checklist' is allowed (PRODUCT-DECISIONS section 8). Reword. |
| `landing/index.html` | 361 | <td class="px-4 py-3 align-top text-ink font-medium">Comprehensive audit</td> | Vocabulary list per SIMPLICITY-GUARDRAILS section 6. Only 'comprehensive checklist' is allowed (PRODUCT-DECISIONS section 8). Reword. |
| `landing/index.html` | 426 | <p class="text-sm text-ink font-medium">Comprehensive audit</p> | Vocabulary list per SIMPLICITY-GUARDRAILS section 6. Only 'comprehensive checklist' is allowed (PRODUCT-DECISIONS section 8). Reword. |
| `landing/index.html` | 496 | Built by a single founder who's tired of "AI scanner" tools that dump 100 findings. Every audit gets a 5-minute human review before it reaches you. | Per q3 settle, 'AI-powered audit + founder review' is the canonical positioning. Verify this usage is anti-pattern framing (talking about competitor tools), not self-description. |
| `landing/index.html` | 517 | ...49)</strong> is a comprehensive audit — up to 25 findings across every category, plus a cross-user data check... | Vocabulary list per SIMPLICITY-GUARDRAILS section 6. Only 'comprehensive checklist' is allowed (PRODUCT-DECISIONS section 8). Reword. |
| `landing/index.html` | 622 | <p><strong class="text-ink">The Stranger Who Tried to Sign Up.</strong> Fills the actual forms with safe synthetic values, end to end.</p> | Internal jargon. Use plain-English 'safe test data' or similar. |
| `landing/terms.html` | 34 | <h2 class="font-serif text-xl mt-10 mb-3">Not a security audit</h2> | Security jargon. Reframe per SIMPLICITY-GUARDRAILS section 6. ('not a security audit' style scope-statement is OK.) |
| `landing/terms.html` | 35 | ...ibility check, not a full security audit. The Pro Package integrations review covers configuration of St... | Security jargon. Reframe per SIMPLICITY-GUARDRAILS section 6. ('not a security audit' style scope-statement is OK.) |
| `landing/verify-scope.html` | 65 | <li>Not a security audit. We do not pen-test, fuzz, or test for OWASP top 10.</li> | Security jargon. Reframe per SIMPLICITY-GUARDRAILS section 6. ('not a security audit' style scope-statement is OK.) |
| `landing/webflow.html` | 357 | Built by a single founder who's tired of "AI scanner" tools that dump 100 findings. Every audit gets a 5-minute human review before it reaches you. | Per q3 settle, 'AI-powered audit + founder review' is the canonical positioning. Verify this usage is anti-pattern framing (talking about competitor tools), not self-description. |
| `landing/webflow.html` | 399 | <summary class="flex justify-between items-center font-medium text-sm">Is this a security audit?<span class="text-muted text-lg">+</span></summary> | Security jargon. Reframe per SIMPLICITY-GUARDRAILS section 6. ('not a security audit' style scope-statement is OK.) |
| `landing/webflow.html` | 475 | <p><strong class="text-ink">The Stranger Who Tried to Sign Up.</strong> Fills the actual forms with safe synthetic values, end to end.</p> | Internal jargon. Use plain-English 'safe test data' or similar. |
| `templates/handoff/handoff.html.j2` | 370 | <li>Security posture against motivated attackers (this is not a pentest)</li> | Security jargon. Reframe per SIMPLICITY-GUARDRAILS section 6. ('this is not a pentest' style scope-statements are OK; flag exists so human can verify framing.) |
| `templates/handoff/handoff.html.j2` | 373 | <p>For any of these, get a developer with that specific specialty. Before processing real payments at volume, get a real pentest.</p> | Security jargon. Reframe per SIMPLICITY-GUARDRAILS section 6. ('this is not a pentest' style scope-statements are OK; flag exists so human can verify framing.) |
| `templates/handoff/handoff.md.j2` | 121 | - Security posture against motivated attackers (this is not a pentest) | Security jargon. Reframe per SIMPLICITY-GUARDRAILS section 6. ('this is not a pentest' style scope-statements are OK; flag exists so human can verify framing.) |
| `templates/handoff/handoff.md.j2` | 124 | For any of these, get a developer with that specific specialty. Before processing real payments at volume, get a real pentest. | Security jargon. Reframe per SIMPLICITY-GUARDRAILS section 6. ('this is not a pentest' style scope-statements are OK; flag exists so human can verify framing.) |

### Em-dashes on customer-facing surfaces (19 instances)

| File | Line | Context | Suggested replacement |
|---|---|---|---|
| `landing/index.html` | 140 | <p class="text-sm text-muted mb-5">🟡 Needs a few fixes before sharing publicly · 5 findings (priority triage — Starter caps at 7)</p> | Customer-facing em-dash. Replace with a parenthetical, period, comma, or colon. Preserve voice and meaning. See SIMPLICITY-GUARDRAILS section 6. |
| `landing/index.html` | 378 | <td class="px-4 py-3 align-top text-muted">—</td> | Em-dash as a table / placeholder cell. Visible but structural. Consider replacing with '-' (hyphen) or 'none' if context allows. Lower priority than em-dashes inside prose. |
| `landing/index.html` | 384 | <td class="px-4 py-3 align-top text-muted">—</td> | Em-dash as a table / placeholder cell. Visible but structural. Consider replacing with '-' (hyphen) or 'none' if context allows. Lower priority than em-dashes inside prose. |
| `landing/index.html` | 390 | <td class="px-4 py-3 align-top text-muted">—</td> | Em-dash as a table / placeholder cell. Visible but structural. Consider replacing with '-' (hyphen) or 'none' if context allows. Lower priority than em-dashes inside prose. |
| `landing/index.html` | 391 | <td class="px-4 py-3 align-top text-muted">—</td> | Em-dash as a table / placeholder cell. Visible but structural. Consider replacing with '-' (hyphen) or 'none' if context allows. Lower priority than em-dashes inside prose. |
| `landing/index.html` | 396 | <td class="px-4 py-3 align-top text-muted">—</td> | Em-dash as a table / placeholder cell. Visible but structural. Consider replacing with '-' (hyphen) or 'none' if context allows. Lower priority than em-dashes inside prose. |
| `landing/index.html` | 397 | <td class="px-4 py-3 align-top text-muted">—</td> | Em-dash as a table / placeholder cell. Visible but structural. Consider replacing with '-' (hyphen) or 'none' if context allows. Lower priority than em-dashes inside prose. |
| `landing/index.html` | 417 | <li>Cross-user data check: —</li> | Em-dash as a table / placeholder cell. Visible but structural. Consider replacing with '-' (hyphen) or 'none' if context allows. Lower priority than em-dashes inside prose. |
| `landing/index.html` | 418 | <li>Quick Start Guide PDF: —</li> | Em-dash as a table / placeholder cell. Visible but structural. Consider replacing with '-' (hyphen) or 'none' if context allows. Lower priority than em-dashes inside prose. |
| `landing/index.html` | 419 | <li>Integrations review: —</li> | Em-dash as a table / placeholder cell. Visible but structural. Consider replacing with '-' (hyphen) or 'none' if context allows. Lower priority than em-dashes inside prose. |
| `landing/index.html` | 420 | <li>Loom walkthrough: —</li> | Em-dash as a table / placeholder cell. Visible but structural. Consider replacing with '-' (hyphen) or 'none' if context allows. Lower priority than em-dashes inside prose. |
| `landing/index.html` | 432 | <li>Integrations review: —</li> | Em-dash as a table / placeholder cell. Visible but structural. Consider replacing with '-' (hyphen) or 'none' if context allows. Lower priority than em-dashes inside prose. |
| `landing/index.html` | 433 | <li>Loom walkthrough: —</li> | Em-dash as a table / placeholder cell. Visible but structural. Consider replacing with '-' (hyphen) or 'none' if context allows. Lower priority than em-dashes inside prose. |
| `landing/index.html` | 516 | <p><strong class="text-ink">Starter ($19)</strong> is priority triage — we identify the top 7 issues a first-time visitor would notice and need fixed before lau... | Customer-facing em-dash. Replace with a parenthetical, period, comma, or colon. Preserve voice and meaning. See SIMPLICITY-GUARDRAILS section 6. |
| `landing/index.html` | 517 | <p><strong class="text-ink">Scale Up ($49)</strong> is a comprehensive audit — up to 25 findings across every category, plus a cross-user data check using 2 tes... | Customer-facing em-dash. Replace with a parenthetical, period, comma, or colon. Preserve voice and meaning. See SIMPLICITY-GUARDRAILS section 6. |
| `landing/r.html` | 104 | <h1 class="font-serif text-3xl sm:text-4xl mb-3" data-r-app-name>—</h1> | Em-dash as a table / placeholder cell. Visible but structural. Consider replacing with '-' (hyphen) or 'none' if context allows. Lower priority than em-dashes inside prose. |
| `landing/r.html` | 105 | <p class="text-sm text-muted" data-r-audit-line>—</p> | Em-dash as a table / placeholder cell. Visible but structural. Consider replacing with '-' (hyphen) or 'none' if context allows. Lower priority than em-dashes inside prose. |
| `landing/r.html` | 110 | <p class="mt-2 font-serif text-xl sm:text-2xl" data-r-verdict-label>—</p> | Em-dash as a table / placeholder cell. Visible but structural. Consider replacing with '-' (hyphen) or 'none' if context allows. Lower priority than em-dashes inside prose. |
| `templates/r/shareable.html.j2` | 109 | <p class="mt-2 font-serif text-xl sm:text-2xl" data-r-verdict-label>—</p> | Em-dash as a table / placeholder cell. Visible but structural. Consider replacing with '-' (hyphen) or 'none' if context allows. Lower priority than em-dashes inside prose. |

### Persona typos

None remaining.

### Stale internal category names (9 instances)

| File | Line | Context | Suggested replacement |
|---|---|---|---|
| `landing/index.html` | 124 | <span><strong class="text-ink font-medium">Trust gaps</strong>: missing privacy/terms, generic meta, anything that screams “not finished.”</span> | Internal taxonomy. Use buyer-facing 'trust signals & legal pages'. |
| `landing/index.html` | 312 | <li>Cross-user data check (2 test accounts)</li> | Internal taxonomy. Use buyer-facing 'user data isolation'. |
| `landing/index.html` | 377 | <td class="px-4 py-3 align-top text-muted">Cross-user data check</td> | Internal taxonomy. Use buyer-facing 'user data isolation'. |
| `landing/index.html` | 417 | <li>Cross-user data check: —</li> | Internal taxonomy. Use buyer-facing 'user data isolation'. |
| `landing/index.html` | 430 | <li>Cross-user data check: ✓ (2 test accounts)</li> | Internal taxonomy. Use buyer-facing 'user data isolation'. |
| `landing/index.html` | 443 | <li>Cross-user data check: ✓ (2 test accounts)</li> | Internal taxonomy. Use buyer-facing 'user data isolation'. |
| `landing/vs-pagelens.html` | 147 | <td class="px-4 py-3 align-top text-muted">Mobile audit</td> | Internal taxonomy. Use buyer-facing 'mobile layout issues'. |
| `landing/vs-pagelens.html` | 208 | <p class="text-xs uppercase tracking-widest text-accent font-semibold mb-1">Mobile audit</p> | Internal taxonomy. Use buyer-facing 'mobile layout issues'. |
| `landing/vs-pagelens.html` | 282 | ...EO scores.</strong> Broken CTAs. Dead links. Exposed keys on the live URL. Sketchy footer text that s... | Internal taxonomy. Use buyer-facing 'broken buttons & dead links'. |

### Stripe routing

None remaining.

## Critical issues (block ship -- must fix)

None.

## Notes for q-final-lint

- After this audit, run linters as planned.
- Em-dash replacements are stylistic: review the surrounding sentence and pick parenthetical / period / comma / colon. Do not bulk-replace globally; meaning gets lost.
- Stale finding caps (Starter cap=10, Scale Up cap=30) and Starter framing copy are surfaced for human review; pricing-page numbers that conflict with PRODUCT-DECISIONS section 1 need a copywriting pass, not a string-replace.
- Re-run this audit at any time with `python scripts/consistency_check.py --report-only` to verify a fix.
