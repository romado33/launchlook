# GitHub integration (Pro tier opt-in)

**Last updated:** May 26, 2026
**Owner:** Rob
**Status:** Live as of q19. Opt-in. Manually triggered by Rob via CLI.
Never auto-runs from the delivery pipeline.

Pro Package customers ($99 tier) can opt into having their audit
findings auto-created as GitHub issues on their repo. One issue per
finding, with the full PDF context (severity, what we saw, why it
matters, paste-ready fix prompt) and the persona tag from the Testers
cast. If the audit was triggered against a specific PR, a single
summary comment also gets posted on that PR.

This doc covers what it is, how to set it up for a customer, how to
invoke the CLI, and how to recover from the failure modes.

---

## What it is

* Pro tier only. The landing page (`landing/index.html`,
  `landing/webflow.html`) carries a one-line mention inside the Pro
  card. The post-purchase delivery email carries a single optional
  paragraph asking the customer if they'd like findings as GitHub
  issues. Nothing else on customer surfaces references the integration
  (per `SIMPLICITY-GUARDRAILS.md` §2: integrations stay invisible on
  the main landing).
* Opt-in. Customers reply to the delivery email with their repo URL
  (and optionally a commit SHA / PR number). Rob adds those fields to
  `customers/<slug>.yaml` and exports the customer's fine-grained PAT
  as an environment variable.
* Manually triggered. Rob runs `python scripts/github_push.py` after
  spot-checking the YAML. The delivery pipeline never auto-runs the
  CLI — it only logs a one-line reminder. This is deliberate: a
  miswired customer slug auto-creating issues on the wrong repo would
  be very hard to explain.

---

## Customer setup (one customer at a time)

1. **Customer replies** to the delivery email with their GitHub repo
   URL (and optional commit SHA / PR number). Per `TALLY-INTAKE-SETUP.md`
   the intake form may also collect this up front in the future; for
   now the reply path is the canonical way in.
2. **Customer creates a fine-grained PAT** scoped to that single repo
   with **Issues: read+write**. Walk them through it if needed:
   GitHub → Settings → Developer settings → Personal access tokens →
   Fine-grained tokens → Generate new token → pick the single repo →
   Repository permissions → Issues: Read and write → 30-day expiry.
3. **Customer sends the PAT** to Rob over a secure channel (1Password,
   ProtonMail, anything but plain Slack / SMS).
4. **Rob exports the PAT** as an environment variable using the
   `<CUSTOMER_SLUG>_GITHUB_PAT` convention. PowerShell:
   ```powershell
   $env:JANE_SPARKLE_GITHUB_PAT = "github_pat_..."
   ```
   bash / zsh:
   ```bash
   export JANE_SPARKLE_GITHUB_PAT="github_pat_..."
   ```
5. **Rob adds the `github:` block** to the customer YAML:
   ```yaml
   github:
     repo: "https://github.com/jane-sparkle/main-site"
     commit_sha: "abc123def"                       # optional
     pr_number: 42                                 # optional
     token_env: "JANE_SPARKLE_GITHUB_PAT"          # name of env var only
   ```
   The PAT itself never appears in the YAML. The YAML lives in git;
   the PAT does not.

See `customers/example-pro-package.yaml` for the canonical block.

---

## Invoking the CLI

### Dry-run preview (always start here)

Print every issue title + a 12-line body preview without making any
API calls. No PAT required for this path.

```powershell
python scripts/github_push.py --customer customers/example-pro-package.yaml --dry-run
```

Use this to double-check that:

* Persona tags look right per finding.
* Severity badges match the PDF report.
* Footer carries the correct audit id + timestamp.

### Live create issues

```powershell
python scripts/github_push.py --customer customers/example-pro-package.yaml
```

You'll get a confirmation prompt before any issues are POSTed
(`type 'push' to confirm`). On success, the CLI prints a summary table
mapping each finding title to the created GitHub issue URL.

Defaults you can override:

* `--labels launchlook,audit-finding` — applied to every issue. Pass
  `--labels ""` to skip.
* `--yes` — skip the confirmation prompt (for scripted re-runs; use
  with care, see "Re-running" below).

### PR comment mode

If the YAML includes `pr_number` (or you pass `--pr 42` on the CLI),
after the issues are created the CLI posts one summary comment on the
PR with a checkbox list linking each finding line to the issue we just
created.

```powershell
python scripts/github_push.py --customer customers/example-pro-package.yaml --pr 42
```

---

## Failure modes + recovery

| Symptom | Likely cause | Fix |
|---|---|---|
| `404 Not Found` from `create_issue` | Repo URL wrong, or repo private and PAT can't see it, or PAT belongs to a non-collaborator | Verify repo URL is correct and HTTPS GitHub.com. Verify the PAT was created on the customer's GitHub account, not Rob's. Verify the PAT is scoped to the right repo. |
| `403 Forbidden` | PAT lacks Issues:write scope, or hit a secondary rate limit | Re-issue a fine-grained PAT with Issues: read+write on this single repo. If it's a secondary rate limit, wait 60s and re-run; the 1-second floor between issue POSTs should keep us well clear in normal use. |
| `401 Unauthorized` | PAT expired, revoked, or copy-pasted with whitespace | Generate a fresh fine-grained PAT, re-export the env var, re-run. |
| Issues created on the wrong repo | YAML had the wrong repo URL | Delete the created issues by hand on GitHub. Fix the YAML. Re-run. |
| Re-ran and got duplicate issues | The CLI is NOT idempotent (see below) | Delete the duplicates by hand. The CLI does not look up existing issues; every run POSTs fresh ones. |

### Re-running creates duplicates

The integration is intentionally **not idempotent**. Running the CLI
twice on the same YAML creates 2× the issues. If you need to re-push
(e.g. because the YAML changed after a re-scan), delete the previously-
created issues on GitHub first.

Why not idempotent? GitHub doesn't expose a stable "audit finding id"
we can look up. We could fingerprint by title, but title-based lookups
break the moment Rob edits a title during review (which happens often).
Manual delete-then-re-push is the simplest correct behavior; if a
customer requests re-push as a routine flow, we'll add a `--replace`
mode that deletes-by-label first.

---

## Safety & limits

* **No PAT in the YAML.** Only the *name* of the env var that holds
  the PAT. The PAT itself is read at runtime from `os.environ`.
* **No PAT in logs.** Error formatters explicitly redact the token if
  it ever appears in a GitHub error body (`_redact_token_in_text`).
  `landing/`, `templates/email/`, and every customer-facing surface
  are kept clean — grep for `GITHUB_PAT|github_token` in those
  directories at any time and expect zero matches.
* **HTTPS GitHub.com only.** SSH (`git@github.com:...`), GitLab,
  Gitea, and self-hosted GitHub Enterprise are rejected at
  `parse_repo_url` time. They can be added when a customer asks.
* **1-second polite delay** between issue POSTs. For a 40-finding Pro
  audit that's a 40-second floor — comfortably inside GitHub's
  5000 req/hour authenticated quota.
* **Never auto-runs from delivery pipeline.** `scripts/deliver_report.py`
  only logs a one-line reminder for Pro customers with a `github:`
  block. Rob runs the CLI by hand. This is the most important safety
  rule in this doc.

---

## Related docs

* `docs/AI-AUDIT-PIPELINE.md` — how the YAML gets generated in the
  first place; this integration consumes it downstream.
* `docs/PRODUCT-DECISIONS.md` §8 — canonical Pro tier deliverable
  list. The change-log entry for this work lives at the bottom.
* `docs/SIMPLICITY-GUARDRAILS.md` §2.5 — why this integration stays
  invisible on the main landing.
* `docs/TESTERS-CAST.md` — how persona tags are written and which
  Tester is the fallback when a finding's YAML row is missing the
  `tester` field.
