# LaunchLook Internal Consistency Audit

Generated: 2026-05-27 03:01 UTC by `scripts/consistency_check.py` (q-final-audit worker)


Canonical truth sources audited against:
- `docs/SIMPLICITY-GUARDRAILS.md` section 6 (forbidden vocab, em-dash rule)
- `docs/PRODUCT-DECISIONS.md` section 1 (tier ladder, finding caps), section 7 (pricing)
- `docs/TESTERS-CAST.md` (canonical 7-persona spelling)
- `scripts/ai_audit/finding_categories.yaml` (buyer-facing finding category names)
- `api/stripe-webhook.py` (Stripe cents-to-tier mapping)

## Summary

| Check | Total found | Auto-fixed | Needs review |
|---|---|---|---|
| Stale tier names + finding caps | 0 | 0 | 0 |
| Stale prices | 0 | 0 | 0 |
| Forbidden vocabulary | 8 | 0 | 8 |
| Customer-facing em-dashes | 0 | 0 | 0 |
| Persona typos | 0 | 0 | 0 |
| Stale internal category names | 0 | 0 | 0 |
| Stripe routing | 0 | 0 | 0 |

Auto-fix mode: **not applied** (use `--auto-fix-safe` to write changes). Files modified by auto-fix: **0**.

## Auto-fixed (already applied)

_No auto-safe fixes were applied (none qualified, or run was --report-only)._

## Needs human review

### Stale tier names + finding caps

None remaining.

### Stale prices

None remaining.

### Forbidden vocab still on customer surfaces (8 instances)

| File | Line | Context | Suggested replacement |
|---|---|---|---|
| `landing/index.html` | 155 | ...ess checkup, not a full security audit.</p> | Security jargon. Reframe per SIMPLICITY-GUARDRAILS section 6. ('not a security audit' style scope-statement is OK.) |
| `landing/terms.html` | 34 | <h2 class="font-serif text-xl mt-10 mb-3">Not a security audit</h2> | Security jargon. Reframe per SIMPLICITY-GUARDRAILS section 6. ('not a security audit' style scope-statement is OK.) |
| `landing/terms.html` | 35 | ...ibility check, not a full security audit. The Pro Package integrations review covers configuration of St... | Security jargon. Reframe per SIMPLICITY-GUARDRAILS section 6. ('not a security audit' style scope-statement is OK.) |
| `landing/webflow.html` | 337 | <summary class="flex justify-between items-center font-medium text-sm">Is this a security audit?<span class="text-muted text-lg">+</span></summary> | Security jargon. Reframe per SIMPLICITY-GUARDRAILS section 6. ('not a security audit' style scope-statement is OK.) |
| `templates/handoff/handoff.html.j2` | 355 | <li>Security posture against motivated attackers (this is not a pentest)</li> | Security jargon. Reframe per SIMPLICITY-GUARDRAILS section 6. ('this is not a pentest' style scope-statements are OK; flag exists so human can verify framing.) |
| `templates/handoff/handoff.html.j2` | 358 | <p>For any of these, get a developer with that specific specialty. Before processing real payments at volume, get a real pentest.</p> | Security jargon. Reframe per SIMPLICITY-GUARDRAILS section 6. ('this is not a pentest' style scope-statements are OK; flag exists so human can verify framing.) |
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
