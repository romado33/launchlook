# Delivery pipeline: Main Report + Quick Start Guide PDFs by email

This is how a paid LaunchLook checkup gets to the customer.

There is no Notion link, no shareable URL, no login. Two PDFs land in the
customer's inbox: the Main Report and the Quick Start Guide.

```
customers/{slug}.yaml  ──► scripts/deliver_report.py ──► two PDFs ──► Resend ──► customer inbox
                              (Jinja2 + Playwright)         (attachments)
```

## One-time setup

```powershell
pip install -r requirements.txt
playwright install chromium
```

Add a Resend API key to `.env` (only required for `--send`). Get a key at
[resend.com/api-keys](https://resend.com/api-keys), then paste it as the
value of `RESEND_API_KEY` in `.env` (the variable is already documented in
`.env.example`).

`FROM_EMAIL` and `ADMIN_EMAIL` come from the existing `.env` setup.

## 1. Fill out a customer YAML

Copy the example and edit:

```powershell
cp customers/example-jane-sparkle.yaml customers/jane-sparkle.yaml
```

`customers/*.yaml` is gitignored (with `example-*.yaml` allowed). Real
customer data never enters git.

The YAML has four top-level sections:

- `customer` – first name, email, app name, app URL, tier (`Starter Package`
  or `Full Package`), and `builder` (Lovable, Bolt, etc.). Set
  `url_redacted: true` to print "URL redacted" instead of the live URL in
  the PDF.
- `verdict` – emoji, one-line summary, and a multi-line narrative paragraph.
- `findings` – a list. Each item needs a `severity` (`critical`, `high`,
  `medium`, `low`), `title`, `what_we_saw`, `why_it_matters`, optional
  `screenshot_caption`, and a `fix_prompt` (paste-ready prompt for the
  builder).
- `quick_start_guide` – `title`, `intro`, an ordered list of `steps`
  (`title` + `body`), and an optional `footer_note`.

Findings cap: 5 for Starter Package (priority triage — the 5 most important
findings), 20 for Full Package (comprehensive audit). The script warns if
you exceed the cap but still renders.

## 2. Render and preview (dry-run)

```powershell
python scripts/deliver_report.py --customer customers/jane-sparkle.yaml
```

This:

1. Validates the YAML.
2. Renders `output/reports/{slug}/main-report.pdf` and
   `output/reports/{slug}/quick-start-guide.pdf` via Jinja2 + Playwright.
3. Opens both PDFs in the system default viewer for visual review.
4. Prints next-step hints. No email is sent.

The slug is `{first-name}-{app-name}` lowercased (Jane Smith + Sparkle
Marketplace becomes `jane-sparkle-marketplace`).

Useful flags:

- `--no-open` skips auto-opening (useful in CI or remote shells).
- `--qsg-link https://...` prints a public URL on the Main Report's closing
  page (only used if you also host the QSG PDF somewhere).

## 3. Send via Resend

Once the dry-run looks right:

```powershell
python scripts/deliver_report.py --customer customers/jane-sparkle.yaml --send
```

The script re-renders the PDFs (fresh date in the footer), shows a confirm
preview (To, Subject, attachments), and waits for you to type `send` before
calling Resend. Pass `--yes` to skip that prompt for unattended use.

Mail is sent from `FROM_EMAIL` (default `hello@launchlook.app`) and BCC'd
to `ADMIN_EMAIL` for visibility. The email has both an HTML body
(`templates/email/delivery_pdf.html.j2`) and a plain-text fallback
(`templates/email/delivery_pdf.txt.j2`), with both PDFs attached.

If `RESEND_API_KEY` is missing, `--send` exits with a clear error and
points back to https://resend.com/api-keys.

## 4. Verify the email landed

1. Check the Resend dashboard at https://resend.com/emails for status
   (delivered, bounced, etc.). The script prints the Resend message id on
   success.
2. Confirm in your own inbox via the BCC.
3. Mark the Notion customer row as `Delivered` and set `Delivered At` to
   today (this is still done manually for now, the same as before).

## File map

| File | Purpose |
| --- | --- |
| `scripts/deliver_report.py` | CLI entry point. Validates, renders, optionally sends. |
| `templates/report/report.html.j2` | Main Report HTML (A4 print). |
| `templates/qsg/qsg.html.j2` | Quick Start Guide HTML (A4 print). |
| `templates/email/delivery_pdf.html.j2` | HTML email body. |
| `templates/email/delivery_pdf.txt.j2` | Plain-text email body. |
| `customers/example-jane-sparkle.yaml` | Reference YAML. Copy and edit. |
| `output/reports/{slug}/` | Generated PDFs (gitignored). |

## Trade-off notes

- **Why Playwright over WeasyPrint?** WeasyPrint needs GTK on Windows,
  which is fragile to install. Playwright bundles its own Chromium and
  renders the same CSS the landing site uses, so the report's typography
  stays in sync with the brand.
- **Why two attachments instead of one combined PDF?** The Quick Start
  Guide is meant to be forwarded to the founder's first users; the Main
  Report is for the founder only. Keeping them separate makes that obvious.
- **Why YAML, not Notion?** Rob writes findings while reading the live app.
  YAML is faster to author and less fragile than Notion's API. Notion stays
  in the loop for customer status tracking.

## Troubleshooting

- `ERROR: playwright not installed` after `pip install -r requirements.txt`:
  also run `playwright install chromium` once, which downloads the bundled
  browser (~150 MB).
- `ERROR: customer.tier must be one of...`: only `Starter Package` and
  `Full Package` are accepted, matching the Stripe / Notion tier names.
- PDFs render but fonts look generic: the templates load Fraunces and Inter
  from Google Fonts at render time. If the network is offline, fall back
  fonts (Georgia, system sans) take over. That's fine for previews.
