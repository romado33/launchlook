# Simplicity Guardrails

The discipline rules every worker must follow when touching customer-facing surfaces: landing pages, report PDFs, Quick Start Guide (QSG) PDFs, and email templates.

If you are about to edit anything under `landing/`, `templates/report/`, `templates/qsg/`, or `templates/email/`, read this file first. Then cite the rule numbers (e.g. §3.1, §6) in your commit message whenever you made a discipline judgment call.

---

## §1 Why this exists

LaunchLook is positioned as **a simple app for non-technical vibe coders.** Behind the scenes there is real complexity: multiple finding categories, an AI pipeline, several integrations, the Testers cast, tier-based deduplication logic, and a comprehensive checklist generator.

The buyer should never see that complexity.

Every customer-facing surface is a translation layer. Internal taxonomy, pipeline names, technical scoring, and engineering vocabulary stop at the boundary. What crosses the boundary is plain English, founder voice, and at most four things to look at.

When in doubt: cut, don't add.

---

## §2 Landing page rules

1. **Plain-English category names only.** Never expose internal taxonomy on the landing page. Banned on customer surfaces: "Core Web Vitals," "axe-core," "Scale-Ready audit," "Compliance-Lite," "RLS check," "regression detection," "AI pipeline," "finding fingerprints." Use buyer language: "performance and speed," "accessibility checks," "growth-readiness checks," "did anything break after AI changes."
2. **Maximum 4 sections above the fold:** hero, free hook CTA, pricing cards (4 tiers), demo video. Everything else (comparison table, FAQ, testimonials, founder bio) lives below the fold.
3. **Pricing cards: max 5 bullets each.** Bury the rest behind a "see full comparison →" expand.
4. **Tier ladder is fixed:** Free / Starter / Scale Up / Pro. No 5th tier. No tier-name jargon (no "Enterprise," "Premium," "Founder Roast," etc.). See `PRODUCT-DECISIONS.md` §1.
5. **Integrations stay invisible on the main landing.** GitHub integration, deep links, Notion delivery: never on the main landing page. They appear only as one-liners inside the Pro tier description, plus a post-purchase email after a Pro purchase.
6. **The Testers cast is a footer tooltip only.** Never a hero section. Personas appear inline on report findings, not as marketing copy. See `TESTERS-CAST.md`.
7. **vs-PageLens lives at `/vs-pagelens` only.** No nav link. Findable via SEO and FAQ.
8. **Demo video is the primary "what is this?" surface.** Use it to collapse explanatory text. If you are tempted to add another paragraph explaining the product, point at the video instead.
9. **Founder bio is 2 to 3 sentences with a photo.** Not a hero section. Not a "Meet the founder" page.
10. **Trust signals stay direct:** "7-day refund," "real founder review," "X paying customers" (when applicable). No badges of badges, no logo walls until logos are real.

---

## §3 PDF report rules (Main Report)

1. **Plain-English finding titles.** Never jargon in the headline or description. Technical wording is allowed only inside the paste-ready fix prompt block (where the buyer is going to copy it into an AI builder anyway).
   - Bad: "Largest Contentful Paint exceeds 4.0s target on /pricing"
   - Good: "Your /pricing page takes 4+ seconds to show its main image. First visitors usually leave before that finishes."
2. **Severity is simple:** High / Medium / Low. No numeric scores. No traffic-light colors. No "P0/P1/P2."
3. **Each finding has a fixed shape:**
   - Headline (8 to 12 words)
   - "What happened" paragraph (2 to 3 sentences)
   - "Why it matters" sentence (one)
   - Paste-ready fix prompt (verbatim copy-able block)
