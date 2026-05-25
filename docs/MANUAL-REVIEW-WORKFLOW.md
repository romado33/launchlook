# Manual review workflow

End-to-end runbook for delivering a LaunchLook review, from "customer
just paid" to "PDFs in their inbox." This is the workflow the audit UI
(`scripts/audit_ui.py`) is built around.

If you're new here, run through this once with a test customer
(`--slug test-rob`, your own email) before doing it on a real customer.

---

## 1. Customer purchases on Stripe

Stripe sends `checkout.session.completed` to `/api/stripe-webhook`. The
webhook creates a Notion row in **LaunchLook customers** with:

- `Status: Paid`
- `Tier:` Starter or Full
- `Customer email`, `Customer name`
- `Stripe session id`

You don't have to do anything. Open Notion when you're ready to start
the review.

## 2. Customer fills the Tally intake form

Tally sends `form_response` to `/api/tally-webhook`. The webhook updates
the Notion row with:

- `Status: Intake received`
- `App URL` (the live URL Rob will audit)
- `App name`, `Builder`, `Audience`, `Goals`, anything else the form
  collected

If the customer doesn't fill the intake within 48 hours, the followup
script (`scripts/followup_send.py`) chases them.

## 3. Start the audit

You'll need three things from the Notion row:

1. The **slug** (you decide; e.g. `jane-smith` or `lilo-test`)
2. The **app URL**
3. **Customer info** (name, email, app name, builder, tier)

### 3a. (Optional) Auto-capture screenshots

Snapshots the customer's app at desktop + mobile so you can review
without juggling browser windows:

```bash
python scripts/capture_screenshots.py --url https://jane.lovable.app --slug jane-smith
```

Output lands in `output/customers/jane-smith/screenshots/` plus a
single-page `index.html` you can scroll through.

### 3b. (Optional) Run the prescreen

Surface candidate findings from regex patterns in
`findings_library/findings.csv`:

```bash
python scripts/prescreen_findings.py --url https://jane.lovable.app --slug jane-smith
```

Output lands at `output/customers/jane-smith/prescreen-findings.md`.
**Pattern hits are not confirmed findings** — confirm each one with
your eyes before pasting into the audit UI.

## 4. Run the audit UI

```bash
python scripts/audit_ui.py \
    --slug jane-smith \
    --url https://jane.lovable.app \
    --tier "Full Package" \
    --name "Jane Smith" \
    --email jane@example.com \
    --app-name Sparkle \
    --builder Lovable
```

This:

1. Starts a local Flask server on `http://localhost:8000`
2. Auto-opens your default browser to that URL
3. Pre-populates the Customer section with the values you passed
4. Restores any unsaved draft (if you've been editing
   `customers/jane-smith.yaml` already)

[UI screenshot here — full form view]

### CLI argument reference

| Argument | Meaning | Example |
| --- | --- | --- |
| `--slug` | Filename for `customers/<slug>.yaml` | `jane-smith` |
| `--url` | Customer's live app URL | `https://jane.lovable.app` |
| `--tier` | `Starter Package` or `Full Package` | `"Full Package"` |
| `--name` | Full name (split into first/last by first space) | `"Jane Smith"` |
| `--first-name` | First name (overrides `--name`) | `Jane` |
| `--last-name` | Last name (overrides `--name`) | `Smith` |
| `--email` | Customer email | `jane@example.com` |
| `--app-name` | Customer app name | `Sparkle` |
| `--builder` | Lovable / Bolt / v0 / Base44 / Replit / Cursor / Other | `Lovable` |
| `--port` | Override port (default `8000`) | `8001` |
| `--host` | Override host (default `127.0.0.1`) | |
| `--no-browser` | Skip auto-opening the browser | |
| `--debug` | Run Flask in debug mode | |

All arguments are optional. If you launch with no flags, the form
opens with empty fields.

## 5. Fill in findings as you walk through the app

Workflow inside the form:

1. Start at the customer's URL in another tab
2. As you find issues, click **+ Add finding** and capture:
   - **Severity:** critical (must fix before launch), high (fix this
     week), medium (polish), low (nitpick)
   - **Title:** one-liner that names the issue
   - **What we saw:** concrete, on-page evidence (route, button label,
     copy)
   - **Why it matters:** one or two sentences on impact
   - **Screenshot (optional):** drag-and-drop a PNG. Saved to
     `screenshots/<slug>/finding-N.png`
   - **Fix prompt:** paste-ready instructions the customer can drop
     into Lovable / Bolt / v0 / etc.
3. The finding counter near "+ Add finding" shows
   `N / cap findings`. Cap is **5 for Starter Package**, **20 for Full
   Package** (read live from `scripts/deliver_report.py`, so any
   future cap change auto-propagates here)
4. Findings auto-sort by severity (critical → high → medium → low)
   when you generate YAML, but the live preview also shows current
   sort order
