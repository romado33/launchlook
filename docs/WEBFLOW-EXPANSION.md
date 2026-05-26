# LaunchLook for Webflow — Expansion Doc

**Last updated:** May 25, 2026
**Owner:** Rob
**Status:** Shipped (landing page, AI pipeline, audit UI, report template, outreach playbook). Three manual tasks remain — see [`ROB-REMAINING-TODO.md`](ROB-REMAINING-TODO.md) §"LaunchLook for Webflow SKU".

This is the single source of truth for the Webflow SKU. Use it to spot-check a Webflow audit, write Webflow-flavored marketing copy, and onboard the next worker who needs to extend the platform-aware pipeline.

---

## 1. What shipped

LaunchLook now sells two parallel SKUs at the same $19 / $49 / $99 pricing:

| | Vibe-coder SKU (existing) | Webflow SKU (new) |
|---|---|---|
| Landing page | `landing/index.html` | `landing/webflow.html` |
| Public URL | `launchlook.app/` | `launchlook.app/webflow` |
| Audience | Lovable / Bolt / v0 / Cursor / Replit / Base44 founders | Webflow freelancers, agencies, in-house teams |
| Stripe Payment Links | `stripe.starter` / `stripe.launch` (existing) | Same — reused, no new products |
| Tally intake | `tally.so/r/QKOX1A` (existing) | Same form, Webflow customer picks `Webflow` in Q7 |
| AI pipeline | `scripts/ai_audit.py` (default `--platform vibe-coder`) | `scripts/ai_audit.py --platform webflow` |
| Fix-prompt voice | "Tell Lovable to..." / "In v0, update..." | "In Webflow Designer, open Pages → ... → Publish" |
| Report header | "LaunchLook · Starter Package report" | "LaunchLook for Webflow · Starter Package report" |
| Email delivery | Resend, `hello@launchlook.app` | Same infra |

**No fork.** The Webflow SKU shares ~95% of the existing pipeline. The platform-specific surface is intentionally small:

- one platform appendix prompt (`scripts/ai_audit/prompts/fix_prompt_webflow.txt`)
- one dropdown (Platform field in `scripts/audit_ui/`)
- conditional report header / fix-prompt label in `templates/report/report.html.j2`
- one landing page (`landing/webflow.html`)
- one outreach section (`docs/OUTREACH-PLAYBOOK.md` §7b)

---

## 2. How to run a Webflow audit (`--platform webflow`)

### Via CLI

```
python scripts/ai_audit.py \
    --slug alex-bauer \
    --url https://bauer-studio.webflow.io \
    --tier "Starter Package" \
    --builder Webflow \
    --platform webflow \
    --name "Alex Bauer" \
    --email alex@example.com \
    --app-name "Bauer Studio"
```

The pipeline then:

1. Loads the base `system.txt` prompt.
2. Appends the Webflow appendix (`fix_prompt_webflow.txt`) below a clear divider. The appendix replaces the FIX PROMPT TONE BY BUILDER section for Webflow customers and adds Webflow-only voice rules (Designer panel names, breakpoint pixel values, "Publish" as the verb).
3. Appends the Webflow-specific finding-category checklist (form-submission test, noindex / robots.txt, JSON-LD schema, Designer-to-live mismatches, mobile breakpoint breakage at 991 / 767 / 478) to the user prompt for this customer only.
4. Writes `customers/alex-bauer.yaml` with `customer.platform: webflow` set.
5. Hands off to `scripts/audit_ui.py --review-ai --slug alex-bauer` for the founder spot-check.
6. After approval, `scripts/deliver_report.py` renders the PDF with the Webflow header ("LaunchLook for Webflow · Starter Package report") and the Webflow fix-prompt label ("Step-by-step fix in Webflow Designer").

### Auto-inference shortcut

If you pass `--builder Webflow` but forget `--platform`, the pipeline infers `platform=webflow` automatically. The reverse (passing `--platform webflow` but `--builder Lovable`) trusts your explicit builder and keeps the Webflow voice — useful for testing.

### Via the audit UI

`scripts/audit_ui.py` now has a Platform dropdown in the Customer card (between Builder and the Verdict section). Default is `vibe-coder`; pick `webflow` to flip the report into Webflow mode. The dropdown value is persisted to `customer.platform` in the generated YAML.

---

## 3. How to spot-check a Webflow audit

The 5-minute spot-check Rob does before shipping any Webflow report:

1. **Did the AI write in Designer language?** Every `fix_prompt` should reference Webflow Designer panels by name (Pages, Style Manager, Symbols, CMS Collections, Project Settings → Forms, SEO tab, Custom Code) and use the verb **Publish** (not "deploy" / "ship"). Reject any fix prompt that mentions `npm`, `import.meta.env`, `src/`, Vercel, or GitHub.
2. **Did the AI use Webflow breakpoint pixel values?** Mobile findings should call out 991px / 767px / 478px explicitly, not "tablet" / "phone."
3. **Did the AI catch at least one Webflow-specific finding category?** A clean Webflow audit will surface at least one of: form-submission failure, noindex / robots block, missing JSON-LD, Designer-to-live mismatch, breakpoint breakage. If none appear and the site is non-trivial, the AI is probably running the vibe-coder checks by accident — verify the YAML has `customer.platform: webflow`.
4. **Is the report header right?** PDF eyebrow should read "LaunchLook for Webflow · {tier} report" and the fix-prompt block label should read "Step-by-step fix in Webflow Designer."
5. **Sanity-check one prompt against Webflow Designer.** Open Webflow Designer on a real project, follow the steps in one of the fix prompts, confirm the navigation path exists. AI sometimes invents panel names.

Reference YAML: `customers/example-webflow.yaml`. Render it locally:

```
python scripts/deliver_report.py --customer customers/example-webflow.yaml --no-open
```

That writes `output/reports/alex-bauer-studio/main-report.pdf`. Open it and confirm the header, severity grouping, and fix-prompt label all render with Webflow phrasing.

---

## 4. Marketing positioning (one-paragraph summary)

> LaunchLook for Webflow is the pre-launch checkup for Webflow sites that catches what Webflow Designer doesn't warn you about: form submissions silently failing since the November 2024 update, accidental noindex blocking Google, missing JSON-LD schema, Designer-to-live mismatches, and mobile breakpoint breakage at the three native Webflow breakpoints (991 / 767 / 478). URL-only — no Workspace or Editor access. AI scans every page; a founder personally curates every finding before delivery. $19 / $49 / $99, sits below the $899 floor of Codeable and Webflow Experts on purpose. Built for freelancers, agencies, and in-house teams who want the second pair of eyes before client handoff.

Use that paragraph (or pieces of it) as the canonical answer to "what does the Webflow SKU do?" Don't reinvent it per channel.

### Why this wedge

From the site-builder market research (`docs/SITE-BUILDER-MARKET-RESEARCH.md`):

- **Real pain.** Post-Nov-2024 form-failure mode hit hundreds of agencies. Months of leads lost. No incumbent fix.
- **Real price gap.** Codeable / Webflow Experts audits start at $899 and go to $4,800. Below that, the only option is Webflow University's free manual checklist (2 hours, requires expertise). LaunchLook fills the $19–$99 gap.
- **No defensible incumbent under $899.** Only Framer plugins catch schema; nothing catches the silent form failure; nothing automates the breakpoint check.

### What we explicitly don't claim

- "Webflow security audit" — not what we do
- "Webflow performance audit" — not what we do (Webflow performance is mostly platform-controlled)
- "Webflow accessibility audit" — partial only (we catch the obvious; not a WCAG-conformance product)
- "Replaces Webflow Experts" — no, we're the layer below

---

## 5. Data model & file map

### Customer YAML

The `customer` block now supports a `platform` key:

```yaml
customer:
  first_name: Alex
  last_name: Bauer
  email: alex@example.com
  app_name: Bauer Studio
  app_url: https://bauer-studio.webflow.io
  url_redacted: false
  tier: Starter Package
  builder: Webflow
  platform: webflow      # NEW. Optional. Defaults to "vibe-coder" when absent.
```

When `platform` is absent or `vibe-coder`, the YAML stays byte-identical to legacy customers (the YAML writer drops the default value rather than emitting it). Legacy YAMLs without the key keep rendering with the vibe-coder report header and fix-prompt label.

### File map