4. **Persona tags are subtle.** "Caught by The Snoop" appears in small text on the finding, not as a giant badge. See `TESTERS-CAST.md` for voice rules.
5. **Maximum 5 sections in the report:** verdict (1 paragraph), findings (sorted by severity), one-page "if you only fix three things" summary, comprehensive checklist (Scale Up and Pro only), Handoff Report (Pro only).
6. **No glossary, no appendix, no caveats wall.** If a buyer needs to learn what a term means in order to read the report, the term doesn't belong in the report.
7. **Maximum 1 page per finding.** If a finding wants more, split it or simplify it.
8. **Brand voice is founder, plainspoken, never corporate.** "I saw that..." over "Our analysis indicates..." First person. The buyer is hearing from Rob, not from a platform.

---

## §4 Quick Start Guide (QSG) PDF rules

1. **Same plain-English rules as the report.** Inherits §3.1 and §3.8.
2. **Fix prompts are SELF-CONTAINED.** A buyer who never read the main report can paste any QSG prompt into their AI builder and get something useful. Do not assume context from the report.
3. **Deep links beat prompts when available.** If a deep link to the buyer's AI builder is available, offer it as a button. Otherwise paste-ready prompt only.
4. **Order prompts by severity.** High-severity fixes go first. Same severity vocabulary as the report (High / Medium / Low).
5. **No "advanced configuration" section.** If a fix requires technical decisions, simplify the prompt or split the finding into two simpler findings.

---

## §5 Email template rules

1. **Plainspoken founder voice.** First-person ("I"). Same voice as §3.8.
2. **No corporate footer.** Just "— Rob" plus a 1-line p.s. if useful. (The "—" here is fine inside a signature line; everywhere else, see §6.)
3. **Maximum 150 words for delivery email body.** PDFs are attached. The email is the cover note, not the deliverable.
4. **No "powered by" line, no platform branding, no badge stack.** Quiet emails.

---

## §6 Brand voice (anti-patterns)

Never do these on any customer-facing surface:

- ❌ Surface internal taxonomy names on customer-facing copy ("Snoop," "Scale-Ready audit," "Compliance-Lite," "AI pipeline," "fingerprint dedup")
- ❌ Use "AI-powered scanner" as a value prop. That is how we deliver, not what the buyer gets.
- ❌ Use "automation," "intelligent analysis," "next-generation," or similar SaaS-speak
- ❌ Use industry jargon in finding titles (technical wording allowed only in paste-ready fix prompt blocks per §3.1)
- ❌ Add "advanced," "premium," or "professional" anything. We have a Pro tier; do not reuse the word.
- ❌ Add another tier. We are at 4 max: Free / Starter / Scale Up / Pro. See `PRODUCT-DECISIONS.md` §1 and §3.
- ❌ Em-dashes (associated with AI-generated content). Use parentheses, commas, or colons instead. The only exception is the "— Rob" sign-off in §5.2.
- ❌ The vocabulary list: "leverage," "utilize," "robust," "comprehensive," "seamless," "intuitive," "elevate," "empower," "unlock." The single allowed use of "comprehensive" is the literal product name "comprehensive checklist" inside the Scale Up and Pro deliverables (see `PRODUCT-DECISIONS.md` §1); even there, prefer "full checklist" in customer-facing copy when possible.

If you find yourself reaching for one of these, the sentence wants to be cut, not rewritten.

---

## §7 How workers must reference this

Every worker that touches `landing/`, `templates/report/`, `templates/qsg/`, or `templates/email/` must:

1. Read `docs/SIMPLICITY-GUARDRAILS.md` first (this file).
2. Apply rules from §2 (landing), §3 (report), §4 (QSG), §5 (email) as relevant to the surface they are editing.
3. Cite the rule numbers in their commit message whenever they made a discipline judgment call. Example commit message line: `Drop "AI-powered" from hero per §2.1 + §6.`

If a rule conflicts with a feature request, the rule wins. Escalate to the user before adding a 5th tier, a hero-level Testers section, an "advanced" anything, or a new banned word. The whole point of these guardrails is that they survive across agent sessions and stop slow drift toward platform-feeling copy.

When the rules are silent on something, default to: cut, plain English, founder voice, fewer sections.