5. The form auto-saves to `drafts/<slug>.json` 1 second after every
   keystroke (and every 30 seconds as a heartbeat). Close the tab and
   come back; the form will offer to restore your draft.

[UI screenshot here — finding card expanded]

For **Full Package** customers, fill in the **Quick Start Guide**
section too: title + intro + at least one step + optional footer note.

## 6. Click "Save + send PDFs" when done

The action footer has three buttons:

| Button | What it does |
| --- | --- |
| **Save draft** | Saves `drafts/<slug>.json`. Useful before lunch. |
| **Generate YAML** | Validates + writes `customers/<slug>.yaml`, shows the rendered YAML in the right-hand preview pane. Does not send anything. |
| **Save + send PDFs** | Generate YAML, then immediately shells out to `python scripts/deliver_report.py --customer customers/<slug>.yaml --send`. Streams the deliver log into the right-hand pane. |

If validation fails, the failing fields turn red and inline errors
appear. The first error field auto-focuses.

[UI screenshot here — sticky footer with status]

The deliver pipeline:
1. Renders Main Report PDF (Playwright + Chromium, A4)
2. Renders Quick Start Guide PDF (Full Package only)
3. Bundles them as Resend email attachments
4. Sends the email from `hello@launchlook.app` to the customer
5. BCCs `ADMIN_EMAIL` if it's set in `.env`

Logs stream live into the "Deliver log" tab of the preview pane. Exit
code 0 means success.

## 7. Where files land

| Path | Contents |
| --- | --- |
| `customers/<slug>.yaml` | Generated input file. Gitignored except `customers/example-*.yaml`. |
| `drafts/<slug>.json` | Auto-saved form draft. Gitignored. |
| `screenshots/<slug>/finding-N.png` | Uploaded screenshots, named by finding index. Gitignored. |
| `output/reports/<slug>/main-report.pdf` | The delivered Main Report. |
| `output/reports/<slug>/quick-start-guide.pdf` | The delivered QSG (Full Package only). |

After delivery, mark the Notion row as `Delivered` (this is currently
manual — the followup script picks up from there).

## Troubleshooting

### Port 8000 is already in use

Another Flask app or local dev server is on 8000. Pass `--port 8001`
(or any free port). The browser-open hint will use the new port.

```bash
python scripts/audit_ui.py --slug jane-smith --port 8001
```

### Browser didn't auto-open

The script prints the URL on stdout. Visit `http://localhost:8000/`
manually. Pass `--no-browser` if you want to suppress the auto-open
attempt entirely.

### "ImportError: cannot import name 'create_app'"

You haven't installed `requirements-ui.txt` into the active Python:

```bash
pip install -r requirements-ui.txt
```

If you also want **Save + send PDFs** to work, install the main
requirements too:

```bash
pip install -r requirements.txt
playwright install chromium
```

### Validation errors won't go away

Open the right-hand "YAML preview" pane after clicking **Generate
YAML**. The inline red error messages list every field that needs a
value. Fields:

- Customer: first name, email, app name, app URL, tier, builder
- Verdict: summary, narrative
- Findings: at least 1, each with severity / title / what_we_saw /
  why_it_matters / fix_prompt
- Full Package only: QSG title, intro, at least 1 step

URL must start with `http://` or `https://`. Email must contain `@`.

### Screenshots aren't showing in the PDF

The audit UI stores screenshots at `screenshots/<slug>/finding-N.png`,
but `scripts/deliver_report.py` uses Playwright + Chromium to render
the PDF and only inlines images that the PDF templates explicitly
reference. If you need the screenshot to appear in the delivered PDF,
edit `templates/report/report.html.j2` to render
`{{ finding.screenshot_path }}` (this is a known follow-up — the
upload pipeline is wired but the PDF template wiring is a separate
piece of work).

The screenshot caption *does* appear in the PDF today, just without
the image. Use the caption to describe what the screenshot would have
shown.

### "Another deliver job is already running."

The deliver subprocess is single-flight per audit-UI session. Wait
for the previous run to finish (watch the deliver-log pane) before
hitting **Save + send PDFs** again.

### Draft restore offer keeps popping up

You hit **Dismiss** and the toast shouldn't reappear unless you
reload the page. If you really want to nuke the draft:

```bash
rm drafts/<slug>.json
```

…then reload.

---

## Source layout

```
scripts/
  audit_ui.py                        # CLI entry point (this is what you run)
  audit_ui/
    __init__.py
    app.py                            # Flask app factory + routes
    yaml_writer.py                    # Form payload → YAML serializer (+ reverse)
    draft_store.py                    # JSON draft persistence
    deliver_runner.py                 # Subprocess wrapper around deliver_report.py
    static/
      style.css                       # Dark mode styles, ~600 lines
      app.js                          # Form controller, no framework
    templates/
      index.html                      # Single-page form
      _finding_card.html              # Cloned by JS for each finding
      _step_card.html                 # Cloned by JS for each QSG step
```