| File | Change | Purpose |
|---|---|---|
| `landing/webflow.html` | NEW | Webflow landing page, $19 / $49 / $99 pricing, Webflow FAQ |
| `landing/index.html` | additive nav + footer link | Small `/webflow` nav link in header + "For Webflow" in footer |
| `landing/README.md` | updated | Documents `/webflow` route |
| `vercel.json` + `landing/vercel.json` | additive | `/webflow → /webflow.html` rewrite |
| `scripts/ai_audit.py` | additive arg | `--platform vibe-coder` (default) or `webflow` |
| `scripts/ai_audit/pipeline.py` | additive | `VALID_PLATFORMS`, `build_system_prompt(platform)`, `_maybe_append_webflow_checks(...)`, `CustomerContext.platform` |
| `scripts/ai_audit/prompts/system.txt` | additive footer | "PLATFORM-CONDITIONAL APPENDICES" section explaining how appendices layer on top |
| `scripts/ai_audit/prompts/fix_prompt_webflow.txt` | NEW | The Webflow appendix prompt |
| `scripts/audit_ui/` | additive | Platform dropdown in form, `VALID_PLATFORMS` in YAML writer, platform key in payload |
| `scripts/audit_ui.py` | additive arg | `--platform` CLI prefill |
| `scripts/deliver_report.py` | additive validation | Accepts and normalizes `customer.platform` |
| `templates/report/report.html.j2` | conditional | Webflow header label + Designer fix-prompt label when `platform: webflow` |
| `docs/OUTREACH-PLAYBOOK.md` | new section §7b | Webflow community targets + 3 ready-to-paste pitches |
| `docs/TALLY-INTAKE-SETUP.md` | additive section | "Webflow option for Q7" — manual 5-min Tally edit |
| `docs/TALLY-PASTE-ONLY.txt` | additive | `Webflow` option added to Q7's list |
| `docs/ROB-REMAINING-TODO.md` | new section | Three manual tasks (Tally edit, outreach, optional thanks URL) |
| `templates/notion/customers-db.csv` | additive example row | EXAMPLE Webflow customer row to show Notion users the Platform value |
| `templates/notion/README.md` | additive | Documents Platform column accepting Webflow |
| `customers/example-webflow.yaml` | NEW | Canonical Webflow audit reference (5 findings, Starter, Designer-flavored fixes) |

---

## 6. Coordination with queued workers

This SKU was shipped with three sibling workers queued behind it. The platform-conditional architecture was designed to play nicely with all three:

| Worker | What it touches | How this SKU stays compatible |
|---|---|---|
| **Security-lite worker** | `scripts/ai_audit/prompts/system.txt` | The Webflow change to `system.txt` is purely additive — a new "PLATFORM-CONDITIONAL APPENDICES" section at the end. Security-lite can register a new appendix (e.g. `fix_prompt_security_lite.txt`) by adding a slug to `PLATFORM_PROMPT_FILES` in `pipeline.py`. No need to touch the base prompt. |
| **Free-audit-pivot worker** | `landing/index.html` hero | We only added a small `/webflow` link to the nav and footer. The hero was not touched. Free-audit-pivot can rewrite the hero freely. |
| **Testers integration worker** | persona tagging on findings | Webflow finding categories were deliberately not labeled with persona names (Saboteur / Snoop / etc.). The Testers worker can map form-fail → The Saboteur, noindex → The Snoop, schema → a new persona at integration time without rewriting Webflow findings. |

### Adding a new platform appendix (template for the next worker)

1. Create `scripts/ai_audit/prompts/fix_prompt_<slug>.txt` with voice rules and a skeleton.
2. Add the slug to `VALID_PLATFORMS` in both `scripts/ai_audit/pipeline.py` and `scripts/audit_ui/yaml_writer.py`.
3. Add a line to `PLATFORM_PROMPT_FILES` in `pipeline.py` pointing at the new file.
4. (Optional) Add a finding-category checklist by following the `_WEBFLOW_FINDING_CHECKS` pattern and calling `_maybe_append_<slug>_checks` from `run()`.
5. (Optional) Add conditional branches in `templates/report/report.html.j2` for the report header / fix-prompt label.

That's it. No base-prompt rewrite needed.

---

## 7. What was punted (and why)

| Punt | Why |
|---|---|
| Separate Stripe products for Webflow | Spec said no. Reuse the existing $19 / $49 / $99 payment links. |
| Separate Tally intake form | Spec said no. Same form, customer picks "Webflow" in Q7. |
| Persona tagging on Webflow findings (Saboteur / Snoop) | Queued for the Testers integration worker. Leaving the hook clean for them. |
| Security-lite checks for Webflow | Queued for the security-lite worker. The platform appendix architecture means they can layer in without touching this SKU. |
| Webflow-specific thanks page (`/webflow/thanks`) | Optional per spec. Existing `/thanks` copy is platform-agnostic and works fine. Skip until ≥3 paying Webflow customers. |
| Auto-publishing the landing page change to production | Out of scope for the worker. Vercel deploys on push to main. |
| Test runs with real LLM providers (Claude / GPT) | Out of scope for the worker — would burn API tokens. Used the existing `--provider stub` paths and the example YAML to confirm the rendering pipeline. |
